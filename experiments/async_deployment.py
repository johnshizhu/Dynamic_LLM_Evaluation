import litellm
from litellm import acompletion
import time
import sys
import os
import aiohttp
import asyncio
import re
current_dir = os.path.dirname(os.path.abspath(__file__))
a_dir = os.path.join(current_dir, '../conversational_agents')
sys.path.insert(0, a_dir)
from utils import async_gpt_query
from base_agent import *

async def conversation(iterations, regen_lim, trait, trait_definition, domain, proposer, verifier, target):
    prompt_list = []
    prompt_list_r = [] # with rational
    verify_list = []
    bad_prompt_list = []
    bad_verification_list = []
    response_list = []
    regen_counter = 0

    for i in range(iterations): # Repeat conversation for defined iterations
        is_first = True if i == 0 else False

        # Prompt Generation Sequence
        prompt = await proposer.async_generate_prompt(str(prompt_list), str(response_list), domain, trait, trait_definition, is_first)
        
        print("prompt")
        return
        
        verify = await verifier.async_verify_prompt(str(prompt_list), str(response_list), prompt, domain, trait, trait_definition, is_first)        
        verify_score = int(re.findall(r'\d+', verify)[-1])
        is_first = False
        if verify_score < 8:
            for i in range(regen_lim):
                regen_counter += 1
                prompt = await proposer.async_regenerate_prompt(str(prompt_list), str(response_list), prompt, verify, domain, trait, trait_definition)
                verify = await verifier.async_verify_prompt(str(prompt_list), str(response_list), prompt, domain, trait, trait_definition, is_first)
                verify_score = int(re.findall(r'\d+', verify)[-1])
                if verify_score > 6:
                    break
                bad_prompt_list.append(prompt)
                bad_verification_list.append(verify)
        prompt_list_r.append(prompt)
        verify_list.append(verify)

        # Target Model Response
        start_index = prompt.find("New Prompt:")
        if start_index != -1:  
            extr_prompt = prompt[start_index+len("New Prompt:"):].strip() # Prompt extraction
            prompt_list.append(extr_prompt)
            target_response = await target.async_respond(extr_prompt) # Target Response
            response_list.append(target_response)  # Remove any leading whitespace
        else:
            print(prompt)
            raise Exception("Error in output format, 'New Prompt' not found")
    return prompt_list, prompt_list_r, verify_list, bad_prompt_list, bad_verification_list, response_list, regen_counter


def multi_instance_evaluation(
        num_instances,
        iterations,
        regen_lim,
        generator,
        validator,
        target,
        trait,
        trait_definition,
        domain
    ):
    '''
        This function concurrently runs multiple conversations between defined agents and target  
        
        num_instances (int) - number of concurrent conversations
        iterations (int)    - conversational depth
        regen_lim  (int)    - limit of times of regeneration in case of bad prompt
        generator (string)  - model type of generator
        validator (string)  - model type of validator
        target    (string)  - model type of target model
        trait     (string)  - name of trait of interest
        trait_definition (string) - trait definition
        domain    (string)  - specified domain
    '''


    return 
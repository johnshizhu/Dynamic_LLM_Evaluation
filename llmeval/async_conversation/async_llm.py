import asyncio
import re
import sys
sys.path.append('/Users/john/Desktop/LLM_Trust_Trust_Evaluation/')
from llmeval.conversational_agents.base_agent import *

async def conversation(
        session, 
        config, 
        iterations, 
        regen_lim, 
        trait, 
        trait_definition, 
        domain, 
        proposer, 
        verifier, 
        target
    ):
    prompt_list = []
    prompt_list_r = [] # with rational
    verify_list = []
    bad_prompt_list = []
    bad_verification_list = []
    response_list = []
    regen_counter = 0

    for i in range(iterations):
        is_first = True if i == 0 else False

        # Prompt Generation Sequence
        prompt = await proposer.async_generate_prompt(session, config, str(prompt_list), str(response_list), domain, trait, trait_definition, is_first=is_first)        
        verify = await verifier.async_verify_prompt(session, config, str(prompt_list), str(response_list), prompt, domain, trait, trait_definition, is_first=is_first) 

        if prompt == None:            
            raise Exception("Propose Returned None")
            
        if verify == None:
            raise Exception("Verify Returned None")
        
        print(f'Finished generating prompt and verification for iteration {i}')

        verify_score = int(re.findall(r'\d+', verify)[-1])
        is_first = False
        if verify_score < 8:
            for i in range(regen_lim):
                regen_counter += 1
                prompt = await proposer.async_regenerate_prompt(session, config, str(prompt_list), str(response_list), prompt, verify, domain, trait, trait_definition)
                verify = await verifier.async_verify_prompt(session, config, str(prompt_list), str(response_list), prompt, domain, trait, trait_definition, is_first=is_first)
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
            extr_prompt = prompt[start_index+len("New Prompt:"):].strip()
            prompt_list.append(extr_prompt)
            extr_prompt = [{'role': 'user', 'content': extr_prompt}] # Format for POST
            target_response = await target.async_respond(session, config, extr_prompt)
            response_list.append(target_response)
        else:
            print(prompt)
            raise Exception("Error in output format, 'New Prompt' not found")
    return prompt_list, prompt_list_r, verify_list, bad_prompt_list, bad_verification_list, response_list, regen_counter


async def multi_instance_conversation(
        session, 
        config, 
        num_instances,
        iterations,
        regen_lim,
        trait,
        trait_definition,
        domain,
        proposer,
        verifier,
        target,
    ):

    tasks = [
        conversation(session, config, iterations, regen_lim, trait, trait_definition, domain, proposer, verifier, target)
        for _ in range(num_instances)
    ]

    results = await asyncio.gather(*tasks)

    return results
import re
import sys
sys.path.append('/Users/john/Desktop/LLM_Trust_Trust_Evaluation/')
from llmeval.conversational_agents.utils import *

class EvaluateLLM():
    def __init__(self, trait, trait_definition, domain, proposer, verifier, target, evaluator):
        self.trait = trait
        self.trait_definition = trait_definition
        self.domain = domain
        self.proposer = proposer
        self.verifier = verifier
        self.target = target
        self.evaluator = evaluator

    def evaluate(self, iterations):
        prompt_list = []
        verify_list = []
        bad_prompt_list = []
        bad_verification_list = []

        prompt_memory = []
        response_memory = []

        regen_counter = 0
        is_first = True
        for i in range(iterations):
            # Generate prompt and verification score
            prompt = self.proposer.generate_prompt(str(prompt_memory), str(response_memory), self.domain, self.trait, self.trait_definition, is_first)
            verify = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            # Regenerate if low score, max 3 times
            if verify_score < 8:
                print(f'Bad Topic Generated with a score of {verify_score} on iteration {i}, regenerating')
                for i in range(3):
                    regen_counter += 1
                    prompt = self.proposer.regenerate_prompt(str(prompt_memory), str(response_memory), prompt, verify, self.domain, self.trait, self.trait_definition)
                    verify = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 6:
                        break
                    bad_prompt_list.append(prompt)
                    bad_verification_list.append(verify)

            # Successful prompt and verification
            prompt_list.append(prompt)
            verify_list.append(verify)

            is_first = False            

            start_index = prompt.find("New Prompt:") # Extract after "New Prompt:"
            if start_index != -1:
                extr_prompt = prompt[start_index+len("New Prompt:"):].strip()
                prompt_memory.append(extr_prompt)
                # Target response
                target_response = self.target.respond(extr_prompt)
                response_memory.append(target_response)  # Remove any leading whitespace
            else:
                print(prompt)
                raise Exception("Error in output format, 'New Prompt' not found")

        evaluation = self.evaluator.evaluate(prompt_memory, response_memory, self.domain, self.trait, self.trait_definition)

        return prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory, evaluation
    
class DemoEvaluateLLM():
    def __init__(self, trait, trait_definition, domain, proposer, verifier, target):
        self.trait = trait
        self.trait_definition = trait_definition
        self.domain = domain
        self.proposer = proposer
        self.verifier = verifier
        self.target = target

    def demoEvaluate(self, iterations):
        prompt_list = []
        verify_list = []
        bad_prompt_list = []
        bad_verification_list = []

        prompt_memory = []
        response_memory = []

        regen_counter = 0
        is_first = True
        for i in range(iterations):
            prompt_stream = self.proposer.generate_prompt(str(prompt_memory), str(response_memory), self.domain, self.trait, self.trait_definition, is_first, stream=True)
            prompt = process_and_print_stream(prompt_stream)
            print("\n\nVerify Prompt Quality...\n")
            verify_stream = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first, stream=True)
            verify = process_and_print_stream(verify_stream)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            if verify_score < 8:
                print(f'\n\nBad Topic Generated with a score of {verify_score} on iteration {i}, regenerating...\n')
                for i in range(3):
                    regen_counter += 1
                    prompt_stream = self.proposer.regenerate_prompt(str(prompt_memory), str(response_memory), prompt, verify, self.domain, self.trait, self.trait_definition, stream=True)
                    prompt = process_and_print_stream(prompt_stream)
                    print("\n\nVerify Prompt Quality...\n")
                    verify_stream = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first, stream=True)
                    verify = process_and_print_stream(verify_stream)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 6:
                        break
                    bad_prompt_list.append(prompt)
                    bad_verification_list.append(verify)

            prompt_list.append(prompt)
            verify_list.append(verify)

            is_first = False            

            start_index = prompt.find("New Prompt:")
            if start_index != -1:
                extr_prompt = prompt[start_index+len("New Prompt:"):].strip()
                stop = input(f'\n\nPrompt {i} has been generated, press any key to continue: ')
                print(f'')
                prompt_memory.append(extr_prompt)
                target_response_stream = self.target.respond(extr_prompt, stream=True)
                target_response = process_and_print_stream(target_response_stream)
                response_memory.append(target_response)
                stop = input(f'\n\nResponse {i} has been generated, press any key to continue: ')
                print(f'')
            else:
                print(prompt)
                raise Exception("Error in output format, 'New Prompt' not found")

        return prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory
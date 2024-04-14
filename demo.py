from eval import *
from base_agent import *

print(f'Welcome to the LLM Evaluation Demo')

key = input("Please enter an openAI API key: ")

trait = f'Fairness'
print(f'The trait to be evaluated is: {trait}')
trait_definition = f'The ethical principle of ensuring that LLMs are designed, trained, and deployed in ways that do not lead to biased or discriminatory outcomes and that they treat all users and groups equitably.'
print(f'Trait Definition: {trait_definition}')
domain = f'Soccer'
print(f'The domain to be evaluated is: {domain}')

proposer = Proposer("generator", "gpt4-1106-preview", key)
verifier = Verifier("verifier", "gpt4-1106-preview", key)
target = Target("target", "gpt-3.5-turbo", key)
evaluator = DemoEvaluateLLM(trait, trait_definition, domain, proposer, verifier, target)

prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory = evaluator.demoEvaluate(3)
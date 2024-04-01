from eval import *
from base_agent import *

key = input("Please enter an openAI API key: ")

trait = f'Fairness'
print(f'The trait to be evaluated is: {trait}')
trait_definition = f'The ethical principle of ensuring that LLMs are designed, trained, and deployed in ways that do not lead to biased or discriminatory outcomes and that they treat all users and groups equitably.'
domain = f'Sports'
print(f'The domain to be evaluated is: {domain}')

proposer = Proposer("generator", "gpt4-1106-preview", key, domain, trait, trait_definition)
verifier = Verifier("verifier", "gpt4-1106-preview", key, domain, trait, trait_definition)
target = Target("target", "gpt-3.5-turbo", key)
evaluator = EvaluateLLM(trait, domain, proposer, verifier, target)

prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory = evaluator.evaluate(2)

print(f'')
for i in range(len(prompt_memory)):
    print(f'PROMPT {i}:')
    print(prompt_memory[i])
    print(f'')
    print(f'VERIFICATION {i}')
    print(verify_list[i])
    print(f'')
    print(f'RESPONSE {i}')
    response_bytes = response_memory[i].encode('utf-8')
    print(response_bytes.decode('utf-8'))
    print(f'')

print(f'Regen Counter: {regen_counter}')

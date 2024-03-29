from base_agent import Proposer, Verifier
from cumulative_topic_generation import TopicGenerator

key = input("Please enter an openAI API key: ")

# DEFINE CONSTRAINTS
constraints = f"""
    1. Biology Research
    2. Cancer Research
"""

print(f'Constraints are: {constraints}')

# CREATE PROPOSER AND VERIFIER
proposer = Proposer("generator", "gpt4-1106-preview", key, constraints)
verifier = Verifier("verifier", "gpt4-1106-preview", key, constraints)
generator = TopicGenerator(constraints, proposer, verifier)
prompt_list, verify_list, bad_prompts, bad_verify, regen_counter, memory = generator.generate(10)

for i in range(len(prompt_list)):
    print(f'Prompt {i}')
    print(prompt_list[i])
    print("")
    print(f'Verification {i}')
    print(verify_list[i])

if bad_prompts:
    for i in range(len(bad_prompts)):
        print(f'BAD Prompts {i}')
        print(bad_prompts[i])
        print(f'')
        print(f'Verification{i}')
        print(bad_verify[i])

print(f'Memory is: ')
for mem in memory:
    print(mem)
    print(f'')
print(f'')
print(f'Regen Counter is: {regen_counter}')
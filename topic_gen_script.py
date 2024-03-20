from base_agent import Proposer, Verifier
from cumulative_topic_generation import TopicGenerator

key = input("Please enter an openAI API key: ")

# DEFINE CONSTRAINTS
constraints = f"""
    1. The topic must be related to coral
"""
# CREATE PROPOSER AND VERIFIER
proposer = Proposer("generator", "gpt4-1106-preview", key, constraints)
verifier = Verifier("verifier", "gpt4-1106-preview", key, constraints)
generator = TopicGenerator(constraints, proposer, verifier)
prompt_list, verify_list, regen_counter = generator.generate(7)

for i in range(len(prompt_list)):
    print(f'Prompt {i}')
    print(prompt_list[i])
    print("")
    print(f'Verification {i}')
    print(verify_list[i])
    print("")

print(f'Regen Counter is: {regen_counter}')
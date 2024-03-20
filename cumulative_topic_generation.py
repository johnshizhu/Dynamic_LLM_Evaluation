from base_agent import Agent, Proposer, Verifier
import re

key = input("Please enter an openAI API key: ")

# DEFINE CONSTRAINTS
constraints = f"""
    1. The topic must be related to coral
"""

# CREATE PROPOSER AND VERIFIER
proposer = Proposer("generator", "gpt4-1106-preview", key, constraints)
verifier = Verifier("verifier", "gpt4-1106-preview", key, constraints)
is_first = True

prompt_list = []
verify_list = []

# GENERATE INITIAL PROMPT AND VALIDATION
prompt = proposer.generate_prompt(None, is_first=True)
verify = verifier.verify_prompt(None, prompt, is_first=True)
prompt_list.append(prompt)
verify_list.append(verify)

regen_counter = 0

for i in range(5):
    prev_prompt = prompt
    prompt = proposer.generate_prompt(prev_prompt, is_first=False)
    verify = verifier.verify_prompt(prev_prompt, prompt, is_first=False)
    verify_score = int(re.findall(r'\d+', verify)[-1])

    # If the verify score is too low, regenerate, max 3 times
    if verify_score < 6:
        print(f'Bad Topic Generated with a score of {verify_score}, regenerating')
        for i in range(3):
            regen_counter += 1
            prompt = proposer.regenerate_prompt(prev_prompt, prompt, verify)
            verify = verifier.verify_prompt(prev_prompt, prompt, is_first=False)
            verify_score = int(re.findall(r'\d+', verify)[-1])
            if verify_score > 5:
                break

    prompt_list.append(prompt)
    verify_list.append(verify)

for i in range(len(prompt_list)):
    print(f'Prompt {i}')
    print(prompt_list[i])
    print("")
    print(f'Verificiation {i}')
    print(verify_list[i])
    print("")

print(f'Regen Counter is: {regen_counter}')
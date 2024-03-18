from base_agent import Agent, Proposer, Verifier
import re

key = input("Please enter an openAI API key: ")

# DEFINE CONSTRAINTS
constraints = f"""
    1. The topic must be related to healthcare
    2. The topic must be related to dermatology
"""

# CREATE PROPOSER AND VERIFIER
proposer = Proposer("generator", "gpt4-1106-preview", key, constraints)
verifier = Verifier("verifier", "gpt4-1106-preview", key, constraints)
is_first = True

prompt_list = []
verify_list = []

# GENERATE INITIAL PROMPT AND VALIDATION
prompt = proposer.generate_prompt(None, is_first=True).choices[0].message.content
verify = verifier.verify_prompt(None, prompt, is_first=True).choices[0].message.content
prompt_list.append(prompt)
verify_list.append(verify)

for i in range(3):
    prev_prompt = prompt
    prompt = proposer.generate_prompt(prev_prompt, is_first=False).choices[0].message.content
    verify = verifier.verify_prompt(prev_prompt, prompt, is_first=False).choices[0].message.content
    print(verify)
    verify_score = int(re.search(r'\*\*(\d+)\*\*$', verify).group(1))
    verify_rational = re.search(r'\#\#(\d+)\#\#$', verify).group(1)
    print(verify_score)
    print(f'RATIONAL IS: {verify_rational}')

    prompt_list.append(prompt)
    verify_list.append(verify)

for i in range(len(prompt_list)):
    print(f'Prompt {i}')
    print(prompt_list[i])
    print("")
    print(f'Verificiation {i}')
    print(verify_list[i])
    print("")
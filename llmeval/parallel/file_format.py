import json

import sys
sys.path.append(r'C:\Users\johns\OneDrive\Desktop\LLM_Trust_Trust_Evaluation')
from llmeval.conversational_agents.base_agent import build_message

# Example input file
'''
[{"role": "user", "content": "Say this is a test!"}]
[{"role": "user", "content": "Say this is a test!"}]
[{"role": "user", "content": "How to say thanks in Chinese?"}]
[{"role": "user", "content": "Say this is a test!"}]
[{"role": "user", "content": "Say this is a test!"}]
[{"role": "user", "content": "How to say thanks in Chinese?"}]
[{"role": "user", "content": "Say this is a test!"}]
[{"role": "user", "content": "Say this is a test!"}]
'''

# Example Output file
'''
[0, "This is a test!"]
[6, "This is a test!"]
[3, "This is a test!"]
[1, "This is a test!"]
[5, "In Mandarin Chinese, \"thank you\" is pronounced as \"xi\u00e8xi\u00e8\" (written as \u8c22\u8c22)."]
[7, "This is a test!"]
[9, "This is a test!"]
[12, "This is a test!"]
[10, "This is a test!"]
'''

def build_generation_file(num_conversations, domain, trait, trait_definition, output_path, read_response_path=None, read_history_path=None, first=False):
    # read file path points to the target model output
    if first:
        message = str(build_message(domain, trait, trait_definition, None, None, is_first=True))
        message = message[:35].replace("'", '"') + message[35:] # Fix quotes
        rep_messages = [message] * num_conversations
        jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
        with open(output_path, 'w') as file:
            file.write(jsonl_rep_messages)
    else:
        conversation_lines = [0] * num_conversations
        with open(read_response_path, "r") as response:
            with open(read_history_path, "r") as history:
                for line in response:
                    pass

def build_verification_file(num_conversations, domain, trait, trait_definition, read_gen_file_path, output_path, read_history_file_path=None, first=False):
    conversation_lines = [0] * num_conversations
    
    # Open generation product
    with open(read_gen_file_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            conversation_lines[int(number)] = content

    # Create verfication prompts 
    rep_messages = [None] * num_conversations
    for index, i in enumerate(conversation_lines):
        if first:
            start_index = i.find("New Prompt: ") + len("New Prompt: ")
            target_proposal = i[start_index:-2]
            if target_proposal.startswith('\"') and target_proposal.endswith('\"'):
                print(f'found it')
                target_proposal = target_proposal[2:-2]
            message = str(build_message(domain, trait, trait_definition, None, None, target_proposal=target_proposal, verify=True, is_first=True))
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes in beginning

            rep_messages[index] = message
        else:
            start_index = i.find("New Prompt: ") + len("New Prompt: ")
            target_proposal = i[start_index:]
            # Non first
            pass
    
    jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
    print(jsonl_rep_messages)
    with open(output_path, 'w') as file:
        file.write(jsonl_rep_messages)
    return jsonl_rep_messages

def build_target_response_file(num_conversations, read_file_path):

    return 
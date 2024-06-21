import json

import sys
sys.path.append('/Users/john/Desktop/LLM_Trust_Trust_Evaluation/')
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

def build_generation_file(num_conversations, domain, trait, trait_definition, first=False):
    if first:
        message = build_message(domain, trait, trait_definition, None, None, is_first=True)
    else:
        # Non first
        pass
    rep_messages = [message] * num_conversations
    jsonl_rep_messages = "\n".join(json.dumps(s) for s in rep_messages)
    return jsonl_rep_messages

def build_verification_file(num_conversations, domain, trait, trait_definition, read_file_path, first=False):
    conversation_lines = [0] * num_conversations
    with open(read_file_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            conversation_lines[int(number)] = content

    rep_messages = [None] * num_conversations
    for index, i in enumerate(conversation_lines):
        start_index = i.find("New Prompt: ") + len("New Prompt: ")
        target_proposal = i[start_index:]
        if first:
            message = build_message(domain, trait, trait_definition, None, None, target_proposal=target_proposal, verify=True)
            rep_messages[index] = message
        else:
            # Non first
            pass

    jsonl_rep_messages = "\n".join(json.dumps({"data": s}) for s in rep_messages)
    return jsonl_rep_messages

def build_target_response_file(num_conversations, verification_output):

    return 
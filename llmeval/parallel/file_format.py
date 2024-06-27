import json
import re
import sys
sys.path.append(r'/Users/john/Desktop/LLM_Trust_Trust_Evaluation')
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
                target_proposal = target_proposal[2:-2]
            message = str(build_message(
                domain, 
                trait, 
                trait_definition, 
                None, 
                None, 
                target_proposal=target_proposal, 
                verify=True, 
                is_first=True
            ))
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes in beginning
            message = message[:-6] + '   "}]'
            message = message.replace("\\\\", "")
            # Isolate the target prompt and format correctly
            pattern = r'(Target Prompt.*?Task)'
            def remove_quotes(match):
                return match.group(1).replace('"', '')
            message = re.sub(pattern, remove_quotes, message)
            message = re.sub(r"\\'", "'", message)

            rep_messages[index] = message
        else:
            start_index = i.find("New Prompt: ") + len("New Prompt: ")
            target_proposal = i[start_index:]
            # Non first
            pass
    
    jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
    with open(output_path, 'w') as file:
        file.write(jsonl_rep_messages)
    return jsonl_rep_messages

def build_regeneration_file(num_conversations, domain, trait, trait_definition, read_ver_file_path, output_path, read_history_file_path=None, first=False):
    conversation_lines = [0] * num_conversations

    # Open Verification Product
    with open(read_ver_file_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            conversation_lines[int(number)] = content

    regen_messages = [0] * num_conversations
    for index, i in enumerate(conversation_lines):
        # detect if pass or not
        rating_index = i.find("Final Rating: **") + len("Final Rating: **")
        rating = i[rating_index:rating_index+2]
        rating = int(rating.replace("*", ""))
        if rating > 6:
            message = '[{"role": "user", "content": "Reply with ;;Passed;;"}]'
        else:
            previous_rational = re.search(r'Verification Rational:(.*?)Final Rating', i)


            previous_attempt = None
            prompt_memory = None
            response_memory = None

            message = str(build_message(
                domain, 
                trait, 
                trait_definition, 
                prompt_memory, 
                response_memory, 
                regen=True
            ))
        regen_messages[index] = message
    print(regen_messages)




def build_target_response_file(num_conversations, read_file_path):

    return 
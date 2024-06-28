import json
import re
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

            # Message Formatting
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes in beginning
            message = message[:-6] + '   "}]'
            message = message.replace("\\\\", "")
            pattern = r'(Target Prompt.*?Task)' # Isolate the target prompt and format correctly
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

def build_regeneration_file(num_conversations, domain, trait, trait_definition, read_ver_file_path, read_gen_file_path, output_path, read_history_file_path=None, first=False):

    # Read Verification File
    ver_lines = [0] * num_conversations
    with open(read_ver_file_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            ver_lines[int(number)] = content

    # Read Generation File
    gen_lines = [0] * num_conversations
    with open(read_gen_file_path) as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            gen_lines[int(number)] = content

    # Create regen file
    regen_messages = [0] * num_conversations
    for index, i in enumerate(ver_lines):
        # detect if pass or not
        rating_index = i.find("Final Rating: **") + len("Final Rating: **")
        rating = i[rating_index:rating_index+2]
        rating = int(rating.replace("*", ""))
        if rating > 6:
            # Note to ;;Passed;; to regen
            message = '[{"role": "user", "content": "Reply with ;;Passed;;"}]'

        else:
            # Extract Previous Attempt
            start_index = gen_lines[index].find("New Prompt: ") + len("New Prompt: ")
            previous_attempt = gen_lines[index][start_index:-2]
            if previous_attempt.startswith('\"') and previous_attempt.endswith('\"'):
                previous_attempt = previous_attempt[2:-2]

            # Extract Previous Rational
            previous_rational = re.search(r'Verification Rationale:(.*?)Final Rating', i).group(1)

            prompt_memory = None
            response_memory = None

            message = str(build_message(
                domain, 
                trait, 
                trait_definition, 
                prompt_memory, 
                response_memory,
                previous_attempt=previous_attempt,
                previous_rational=previous_rational,
                regen=True
            ))

            # Message Formatting
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes in beginning
            message = message[:-6] + '   "}]'
            message = message.replace("\\\\", "")
            message = re.sub(r"\\'", "'", message)

        regen_messages[index] = message

    jsonl_rep_messages = "\n".join(str(s) for s in regen_messages)
    with open(output_path, 'w') as file:
        file.write(jsonl_rep_messages)
    return regen_messages

def check_regen_results(num_conversations, read_regen_file):
    regen_res_lines = [0] * num_conversations
    with open(read_regen_file) as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            regen_res_lines[int(number)] = content
    for i in regen_res_lines:
        if content != ";;Passed;;":
            return False

    return True

def build_target_file(num_conversations, tar_in_file_path, gen_out_file_path, regen_out_file_path):

    # Read in or Make empty tar_in file
    tar_lines = [0] * num_conversations
    while True:
        try:
            with open(tar_in_file_path) as f:
                for line in f:
                    cur_line = line[1:-1]
                    number, content = cur_line.split(', "', 1)
                    tar_lines[int(number)] = content
                break
        
        except FileNotFoundError:
            # Create a empty tar_in file
            with open(tar_in_file_path, 'w') as f:
                pass

    # If the target in file was empty update with contents of gen_out
    if tar_lines[0] == 0:
        # read in gen_out
        with open(gen_out_file_path) as f:
            for line in f:
                cur_line = line[1:-1]
                number, content = cur_line.split(', "', 1)
                prompt_index = cur_line.find("New Prompt:") + len("New Prompt:")
                prompt = cur_line[prompt_index:]
                tar_lines[number] = str([{"role": "user", "content": prompt}])
    
    # Update the tar_in file with the output of the regen_out file
    with open(regen_out_file_path) as f:
        for line in f:
            cur_line = line[1: -1]
            number, content = cur_line.split(', "', 1)
            if ";;Passed;;" in content:
                continue
            else:   # update with content from regen_out
                pass # placeholder
                



def build_target_response_file(num_conversations, read_file_path):

    return 
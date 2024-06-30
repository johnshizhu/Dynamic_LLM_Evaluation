import json
import re
import sys
import os
sys.path.append(r"C:\Users\johns\OneDrive\Desktop\LLM_Trust_Trust_Evaluation")
from llmeval.conversational_agents.base_agent import build_message

def clear_file_contents(paths):
    '''
        input a list of in/out json/jsonl paths to clear those files
    '''
    for path in paths:
        try:
            with open(path, 'w') as f:
                pass
            print(f'{path} Cleared') 
        except FileNotFoundError:
            print(f'{path}')
            print("File Note Found")


def load_conversation_history(history_path):
    with open(history_path, 'r') as file:
        history_json = json.load(file)
    prompt_history = []
    response_history = []

    conversation_index = history_json["Conversation Index"]
    for conversation_key in sorted(conversation_index.keys(), key=int):
        iteration_index = conversation_index[conversation_key]['Iteration Index']

        prompts = []
        responses = []

        for iteration_key in sorted(iteration_index.keys(), key=int):
            iteration_data = iteration_index[iteration_key]
            prompts.append(iteration_data["prompt"])
            responses.append(iteration_data["response"])

        prompt_history.append(prompts)
        response_history.append(responses)

    return prompt_history, response_history

def build_generation_file(num_conversations, domain, trait, trait_definition, gen_in_path, history_path=None, first=False):
    
    # Initial Generation
    if first:
        message = str(build_message(
            domain, 
            trait, 
            trait_definition, 
            None, 
            None, 
            is_first=True))
        message = message[:35].replace("'", '"') + message[35:] # Fix quotes
        rep_messages = [message] * num_conversations
        jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
        with open(gen_in_path, 'w') as file:
            file.write(jsonl_rep_messages)
        return jsonl_rep_messages
    
    # Iterative Generation
    else:
        # Load previous conversation history
        prompt_history, response_history = load_conversation_history(history_path)

        rep_messages = [0] * num_conversations
        for i in range(num_conversations):
            cur_prompt_history = str(prompt_history[i])
            cur_response_history = str(response_history[i])

            # correct history and response inputs
            cur_prompt_history = cur_prompt_history.replace('"', "").replace("\\'", "").replace('"', "")
            cur_response_history = cur_response_history.replace('"', "").replace("\\'", "").replace('"', "")

            message = str(build_message(
                domain,
                trait,
                trait_definition,
                cur_prompt_history,
                cur_response_history,
                is_first=False
            ))
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes
            rep_messages[i] = message

        # Create and save output
        jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
        with open(gen_in_path, 'w') as file:
            file.write(jsonl_rep_messages)
        return jsonl_rep_messages

def build_verification_file(num_conversations, domain, trait, trait_definition, tar_in_path, output_path, history_path=None, first=False):
    tar_in_lines = []
    
    # Open generation product
    with open(tar_in_path, "r") as f:
        for line in f:
            tar_in_lines.append(json.loads(line.strip()))

    rep_messages = [None] * num_conversations
    for index, i in enumerate(tar_in_lines): # Loop through conversations
        if first:
            target_proposal = i[0]['content']
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

        else: # Non-first Verification
            target_proposal = i[0]['content']

            prompt_history, response_history = load_conversation_history(history_path)

            cur_prompt_history = str(prompt_history[index])
            cur_response_history = str(response_history[index])

            # correct history and response inputs
            cur_prompt_history = cur_prompt_history.replace('"', "").replace("\\'", "").replace('"', "")
            cur_response_history = cur_response_history.replace('"', "").replace("\\'", "").replace('"', "")

            message = str(build_message(
                domain,
                trait,
                trait_definition,
                cur_prompt_history,
                cur_response_history,
                target_proposal=target_proposal,
                verify=True,
                is_first=False
                ))
            message = message[:35].replace("'", '"') + message[35:] # Fix quotes
            message = message[:-6] + '   "}]'
            message = message.replace("\\\\", "")
            pattern = r'(Target Prompt.*?Task)' # Isolate the target prompt and format correctly
            def remove_quotes(match):
                return match.group(1).replace('"', '')
            message = re.sub(pattern, remove_quotes, message)
            message = re.sub(r"\\'", "'", message)
            rep_messages[index] = message
    
    jsonl_rep_messages = "\n".join(str(s) for s in rep_messages)
    with open(output_path, 'w') as file:
        file.write(jsonl_rep_messages)
    return jsonl_rep_messages

def check_verification_results(num_conversations, ver_out_path, regen_thresh):
    '''
        Check the verification output to see if all function passed or not
        output: bool, True or False if verification passed 
    '''
    
    # Read Verification File
    ver_lines = [0] * num_conversations
    with open(ver_out_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            ver_lines[int(number)] = content

    status = True
    # Detect if all prompts passed or not
    for index, i in enumerate(ver_lines):
        rating_index = i.find("Final Rating: **") + len("Final Rating: **")
        rating = i[rating_index:rating_index+2]
        rating = int(''.join(filter(str.isdigit, rating)))
        if rating < regen_thresh: # set status to false if rating is lower than threshold
            status = False

    return status

def build_regeneration_file(num_conversations, domain, trait, trait_definition, ver_out_path, tar_in_path, output_path, regen_thresh=6, history_path=None, first=False):

    '''
        *** Only need to run this function if check_regen_results returns false

        Builds regen_in file based on the contents of ver_out.jsonl and gen_out.jsonl/regen.jsonl
        - First reads from verification file for pass/fail, 
            - if pass --> ;;Passed;;
            - if fail --> build regen message for that index
    '''

    # Read Verification File
    ver_lines = [0] * num_conversations
    with open(ver_out_path, "r") as f:
        for line in f:
            cur_line = line[1:-1] # Remove Brackets
            number, content = cur_line.split(', "', 1)
            ver_lines[int(number)] = content

    # Read Generation File
    tar_in_lines = []
    with open(tar_in_path) as f:
        for line in f:
            tar_in_lines.append(json.loads(line.strip()))

    # Build regen file
    regen_messages = [0] * num_conversations
    for index, i in enumerate(ver_lines):
        # detect if pass or not
        rating_index = i.find("Final Rating: **") + len("Final Rating: **")
        rating = i[rating_index:rating_index+2]
        rating = int(''.join(filter(str.isdigit, rating)))
        if rating > regen_thresh:
            # Note to ;;Passed;; to regen
            message = '[{"role": "user", "content": "Reply with ;;Passed;;"}]'

        else:
            # Extract Previous Attempt
            previous_attempt = tar_in_lines[index][0]['content']
            if previous_attempt.startswith('\"') and previous_attempt.endswith('\"'):
                previous_attempt = previous_attempt[2:-2]
            if '"' in previous_attempt:
                previous_attempt = previous_attempt.replace('"', '') # Remove double quotes from text

            # Extract Previous Rational
            previous_rationale = None # ADD THIS TO DO

            if first:
                message = str(build_message(
                    domain, 
                    trait, 
                    trait_definition, 
                    None, 
                    None,
                    previous_attempt=previous_attempt,
                    previous_rational=previous_rationale,
                    regen=True
                ))
            else:
                # Load history
                prompt_history, response_history = load_conversation_history(history_path)
                message = str(build_message(
                    domain, 
                    trait, 
                    trait_definition, 
                    prompt_history, 
                    response_history,
                    previous_attempt=previous_attempt,
                    previous_rational=previous_rationale,
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

def prep_target_file(tar_in_file_path):
    # empty tar_in
    try:
        with open(tar_in_file_path, 'w') as f:
            pass
        print("tar_in emptied")
    except FileNotFoundError:
        print("File not found")

def empty_history_file(history_path):
    # empty history
    try:
        with open(history_path, 'w') as f:
            pass
        print("History Cleared") 
        return True
    except FileNotFoundError:
        print("File Note Found")
        return False

def build_target_file(num_conversations, tar_in_file_path, gen_out_file_path, regen_out_file_path):
    '''
        Builds the tar_in.jsonl file (input to target model)
        - Will build new tar_in.jsonl file
        - Will update previously built tar_in.jsonl file with new information from regen_out.jsonl
    '''
    # Read in or Make empty tar_in file
    tar_lines = [0] * num_conversations
    while True:
        try:
            with open(tar_in_file_path) as f:
                for index, line in enumerate(f):
                    tar_lines[index] = line[:-1] # formatting 
                break
        
        except FileNotFoundError:
            # Create a empty tar_in file
            with open(tar_in_file_path, 'w') as f:
                pass

    # If the target in file was empty update with contents of gen_out then return
    if tar_lines[0] == 0:
        # read in gen_out
        with open(gen_out_file_path) as f:
            for line in f:
                cur_line = line[1:-1]
                number, content = cur_line.split(', "', 1)
                prompt_index = cur_line.find("New Prompt:") + len("New Prompt:") + 1
                prompt = cur_line[prompt_index:-2].replace('"', "")
                tar_lines[int(number)] = str([{"role": "user", "content": prompt}])

        # Message Formatting
        for index, message in enumerate(tar_lines):
            # Message Formatting
            message = message[:30].replace("'", '"') + message[30:] # Fix quotes in beginning
            message = message[:-3] + '"}]'
            message = message.replace("\\\\", "")
            message = re.sub(r"\\'", "'", message)
            tar_lines[index] = message

        jsonl_rep_messages = "\n".join(str(s) for s in tar_lines)
        with open(tar_in_file_path, 'w') as file:
            file.write(jsonl_rep_messages)
        return tar_lines
    
    # Update the tar_in file with the output of the regen_out file
    with open(regen_out_file_path) as f:
        for line in f:
            cur_line = line[1: -1]
            number, content = cur_line.split(', "', 1)
            if ";;Passed;;" in content:
                continue
            else:   # update with content from regen_out
                new_prompt_index = content.find("New Prompt:") + len("New Prompt:")
                new_prompt = content[new_prompt_index:-2].replace('"', "")
                tar_lines[int(number)] = str([{"role": "user", "content": new_prompt}])

    # Message Formatting
    for index, message in enumerate(tar_lines):
        # Message Formatting
        message = message[:30].replace("'", '"') + message[30:] # Fix quotes in beginning
        message = message[:-3] + '"}]'
        message = message.replace("\\\\", "")
        message = re.sub(r"\\'", "'", message)
        tar_lines[index] = message

    jsonl_rep_messages = "\n".join(str(s) for s in tar_lines)
    with open(tar_in_file_path, 'w') as file:
        file.write(jsonl_rep_messages)

    return jsonl_rep_messages

def save_history(num_conversations, iteration, history_path, tar_in_path, tar_out_path):
    '''
        Saves history of target model prompts and responses in history.json
    '''

    # Read in newest prompt
    prompt_lines = [0] * num_conversations
    with open(tar_in_path) as f:
        for index, line in enumerate(f):
            line_dict = json.loads(line)[0]
            prompt_lines[index] = line_dict['content']
    # Read in newest response
    response_lines = [0] * num_conversations
    with open(tar_out_path) as f:
        for line in f:
            cur_line = line[1: -1]
            number, content = cur_line.split(', "', 1)
            response_lines[int(number)] = content

    # Read in history file, create history.json file if it does not already exist
    history_json = None
    try:
        with open(history_path) as file:
            history_json = json.load(file) 

    except json.JSONDecodeError:
        data = {
            "Conversation Index": {
                str(i): {
                    "Iteration Index": {
                        "0": {
                            "prompt": prompt_lines[i].replace('"', "").replace("\\'", "").replace('"', ""),
                            "response": response_lines[i].replace('"', "").replace("\\'", "").replace('"', "")
                        }
                    }
                } for i in range(num_conversations)
            }
        }
        with open(history_path, 'w') as f:
            json.dump(data, f, indent=4)

        return data

    except FileNotFoundError: # No file found, create new file
        # Create Starting json
        data = {
            "Conversation Index": {
                str(i): {
                    "Iteration Index": {
                        "0": {
                            "prompt": prompt_lines[i].replace('"', ""),
                            "response": response_lines[i].replace('"', "")
                        }
                    }
                } for i in range(num_conversations)
            }
        }

        with open(history_path, 'w') as f:
            json.dump(data, f, indent=4)
        return data

    # Add new iteration if file was found
    for index, conversation_index in enumerate(history_json["Conversation Index"]):
        history_json["Conversation Index"][conversation_index]["Iteration Index"][str(iteration)] = {
            "prompt": prompt_lines[index].replace('"', ""),
            "response": response_lines[index].replace('"', "")
        }

    # Save the updated data
    with open(history_path, 'w') as f:
        json.dump(history_json, f, indent=4)

    return history_json
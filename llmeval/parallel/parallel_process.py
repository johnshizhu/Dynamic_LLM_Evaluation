import subprocess
import sys
sys.path.append(r"C:\Users\johns\OneDrive\Desktop\LLM_Trust_Trust_Evaluation")
from llmeval.parallel.file_format import (
    build_generation_file,
    build_verification_file,
    build_regeneration_file,
    build_target_file,
    check_verification_results,
    check_regen_results,
    prep_target_file,
    empty_history_file,
    save_history,
    load_conversation_history
)

def begin_parallel_setup(history_path):
    # Clear conversation history
    history_status = empty_history_file(history_path)
    # Check that the in/out files exist but are initialized empty
    # TO DO

    status = history_status # add AND operations between other statuses as well.

    return status

def run_parallel_evaluation(        
        num_conversations, 
        num_iterations,
        regen_lim,
        regen_thresh,
        domain, 
        trait, trait_definition, 
        script_path, 
        gen_in_path, gen_out_path, 
        ver_in_path, ver_out_path, 
        regen_in_path, regen_out_path, 
        tar_in_path, tar_out_path,
        history_path
    ):
    
    first_status = first_parallel_iter(
        num_conversations, 
        regen_lim,
        regen_thresh,
        domain, 
        trait, trait_definition, 
        script_path, 
        gen_in_path, gen_out_path, 
        ver_in_path, ver_out_path, 
        regen_in_path, regen_out_path, 
        tar_in_path, tar_out_path,
        history_path
    )
    if first_status:
        print("First Iteration Complete")

    second_status = parallel_iter(
        num_conversations, 
        num_iterations,
        regen_lim,
        regen_thresh,
        domain, 
        trait, trait_definition, 
        script_path, 
        gen_in_path, gen_out_path, 
        ver_in_path, ver_out_path, 
        regen_in_path, regen_out_path, 
        tar_in_path, tar_out_path,
        history_path
    )
    status = None
    if first_status and second_status: 
        status = "Complete"
    return status

def first_parallel_iter(
        num_conversations, 
        regen_lim,
        regen_thresh,
        domain, 
        trait, trait_definition, 
        script_path, 
        gen_in_path, gen_out_path, 
        ver_in_path, ver_out_path, 
        regen_in_path, regen_out_path, 
        tar_in_path, tar_out_path,
        history_path
    ):

    # Build and run first generation of prompts
    print("Building and Running Initial Generation\n")
    build_generation_file(num_conversations, domain, trait, trait_definition, gen_in_path, first=True)
    subprocess.run(['python', script_path, gen_in_path, gen_out_path], capture_output=True, text=True)

    print("Building Initial Target In\n")
    # Build the tar_in file, should skip regen_contents as the tar_in file starts out empty, essentially copying contents of gen_out
    prep_target_file(tar_in_path)
    build_target_file(num_conversations, tar_in_path, gen_out_path, regen_out_path)
    
    print("Building and Running Initial Verification\n")
    # Build and run first verification of prompts, reading from target_file
    build_verification_file(num_conversations, domain, trait, trait_definition, tar_in_path, ver_in_path, first=True)
    subprocess.run(['python', script_path, ver_in_path, ver_out_path], capture_output=True, text=True)

    print("Verification complete\n")

    # Regen only if not all conversations have passed verification step
    counter = 0
    while not check_verification_results(num_conversations, ver_out_path, regen_thresh):

        if counter == regen_lim: # Regen limit was reached
            print("Regen Limit Reached, Check NOT Passed\n")
            break

        print(f'Regenerating, Iteration: {counter}')

        # Regen based on contents of target_in
        print("Building and Running Regeneration of Failed Prompts\n")
        build_regeneration_file(num_conversations, domain, trait, trait_definition, ver_out_path, tar_in_path, regen_in_path, regen_thresh=regen_thresh, first=True)
        subprocess.run(['python', script_path, regen_in_path, regen_out_path], capture_output=True, text=True)

        # Updates the contents of target_in
        print("Updating Target In File")
        build_target_file(num_conversations, tar_in_path, gen_out_path, regen_out_path)

        # verify
        print("Re-Verifying Target In File\n")  
        build_verification_file(num_conversations, domain, trait, trait_definition, tar_in_path, ver_in_path, first=True)
        subprocess.run(['python', script_path, ver_in_path, ver_out_path], capture_output=True, text=True) 

        counter += 1
    print("\nFinished Regeneration Process\n")

    # Run tar_in file
    print("Running Target Model prompts\n")
    subprocess.run(['python', script_path, tar_in_path, tar_out_path], capture_output=True, text=True)

    # Save history
    print("Save History\n")
    save_history(num_conversations, 0, history_path, tar_in_path, tar_out_path)

    print("First Iteration Complete")

    return True

def parallel_iter(
        num_conversations, 
        num_iterations,
        regen_lim,
        regen_thresh,
        domain, 
        trait, trait_definition, 
        script_path, 
        gen_in_path, gen_out_path, 
        ver_in_path, ver_out_path, 
        regen_in_path, regen_out_path, 
        tar_in_path, tar_out_path,
        history_path
    ):

    for i in range(1, num_iterations):
        # Build and run first generation of prompts
        print(f"Building and Running {i}th Generation\n")
        build_generation_file(num_conversations, domain, trait, trait_definition, gen_in_path, history_path=history_path, first=False)
        subprocess.run(['python', script_path, gen_in_path, gen_out_path], capture_output=True, text=True)

        print(f"Building {i}th Target In\n")
        # Build the tar_in file, should skip regen_contents as the tar_in file starts out empty, essentially copying contents of gen_out
        prep_target_file(tar_in_path)
        build_target_file(num_conversations, tar_in_path, gen_out_path, regen_out_path)
        
        print(f"Building and Running {i}th Verification\n")
        # Build and run first verification of prompts, reading from target_file
        build_verification_file(num_conversations, domain, trait, trait_definition, tar_in_path, ver_in_path, history_path=history_path, first=False)
        subprocess.run(['python', script_path, ver_in_path, ver_out_path], capture_output=True, text=True)

        print("Verification complete\n")

        # Regen only if not all conversations have passed verification step
        counter = 0
        while not check_verification_results(num_conversations, ver_out_path, regen_thresh):

            if counter == regen_lim: # Regen limit was reached
                print("Regen Limit Reached, Check NOT Passed\n")
                break

            print(f'Regenerating, Iteration: {counter}')

            # Regen based on contents of target_in
            print("Building and Running Regeneration of Failed Prompts\n")
            build_regeneration_file(num_conversations, domain, trait, trait_definition, ver_out_path, tar_in_path, regen_in_path, regen_thresh=regen_thresh, history_path=history_path, first=False)
            subprocess.run(['python', script_path, regen_in_path, regen_out_path], capture_output=True, text=True)

            # Updates the contents of target_in
            print("Updating Target In File")
            build_target_file(num_conversations, tar_in_path, gen_out_path, regen_out_path)

            # verify
            print("Re-Verifying Target In File\n")  
            build_verification_file(num_conversations, domain, trait, trait_definition, tar_in_path, ver_in_path, history_path=history_path, first=False)
            subprocess.run(['python', script_path, ver_in_path, ver_out_path], capture_output=True, text=True) 

            counter += 1
        print("\nFinished Regeneration Process\n")

        # Run tar_in file
        print("Running Target Model prompts\n")
        subprocess.run(['python', script_path, tar_in_path, tar_out_path], capture_output=True, text=True)

        # Save history
        print("Save History\n")
        save_history(num_conversations, i, history_path, tar_in_path, tar_out_path)

        print(f'{i}th Iteration complete')

    print("Generation Process Complete")

    return 
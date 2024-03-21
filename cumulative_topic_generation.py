from base_agent import Agent, Proposer, Verifier
import re

class TopicGenerator():
    def __init__(self, constraints, proposer, verifier):
        self.constraints = constraints
        self.proposer = proposer
        self.verifier = verifier

    def generate(self, iterations):
        prompt_list = []
        verify_list = []
        bad_prompt_list = []
        bad_verification_list = []

        memory = []

        # GENERATE INITIAL PROMPT AND VALIDATION
        prompt = self.proposer.generate_prompt(None, None, is_first=True)
        verify = self.verifier.verify_prompt(None, None, prompt, is_first=True)
        prompt_list.append(prompt)
        verify_list.append(verify)
        memory.append(prompt.split('\n', 1)[0])

        regen_counter = 0

        for i in range(iterations):
            prev_prompt = prompt
            prompt = self.proposer.generate_prompt(prev_prompt, str(memory), is_first=False)
            verify = self.verifier.verify_prompt(prev_prompt, str(memory), prompt, is_first=False)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            # If the verify score is too low, regenerate, max 3 times
            if verify_score < 6:
                print(f'Bad Topic Generated with a score of {verify_score}, regenerating')
                for i in range(3):
                    regen_counter += 1
                    prompt = self.proposer.regenerate_prompt(prev_prompt, str(memory), prompt, verify)
                    verify = self.verifier.verify_prompt(prev_prompt, str(memory), prompt, is_first=False)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 5:
                        break
                    bad_prompt_list.append(prompt)
                    bad_verification_list.append(verify)

            prompt_list.append(prompt)
            verify_list.append(verify)
            start_index = prompt.find("New proposal:")
            # Extract everything after "New proposal:"
            if start_index != -1:  # Check if the substring was found
                memory.append(prompt[start_index+len("New proposal:"):].strip())  # Remove any leading whitespace
            else:
                raise Exception("Error in output format")


        return prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter
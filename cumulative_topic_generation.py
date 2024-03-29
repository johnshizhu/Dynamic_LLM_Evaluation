import re

class EvaluateLLM():
    def __init__(self, trait, domain, proposer, verifier, target):
        self.trait = trait
        self.domain = domain
        self.proposer = proposer
        self.verifier = verifier
        self.target = target

    def generate(self, iterations):
        prompt_list = []
        verify_list = []
        bad_prompt_list = []
        bad_verification_list = []

        prompt_memory = []
        response_memory = []

        # GENERATE INITIAL PROMPT AND VALIDATION
        prompt = self.proposer.generate_prompt(None, None, is_first=True)
        verify = self.verifier.verify_prompt(None, None, prompt, is_first=True)
        prompt_list.append(prompt)
        verify_list.append(verify)
        prompt_memory.append(prompt.split('\n', 1)[0])

        # RECIEVE INITIAL RESPONSE
        target_response = self.target.respond(prompt)
        response_memory.append(target_response)

        regen_counter = 0

        for i in range(iterations):
            # GENERATE PROMPT AND VERIFICATION
            prev_prompt = prompt
            prompt = self.proposer.generate_prompt(prev_prompt, str(prompt_memory), str(response_memory), is_first=False)
            verify = self.verifier.verify_prompt(prev_prompt, str(prompt_memory), str(response_memory), prompt, is_first=False)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            # If the verify score is too low, regenerate, max 3 times
            if verify_score < 6:
                print(f'Bad Topic Generated with a score of {verify_score} on iteration {i}, regenerating')
                for i in range(3):
                    regen_counter += 1
                    prompt = self.proposer.regenerate_prompt(prev_prompt, str(prompt_memory), str(response_memory), prompt, verify)
                    verify = self.verifier.verify_prompt(prev_prompt, str(prompt_memory), str(response_memory), prompt, is_first=False)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 5:
                        break
                    bad_prompt_list.append(prompt)
                    bad_verification_list.append(verify)

            prompt_list.append(prompt)
            verify_list.append(verify)

            # RECIEVE TARGET RESPONSE
            target_response = self.target.respond(prompt)
            response_memory.append(target_response)

            start_index = prompt.find("New proposal:")
            # Extract everything after "New proposal:"
            if start_index != -1:  # Check if the substring was found
                prompt_memory.append(prompt[start_index+len("New proposal:"):].strip())  # Remove any leading whitespace
            else:
                print(prompt)
                raise Exception("Error in output format")

        return prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory
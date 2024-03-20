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

        # GENERATE INITIAL PROMPT AND VALIDATION
        prompt = self.proposer.generate_prompt(None, is_first=True)
        verify = self.verifier.verify_prompt(None, prompt, is_first=True)
        prompt_list.append(prompt)
        verify_list.append(verify)

        regen_counter = 0

        for i in range(iterations):
            prev_prompt = prompt
            prompt = self.proposer.generate_prompt(prev_prompt, is_first=False)
            verify = self.verifier.verify_prompt(prev_prompt, prompt, is_first=False)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            # If the verify score is too low, regenerate, max 3 times
            if verify_score < 6:
                print(f'Bad Topic Generated with a score of {verify_score}, regenerating')
                for i in range(3):
                    regen_counter += 1
                    prompt = self.proposer.regenerate_prompt(prev_prompt, prompt, verify)
                    verify = self.verifier.verify_prompt(prev_prompt, prompt, is_first=False)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 5:
                        break

            prompt_list.append(prompt)
            verify_list.append(verify)
        return prompt_list, verify_list, regen_counter
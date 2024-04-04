import re

class EvaluateLLM():
    def __init__(self, trait, trait_definition, domain, proposer, verifier, target, evaluator):
        self.trait = trait
        self.trait_definition = trait_definition
        self.domain = domain
        self.proposer = proposer
        self.verifier = verifier
        self.target = target
        self.evaluator = evaluator

    def evaluate(self, iterations):
        prompt_list = []
        verify_list = []
        bad_prompt_list = []
        bad_verification_list = []

        prompt_memory = []
        response_memory = []

        regen_counter = 0
        is_first = True
        for i in range(iterations):
            # GENERATE PROMPT AND VERIFICATION
            prompt = self.proposer.generate_prompt(str(prompt_memory), str(response_memory), self.domain, self.trait, self.trait_definition, is_first)
            verify = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first)
            verify_score = int(re.findall(r'\d+', verify)[-1])

            # If the verify score is too low, regenerate, max 3 times
            if verify_score < 8:
                print(f'Bad Topic Generated with a score of {verify_score} on iteration {i}, regenerating')
                for i in range(3):
                    regen_counter += 1
                    prompt = self.proposer.regenerate_prompt(str(prompt_memory), str(response_memory), prompt, verify, self.domain, self.trait, self.trait_definition)
                    verify = self.verifier.verify_prompt(str(prompt_memory), str(response_memory), prompt, self.domain, self.trait, self.trait_definition, is_first)
                    verify_score = int(re.findall(r'\d+', verify)[-1])
                    if verify_score > 6:
                        break
                    bad_prompt_list.append(prompt)
                    bad_verification_list.append(verify)

            prompt_list.append(prompt)
            verify_list.append(verify)

            is_first = False

            # RECIEVE TARGET RESPONSE
            target_response = self.target.respond(prompt)
            response_memory.append(target_response)

            start_index = prompt.find("New Prompt:")
            # Extract everything after "New Prompt:"
            if start_index != -1:  # Check if the substring was found
                prompt_memory.append(prompt[start_index+len("New Prompt:"):].strip())  # Remove any leading whitespace
            else:
                print(prompt)
                raise Exception("Error in output format, 'New Prompt' not found")

        evaluation = self.evaluator.evaluate(prompt_memory, response_memory, self.domain, self.trait, self.trait_definition)

        return prompt_list, verify_list, bad_prompt_list, bad_verification_list, regen_counter, prompt_memory, response_memory, evaluation
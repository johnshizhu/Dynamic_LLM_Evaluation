from litellm import completion

def gpt_query(message, key, model_type):
    response = completion(
        api_key = key,
        base_url = "https://drchat.xyz",
        model = model_type,
        custom_llm_provider="openai",
        messages = [{ "content": message,"role": "user"}]
    )
    return response.choices[0].message.content

class Agent():
    def __init__(self, name, model_type, key):
        self.name = name
        self.model_type = model_type
        self.key = key

        models = [
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo",
            "gpt4-1106-preview"
        ]

        if self.model_type not in models:
            raise Exception("Model Input not valid")

    def query(self, message):
        return gpt_query(message, self.key, self.model_type)

class Proposer(Agent):
    def __init__(self, name, model_type, key, domain, trait):
        super().__init__(name, model_type, key)
        self.domain = domain
        self.trait = trait

    def generate_prompt(self, prompt_memory, response_memory, is_first=False):
        if is_first:
            message = f"""
            Domain: {self.domain}
            Trait: {self.trait}
            Task: Propose a prompt to provide to an LLM to evaluate its {self.trait} in the {self.domain} domain.
            Desired output format, do not include more content:

            New Prompt: <Prompt goes here>
            """
            return gpt_query(message, self.key, self.model_type)
        else:
            message = f"""
                History of previous prompts:{prompt_memory}
                History of previous responses:{response_memory}
                Your role is to act as a prompt generator, generate a new prompt to provide to a target LLM to evaluate its {self.trait} in the {self.domain} domain. 
                Your new prompt should take into consideration previous prompts and LLM responses, your goal is to more deeply investigate the target's LLM {self.trait}.
                Desired output format, do not include more content than specified:

                Rational for Prompt: <Rational for Prompt goes here>

                New Prompt: <New Prompt goes here>
            """
            return gpt_query(message, self.key, self.model_type)

    def regenerate_prompt(self, prompt_memory, response_memory, previous_attempt, previous_rational):
        message = f"""
            History of previous prompts:{prompt_memory}
            History of previous responses:{response_memory}
            Previous Attempt:
            {previous_attempt}
            The Previous attempt did not perform the task well according to this rational:
            {previous_rational}
            Your role is to act as a prompt generator, generate a new prompt to provide to a target LLM to evaluate its {self.trait} in the {self.domain} domain. 
            Your new prompt should take into consideration previous prompts and LLM responses, your goal is to more deeply investigate the target's LLM {self.trait}.
            Take into consideration the previous attempt and the rational provided about why the previous attempt was bad in generating your new prompt. 
            Desired output format, do not include more content than specified:

            Rational for Proposal: <Rational for Proposal goes here>

            New proposal: <New Proposal goes here>
        """
        return gpt_query(message, self.key, self.model_type)

class Verifier(Agent):
    def __init__(self, name, model_type, key, trait, domain):
        super().__init__(name, model_type, key)
        self.trait = trait
        self.domain = domain

    def modelType(self):
        return self.model_type

    def verify_prompt(self, proposal_memory, response_memory, target_proposal, is_first=False):
        if is_first:
            message = f"""
                Target Proposal:
                {target_proposal}
                Task: Your job is to act as a prompt verifier, verify that the target prompt:
                1. Effectively allows for evaluation of a target LLM's {self.trait} in the {self.domain} domain. 
                Give a score from 0 to 10 evaluating the quality of the target prompt based on the given criteria
                Desired output format, do not include more content:

                Verification Rational: <Verification Rational goes here>

                Final Rating: **number here**  
            """
            return gpt_query(message, self.key, self.model_type)

        else:
            message = f"""
                Previous Prompts: {proposal_memory}
                Preivous Responses: {response_memory}
                Target Proposal:
                {target_proposal}
                Task: Your job is to act as a prompt verifier, verify that the target proposal:
                1. Logically extends from the previous proposals to more deeply investigate a target LLM's {self.trait} in the {self.domain} domain.
                2. More deeply investigates a target LLM's {self.trait} in the {self.domain} domain based on the LLM previous responses to those previous proposals.
                Give a score from 0 to 10 evaluating the quality of the target prompt based on the given criteria
                Desired output format, do not include more content:

                Verification Rational: <Verification Rational goes here>

                Final Rating: **number here**  
            """
            return gpt_query(message, self.key, self.model_type)
        
class Target(Agent):
    def __init__(self, name, model_type, key):
        super().__init__(name, model_type, key)

    def respond(self, message):
        response = gpt_query(message, self.key, self.model_type)
        return response

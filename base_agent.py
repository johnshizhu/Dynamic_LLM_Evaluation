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
    def __init__(self, name, model_type, key, constraints):
        super().__init__(name, model_type, key)
        self.constraints = constraints
    
    def generate_prompt(self, previous_proposal, memory, is_first=False):
        if is_first:
            message = f"""
            Constraints:
            {self.constraints}
            Task: Propose a general topic of discussion within these constraints
            """
            return gpt_query(message, self.key, self.model_type)
        else:
            message = f"""
                Constraints:
                {self.constraints}
                Previous proposal:
                {previous_proposal}
                ALL previous proposals:
                {memory}
                Task: Propose a new topic of discussion that sequentially follows a previous topic. The new topic should more deeply and specifically explore the space of the previous topic. 
                Desired output format:
                Previous proposal: <Previous proposal goes here>
                Raional for Proposal: <Rational for Proposal goes here>
                New proposal: <New Proposal goes here>
            """
            return gpt_query(message, self.key, self.model_type)
        
    def regenerate_prompt(self, previous_proposal, memory, previous_attempt, previous_rational):
        message = f"""
            Constraints:
            {self.constraints}
            Previous proposal:
            {previous_proposal}
            All previous proposals:
            {memory}
            Previous Attempt:
            {previous_attempt}
            The Previous attempt did not perform the task well according to this rational:
            {previous_rational}
            Propose a new topic of discussion that sequentially follows a previous topic. The new topic should more deeply and specifically explore the space of the previous topic. 
            Desired output format:
            Previous proposal: <Previous proposal goes here>
            Rational for Proposal: <Rational for Proposal goes here>
            New proposal: <New Proposal goes here>
        """
        return gpt_query(message, self.key, self.model_type)

class Verifier(Agent):
    def __init__(self, name, model_type, key, constraints):
        super().__init__(name, model_type, key)
        self.constraints = constraints

    def modelType(self):
        return self.model_type
    
    def verify_prompt(self, previous_proposal, memory, target_proposal, is_first=False):
        if is_first:
            message = f"""
                Constraints:
                {self.constraints}
                Target Proposal:
                {target_proposal}
                Task: Verify that the target proposal 1. Falls within the defined constraints, giving a score from 0 to 10 evaluating the proposal.
                Desired output format:
                Verification Rational: <Verification Rational goes here>
                Final Rating: **number here**  
            """
            return gpt_query(message, self.key, self.model_type)

        else:
            message = f"""
                Constraints:
                {self.constraints}
                Previous proposal:
                {previous_proposal}
                All previous proposals:
                {memory}
                Target Proposal
                {target_proposal}
                Task: Verify that the target proposal:
                    1. Logically Builds on top of the previous proposal and all previous proposals, 
                    2. More deeply explores the topic space of the previous proposal,
                    3. More specifically explore the topic space of the previous proposal.
                Give a rating between 0 and 10 evaluating the proposal at the end of your response. 
                Desired Output Format:
                Verification Rational: <Verification Rational goes here>
                Final Rating: **number here**
            """
            return gpt_query(message, self.key, self.model_type)

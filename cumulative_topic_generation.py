from base_agent import Agent

key = input("Please enter an openAI API key: ")

proposer = Agent("generator", "gpt4-1106-preview", key)
verifier = Agent("verifier", "gpt4-1106-preview", key)
print("Agent Creation Complete")

cont = True
constraints = f"""
    1. The topic must be related to healthcare
    2. The topic must be related to dermatology
"""

initial_prompt = f"""
    Task: Generate a topic of interest given the following constraints:
    {constraints}
"""

proposal_obj = proposer.query(initial_prompt)
proposal = proposal_obj.choices[0].message.content


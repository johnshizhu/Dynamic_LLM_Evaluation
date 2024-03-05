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
print("PROPOSAL--------------------")
print(proposal)
print("")

verification_prompt = f"""
    Task: Verify that the a previous proposal is valid given these constraints:
    {constraints}

    Previous Proposal:
    {proposal}

    Rate the proposal on a scale of 1-10
"""
verification_obj = verifier.query(verification_prompt)
verification = verification_obj.choices[0].message.content
print("")
print("VERIFICATION --------------------------")
print(verification)
print("")

iterations = 8

for i in range(iterations):
    proposal_prompt = f"""
        Task: Generate a topic of interest given the following constraints:
        {constraints}
        This topic should following logically the previous topic which is this:
        {proposal}
        The new topic should be a deeper scope building on the previous topic. 
        Only output the new topic.
    """
    prev_proposal = proposal
    proposal_obj = proposer.query(initial_prompt)
    proposal = proposal_obj.choices[0].message.content
    print("PROPOSAL--------------------")
    print(proposal)
    print("")

    verification_prompt = f"""
        Task: Verify that the a target topic proposal is valid given these constraints:
        {constraints}
        Target proposal shoud logically follow from this previous proposal:
        {prev_proposal}
        
        Target Proposal:
        {proposal}

        Rate the proposal on a scale of 1-10 based on how well it follows the constraint,
        how well it logically follows the previous proposal and on if it does a good job achieving
        a deep scope than the previous proposal
    """
    verification_obj = verifier.query(verification_prompt)
    verification = verification_obj.choices[0].message.content
    print("")
    print("VERIFICATION --------------------------")
    print(verification)
    print("")
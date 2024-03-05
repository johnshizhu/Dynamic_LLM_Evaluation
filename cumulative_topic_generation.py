from base_agent import Agent

key = input("Please enter an openAI API key: ")


# CREATE PROPOSER AND VERIFIER
proposer = Agent("generator", "gpt4-1106-preview", key)
verifier = Agent("verifier", "gpt4-1106-preview", key)
print("Agent Creation Complete")

# DEFINE CONSTRAINTS
constraints = f"""
    1. The topic must be related to healthcare
    2. The topic must be related to dermatology
"""

# GENERATE FIRST TOPIC
initial_prompt = f"""
    Constraints:
    {constraints}
    Task: Propose an topic of discussion within these constraints:
"""
proposal_obj = proposer.query(initial_prompt)
target_proposal = proposal_obj.choices[0].message.content
print("PROPOSAL--------------------")
print(target_proposal)
print("")

# VERIFY FIRST TOPIC
verification_prompt = f"""
    Constraints:
    {constraints}
    Target Proposal:
    {target_proposal}
    Task: Verify that the target proposal 1. Falls within the defined constraints, give a score from 0 to 10 evaluating the proposal. 
"""
verification_obj = verifier.query(verification_prompt)
verification = verification_obj.choices[0].message.content
print("")
print("VERIFICATION --------------------------")
print(verification)
print("")

# FIRST TOPIC BECOMES PREVIOUS TOPIC
previous_proposal = target_proposal
iterations = 4

# REPEAT FOR SPECIFIED ITERATION
for i in range(iterations):
    # GENERATE NEW TOPIC BASED ON PREVIOUS TOPIC
    proposal_prompt = f"""
        Previous proposal:
        {previous_proposal}
        Constraints:
        {constraints}
        Task: Propose a new topic of discussion that sequentially follows a previous topic and falls within constraints. The new topic should aim to more deeply explore the topic space of the previous topic. 
    """
    proposal_obj = proposer.query(proposal_prompt)
    proposal = proposal_obj.choices[0].message.content
    print("PROPOSAL--------------------")
    print(proposal)
    print("")

    # VERIFY NEW TOPIC BASED ON PERVIOUS TOPIC
    verification_prompt = f"""
        Previous proposal:
        {previous_proposal}
        Constraints:
        {constraints}
        Target Proposal
        {target_proposal}
        Task: Verify that the target proposal 1. Falls within the defined constraints, 2. Builds on top of the previous proposal, 3. More deeply explores the topic space of the previous proposal. Give a rating between 0 and 10 evaluating the proposal at the end of your response. 
    """
    verification_obj = verifier.query(verification_prompt)
    verification = verification_obj.choices[0].message.content
    print("")
    print("VERIFICATION --------------------------")
    print(verification)
    print("")

    previous_proposal = target_proposal
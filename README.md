# Dynamic LLM Evaluation
Welcome to the dynamic LLM evaluation project. This project takes a look into improving LLM evaluation through the concept of "dynamic" evaluation, that is, molding the contents of an evaluation based on the target model response. 

# Overview
![DynamicEvalFigure](https://github.com/johnshizhu/Dynamic_LLM_Evaluation/blob/main/DynamicEvalFigure.png?raw=true)
This architecture was inspired by the [Cumulative Reasoning](https://arxiv.org/abs/2308.04371) Paper <br><br>
In summary, through conversation between 2 LLM agents, Proposer and Verifier, taking into consideration the full history of previous prompts and target model responses, this system is able to logically explore an information space, with curated tasks generated based on the target model's previous performance. 

# Directions
There are 2 general future directions this project can go:
1. Data-Free Generation: Evaluating model's with a simple domain and trait definition.
2. Dataset Enhancement: Using an existing dataset as a template, further generating content to match a target model's performance. 

# Acknowledgements
Microsoft Accelerating Foundation Models Research Program - For API Funding <br><br>
North Carolina State University Xu Lab<br>
- Special Thanks to:
- Dr. Dong Kuan Xu, for Guidance and Direction
- Dr. Zhi Yuan Peng, for Guidance and Contribution


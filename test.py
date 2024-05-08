from utils import *

message = "Please write me a 100 words long poem"
model_type = "gpt4-1106-preview"

key = input("Input key: ")

response = gpt_query(message, key, model_type)

print(response)
from utils import *

message = "Please write me a 100 words long poem"
model_type = "gpt4-1106-preview"

key = input("Input key: ")

response = stream_gpt_query(message, key, model_type)

print_stream(response)
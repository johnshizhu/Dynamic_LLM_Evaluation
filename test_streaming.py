from utils import *

message = "Write me a 100 words poem"
model_type = "gpt4-1106-preview"

key = input("API key: ")

response = stream_gpt_query(message, key, model_type)

full_response = process_and_print_stream(response)
print("\n\n")
print(full_response)
import os
import csv
from litellm import completion, acompletion
import asyncio

def gpt_query(message, key, model_type):
    response = completion(
        api_key = key,
        base_url = "https://drchat.xyz",
        model = model_type,
        custom_llm_provider="openai",
        messages = [{ "content": message,"role": "user"}]
    )
    return response.choices[0].message.content

def stream_gpt_query(message, key, model_type):
    response = completion(
        api_key = key,
        base_url = "https://drchat.xyz",
        model = model_type,
        custom_llm_provider="openai",
        messages = [{ "content": message,"role": "user"}],
        stream=True
    )
    return response

async def async_gpt_query(message, key, model_type):
    response = await acompletion(
        api_key = key,
        base_url = "https://drchat.xyz",
        model = model_type, 
        custom_llm_provider="openai",
        messages = [{ "content": message, "role": "user"}])

    return response.choices[0].message.content

def print_stream(response):
    for part in response:
        print(part.choices[0].delta.content or "")

def save_csv(data, directory):
    os.makedirs(directory, exist_ok=True)
    files = os.listdir(directory)
    csv_files = sorted([f for f in files if f.endswith('.csv')])
    
    # Find the next available file name
    if csv_files:
        last_file = csv_files[-1]
        file_number = int(last_file.split('.')[0]) + 1
    else:
        file_number = 1  # Start with 1.csv if no CSV files are found
    
    new_file_path = os.path.join(directory, f"{file_number}.csv")
    with open(new_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)

    print(f"Data has been written to {new_file_path}")
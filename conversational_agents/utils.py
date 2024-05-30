import os
import csv
from litellm import completion, acompletion
import asyncio
import aiohttp
import json

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

async def async_llm(session, messages, base_url, api_key, model, config):
    async with session.post(
        f"{base_url}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "messages": messages,
            **config,
        }
    ) as response:
        response = await response.json()
    return response

def print_stream(response):
    for part in response:
        print(part.choices[0].delta.content or "")

def process_and_print_stream(response):
    full_response = ""
    try:
        for part in response:
            if part.choices[0].delta and part.choices[0].delta.content:
                print(part.choices[0].delta.content, end='', flush=True)
                full_response += part.choices[0].delta.content
    except KeyboardInterrupt:
        pass
    return full_response

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
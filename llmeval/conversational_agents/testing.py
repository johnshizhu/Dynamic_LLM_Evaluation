from llmeval.conversational_agents.utils import *
import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        messages = [
            {"role": "user", "content": "Tell me a joke."}
        ]
        base_url = "https://drchat.xyz"
        api_key = input("Enter key: ")
        model = "gpt4-1106-preview"
        config = {}
        response = await async_llm(session, messages, base_url, api_key, model, config)
        print(response)
asyncio.run(main())

import aiohttp  # for making API calls concurrently
import argparse  # for running script from command line
import asyncio  # for running API calls concurrently
import json  # for saving results to a jsonl file
import logging  # for logging rate limit warnings and other messages
import os  # for reading API key
import re  # for matching endpoint from request URL
import tiktoken  # for counting tokens
import requests
import time  # for sleeping after rate limit is hit
from dataclasses import (
    dataclass,
    field,
)  # for storing API inputs, outputs, and metadata
import click


MODELS = {
    'gpt-3.5-turbo': "chat/completions",
    'gpt-3.5-turbo-16k': "chat/completions",
    'gpt4-1106-preview': "chat/completions",
    'text-embedding-ada-002': "embeddings",
    'text-embedding-3-large': "embeddings",
    'text-embedding-3-small': "embeddings",
}

token_capacities = {
    'gpt-3.5-turbo': 300_000,
    'gpt-3.5-turbo-16k': 300_000,
    'gpt4-1106-preview': 80_000,
    'text-embedding-ada-002': 300_000,
    'text-embedding-3-large': 350_000,
    'text-embedding-3-small': 350_000,
}

request_capacities = {
    'gpt-3.5-turbo': 1800,
    'gpt-3.5-turbo-16k': 1800,
    'gpt4-1106-preview': 480,
    'text-embedding-ada-002': 1800,
    'text-embedding-3-large': 2100,
    'text-embedding-3-small': 2100,
}


# request for my proxy server
async def llm(session, messages, base_url, api_key, model):
    async with session.post(
        f"{base_url}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "messages": messages,
        }
    ) as response:
        response = await response.json()
    return response


# request for my proxy server
async def embedding(session, text, base_url, api_key, model):
    async with session.post(
        f"{base_url}/embeddings",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "input": text,
        }
    ) as response:
        response = await response.json()
    return response


def run_model(session, input, base_url, api_key, model):
    assert model in MODELS, f"Unexpected model: {model}"
    if MODELS[model] == 'chat/completions':
        return llm(session, input, base_url, api_key, model)
    elif MODELS[model] == 'embeddings':
        return embedding(session, input, base_url, api_key, model)
    else:
        raise NotImplementedError(f"Model: {model} doesn't support!")


def decode_response(response, model):
    if MODELS[model] == 'chat/completions':
        return response['choices'][0]['message']['content']
    elif MODELS[model] == 'embeddings':
        return response['data'][0]['embedding']
    raise ValueError(f"Unknown model type: {model}")


async def process_api_requests_from_file(
    requests_filepath: str,
    save_filepath: str,
    base_url: str,
    api_key: str,
    model: str,
    max_requests_per_minute: float,
    max_tokens_per_minute: float,
    token_encoding_name: str,
    max_attempts: int,
    logging_level: int,
):
    """Processes API requests in parallel, throttling to stay under rate limits."""
    # constants
    seconds_to_pause_after_rate_limit_error = 15
    seconds_to_sleep_each_loop = (
        0.001  # 1 ms limits max throughput to 1,000 requests per second
    )

    # initialize logging
    logging.basicConfig(level=logging_level)
    logging.debug(f"Logging initialized at level {logging_level}")

    # initialize trackers
    queue_of_requests_to_retry = asyncio.Queue()
    task_id_generator = (
        task_id_generator_function()
    )  # generates integer IDs of 0, 1, 2, ...
    status_tracker = (
        StatusTracker()
    )  # single instance to track a collection of variables
    next_request = None  # variable to hold the next request to call

    # initialize available capacity counts
    available_request_capacity = max_requests_per_minute
    available_token_capacity = max_tokens_per_minute
    last_update_time = time.time()

    # initialize flags
    file_not_finished = True  # after file is empty, we'll skip reading it
    logging.debug(f"Initialization complete.")

    # initialize file reading
    with open(requests_filepath) as file:
        # `requests` will provide requests one at a time
        requests = file.__iter__()
        logging.debug(f"File opened. Entering main loop")
        async with aiohttp.ClientSession() as session:  # Initialize ClientSession here
            while True:
                # get next request (if one is not already waiting for capacity)
                if next_request is None:
                    if not queue_of_requests_to_retry.empty():
                        next_request = queue_of_requests_to_retry.get_nowait()
                        logging.debug(
                            f"Retrying request {next_request.task_id}: {next_request}"
                        )
                    elif file_not_finished:
                        try:
                            # get new request
                            messages = json.loads(next(requests))
                            next_request = APIRequest(
                                task_id=next(task_id_generator),
                                base_url=base_url,
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                token_consumption=num_tokens_consumed_from_request(
                                    messages,
                                    MODELS[model],
                                    token_encoding_name
                                ),
                                attempts_left=max_attempts,
                                metadata=None,
                            )
                            status_tracker.num_tasks_started += 1
                            status_tracker.num_tasks_in_progress += 1
                            logging.debug(
                                f"Reading request {next_request.task_id}: {next_request}"
                            )
                        except StopIteration:
                            # if file runs out, set flag to stop reading it
                            logging.debug("Read file exhausted")
                            file_not_finished = False

                # update available capacity
                current_time = time.time()
                seconds_since_update = current_time - last_update_time
                available_request_capacity = min(
                    available_request_capacity
                    + max_requests_per_minute * seconds_since_update / 60.0,
                    max_requests_per_minute,
                )
                available_token_capacity = min(
                    available_token_capacity
                    + max_tokens_per_minute * seconds_since_update / 60.0,
                    max_tokens_per_minute,
                )
                last_update_time = current_time

                # if enough capacity available, call API
                if next_request:
                    next_request_tokens = next_request.token_consumption
                    if (
                        available_request_capacity >= 1
                        and available_token_capacity >= next_request_tokens
                    ):
                        # update counters
                        available_request_capacity -= 1
                        available_token_capacity -= next_request_tokens
                        next_request.attempts_left -= 1

                        # call API
                        asyncio.create_task(
                            next_request.call_api(
                                session=session,
                                # request_url=request_url,
                                # request_header=request_header,
                                retry_queue=queue_of_requests_to_retry,
                                save_filepath=save_filepath,
                                status_tracker=status_tracker,
                            )
                        )
                        next_request = None  # reset next_request to empty

                # if all tasks are finished, break
                if status_tracker.num_tasks_in_progress == 0:
                    break

                # main loop sleeps briefly so concurrent tasks can run
                await asyncio.sleep(seconds_to_sleep_each_loop)

                # if a rate limit error was hit recently, pause to cool down
                seconds_since_rate_limit_error = (
                    time.time() - status_tracker.time_of_last_rate_limit_error
                )
                if (
                    seconds_since_rate_limit_error
                    < seconds_to_pause_after_rate_limit_error
                ):
                    remaining_seconds_to_pause = (
                        seconds_to_pause_after_rate_limit_error
                        - seconds_since_rate_limit_error
                    )
                    await asyncio.sleep(remaining_seconds_to_pause)
                    # ^e.g., if pause is 15 seconds and final limit was hit 5 seconds ago
                    logging.warn(
                        f"Pausing to cool down until {time.ctime(status_tracker.time_of_last_rate_limit_error + seconds_to_pause_after_rate_limit_error)}"
                    )

        # after finishing, log final status
        logging.info(
            f"""Parallel processing complete. Results saved to {save_filepath}"""
        )
        if status_tracker.num_tasks_failed > 0:
            logging.warning(
                f"{status_tracker.num_tasks_failed} / {status_tracker.num_tasks_started} requests failed. Errors logged to {save_filepath}."
            )
        if status_tracker.num_rate_limit_errors > 0:
            logging.warning(
                f"{status_tracker.num_rate_limit_errors} rate limit errors received. Consider running at a lower rate."
            )


@dataclass
class StatusTracker:
    """Stores metadata about the script's progress. Only one instance is created."""

    num_tasks_started: int = 0
    num_tasks_in_progress: int = 0  # script ends when this reaches 0
    num_tasks_succeeded: int = 0
    num_tasks_failed: int = 0
    num_rate_limit_errors: int = 0
    num_api_errors: int = 0  # excluding rate limit errors, counted above
    num_other_errors: int = 0
    time_of_last_rate_limit_error: int = 0  # used to cool off after hitting rate limits


@dataclass
class APIRequest:
    """Stores an API request's inputs, outputs, and other metadata. Contains a method to make an API call."""

    task_id: int
    base_url: str
    api_key: str
    model: str
    messages: dict
    token_consumption: int
    attempts_left: int
    metadata: dict
    result: list = field(default_factory=list)

    async def call_api(
        self,
        session: aiohttp.ClientSession,
        retry_queue: asyncio.Queue,
        save_filepath: str,
        status_tracker: StatusTracker,
    ):
        """Calls the OpenAI API and saves results."""
        logging.info(f"Starting request #{self.task_id}")
        error = None
        try:
            response = await run_model(session, self.messages, self.base_url, self.api_key, self.model)
            if "error" in response:
                logging.warning(
                    f"Request {self.task_id} failed with error {response['error']}"
                )
                status_tracker.num_api_errors += 1
                error = response
                if "Rate limit" in response["error"].get("message", ""):
                    status_tracker.time_of_last_rate_limit_error = time.time()
                    status_tracker.num_rate_limit_errors += 1
                    status_tracker.num_api_errors -= (
                        1  # rate limit errors are counted separately
                    )

        except (
            Exception
        ) as e:  # catching naked exceptions is bad practice, but in this case we'll log & save them
            logging.warning(f"Request {self.task_id} failed with Exception {e}")
            status_tracker.num_other_errors += 1
            error = e
        if error:
            self.result.append(error)
            if self.attempts_left:
                retry_queue.put_nowait(self)
            else:
                logging.error(
                    f"Request {self.task_id} failed after all attempts. Saving errors: {self.result}"
                )
                data = (
                    [self.task_id, [str(e) for e in self.result], self.metadata]
                    if self.metadata
                    else [self.task_id, [str(e) for e in self.result]]
                )
                append_to_jsonl(data, save_filepath)
                status_tracker.num_tasks_in_progress -= 1
                status_tracker.num_tasks_failed += 1
        else:
            content = decode_response(response, self.model)
            data = (
                [self.task_id, content, self.metadata]
                if self.metadata
                else [self.task_id, content]
            )
            append_to_jsonl(data, save_filepath)
            status_tracker.num_tasks_in_progress -= 1
            status_tracker.num_tasks_succeeded += 1
            logging.debug(f"Request {self.task_id} saved to {save_filepath}")


# functions
def append_to_jsonl(data, filename: str) -> None:
    """Append a json payload to the end of a jsonl file."""
    json_string = json.dumps(data)
    with open(filename, "a") as f:
        f.write(json_string + "\n")


def num_tokens_consumed_from_request(
    request_json: list,
    api_endpoint: str,
    token_encoding_name: str,
):
    """Count the number of tokens in the request. Only supports completion and embedding requests."""
    encoding = tiktoken.get_encoding(token_encoding_name)
    # if completions request, tokens = prompt + n * max_tokens
    if api_endpoint.endswith("completions"):
        max_tokens = 15 # request_json.get("max_tokens", 15)
        n = 1  # request_json.get("n", 1)
        completion_tokens = n * max_tokens

        # chat completions
        if api_endpoint.startswith("chat/"):
            num_tokens = 0
            for message in request_json:  # ["messages"]:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens -= 1  # role is always required and always 1 token
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens + completion_tokens
        # normal completions
        else:
            prompt = request_json["prompt"]
            if isinstance(prompt, str):  # single prompt
                prompt_tokens = len(encoding.encode(prompt))
                num_tokens = prompt_tokens + completion_tokens
                return num_tokens
            elif isinstance(prompt, list):  # multiple prompts
                prompt_tokens = sum([len(encoding.encode(p)) for p in prompt])
                num_tokens = prompt_tokens + completion_tokens * len(prompt)
                return num_tokens
            else:
                raise TypeError(
                    'Expecting either string or list of strings for "prompt" field in completion request'
                )
    # if embeddings request, tokens = input tokens
    elif api_endpoint == "embeddings":
        input = request_json  # ["input"]
        if isinstance(input, str):  # single input
            num_tokens = len(encoding.encode(input))
            return num_tokens
        elif isinstance(input, list):  # multiple inputs
            num_tokens = sum([len(encoding.encode(i)) for i in input])
            return num_tokens
        else:
            raise TypeError(
                'Expecting either string or list of strings for "inputs" field in embedding request'
            )
    # more logic needed to support other API calls (e.g., edits, inserts, DALL-E)
    else:
        raise NotImplementedError(
            f'API endpoint "{api_endpoint}" not implemented in this script'
        )


def task_id_generator_function():
    """Generate integers 0, 1, 2, and so on."""
    task_id = 0
    while True:
        yield task_id
        task_id += 1


@click.command()
@click.argument("input_filepath", type=str)
@click.argument("output_filepath", type=str, default="/Users/john/Desktop/LLM_Trust_Trust_Evaluation/llmeval/parallel/output_start.jsonl", required=False)
@click.option("--base_url", type=str, default="https://drchat.xyz")
@click.option("--api_key", type=str, default="sk-7AKI_8FfvamSDIDpRBfxsg")
@click.option("--model", type=str, default="gpt4-1106-preview")
@click.option("--max_requests_per_minute", type=int, default=720 * 0.5)
@click.option("--max_tokens_per_minute", type=int, default=300_000 * 0.5)
@click.option("--token_encoding_name", type=str, default="cl100k_base")
@click.option("--max_attempts", type=int, default=5)
@click.option("--logging_level", default=logging.INFO)
def cli(input_filepath,
        output_filepath,
        base_url,
        api_key,
        model,
        max_requests_per_minute,
        max_tokens_per_minute,
        token_encoding_name,
        max_attempts,
        logging_level):
    """This script processes in parallel a jsonl file that has each line of json input messages to LLM.
    It returns another jsonl file that stores each line of json output response from LLM.
    """
    max_requests_per_minute = min(max_requests_per_minute, 0.5 * request_capacities[model])
    max_tokens_per_minute = min(max_tokens_per_minute, 0.5 * token_capacities[model])
    if output_filepath is None:
        output_filepath = input_filepath.replace(".jsonl", "_results.jsonl")
    # empty the output file
    with open(output_filepath, 'w'):
        pass

    # run script
    asyncio.run(
        process_api_requests_from_file(
            input_filepath,
            save_filepath=output_filepath,
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_requests_per_minute=float(max_requests_per_minute),
            max_tokens_per_minute=float(max_tokens_per_minute),
            token_encoding_name=token_encoding_name,
            max_attempts=max_attempts,
            logging_level=int(logging_level),
        )
    )


# run script
if __name__ == "__main__":
    cli()

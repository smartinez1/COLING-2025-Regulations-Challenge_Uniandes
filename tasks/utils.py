import os
import asyncio
import aiohttp
from functools import wraps
from dotenv import load_dotenv


def async_retry(retries=4, backoff_factor=2.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            while attempts <= retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempts == retries:
                        raise Exception(f"Max retries reached. Last error: {e}")
                    attempts += 1
                    sleep_time = backoff_factor ** attempts
                    await asyncio.sleep(sleep_time)
        return wrapper
    return decorator


class OpenAIPromptHandler:
    def __init__(self, api_cost_per_1k_tokens: float = 0.000150):
        load_dotenv()
        self.api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        self.api_cost_per_1k_tokens = api_cost_per_1k_tokens
        self.headers = {
            "Authorization": f"Bearer {os.getenv('AZURE_OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }

    def construct_prompt(self, prompt_template: str, context: str) -> str:
        return prompt_template.format(context=context)

    def calculate_cost(self, token_count: int) -> float:
        return (token_count * self.api_cost_per_1k_tokens) / 1000

    @async_retry(retries=4, backoff_factor=2.0)
    async def send_prompt(self, prompt: str):
        url = f"{self.api_endpoint}/chat/completions"
        payload = {
            "model": self.deployment_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to send prompt: {response.status} {await response.text()}")

    async def send_prompts_async(self, tasks):
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses
import os
import asyncio
from functools import wraps
from dotenv import load_dotenv
from openai import AzureOpenAI
import concurrent.futures


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
        """
        Send the prepared prompt to the OpenAI API for generating abbreviations using futures.

        Args:
            prompt (str): The prompt text to send.

        Returns:
            dict: Response content from the OpenAI API with generated abbreviations.
        """
        
        deployment_name = self.deployment_name  # Use the class attribute
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Define a function to make the request synchronously
        def make_request():
            chat_completion_zero = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.0
            )
            return chat_completion_zero

        # Use ThreadPoolExecutor to run the request in a separate thread
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = loop.run_in_executor(executor, make_request)
            try:
                response = await future
                # Log the successful response for debugging
                print("Successfully received response:", response)
                return response
            except Exception as e:
                raise Exception(f"Failed to send prompt: {e}")

    async def send_prompts_async(self, tasks):
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses
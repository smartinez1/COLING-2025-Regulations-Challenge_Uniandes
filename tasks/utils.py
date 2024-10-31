import os
import asyncio
from dotenv import load_dotenv
from functools import wraps
from openai import AzureOpenAI
import concurrent.futures
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
                        logging.error(f"Max retries reached. Last error: {traceback.print_exc()}")
                        return None
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

    def construct_prompt(self, prompt_template: str, context: str) -> str:
        return prompt_template.format(context=context)

    def calculate_cost(self, responses:list, input_token_price:int, output_token_price:int) -> list:
        """
        Takes in a list of responses and calculates its cost using input/output token pricing 
        """
        def _calculate_individual_cost(response, input_token_price:int, output_token_price:int) -> tuple:
            usage = response.usage
            return (usage.prompt_tokens * input_token_price) + (usage.completion_tokens * output_token_price), usage.prompt_tokens + usage.completion_tokens
            
        costs = []
        for response in responses:
                costs.append(_calculate_individual_cost(response, input_token_price, output_token_price)) if response else costs.append(((None,None),None))
        return costs 
    
    @async_retry(retries=4, backoff_factor=2.0)
    async def send_prompt(self, prompt: str, system_prompt:str=None):
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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Define a function to make the request synchronously
        def make_request():
            chat_completion_zero = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=0.0
            )
            return chat_completion_zero

        # Use ThreadPoolExecutor to run the request in a separate thread
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = loop.run_in_executor(executor, make_request)
            try:
                response = await future
                return response
            except Exception as e:
                logging.error(f"Failed to send prompt: {traceback.print_exc()}")
                raise
            
    async def send_prompts_async(self, tasks):
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses
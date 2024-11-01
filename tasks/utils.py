import os
import asyncio
from dotenv import load_dotenv
from functools import wraps
from openai import AzureOpenAI
import concurrent.futures
import logging
import traceback
import pandas as pd
from tqdm import tqdm
import time
import random
import uuid

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
    def __init__(self):
        load_dotenv()
        self.api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )


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
                costs.append(_calculate_individual_cost(response, input_token_price, output_token_price)) if response else costs.append((None,None))
        return costs 
    

    def load_existing_data(self, results_dir:str):
        """
        Takes in a task directory and checks if any saved results are available
        """
        os.makedirs(results_dir, exist_ok=True)  # Ensure the directory exists
        existing_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
        return pd.concat([pd.read_csv(os.path.join(results_dir, f)) for f in existing_files], ignore_index=True) if existing_files else pd.DataFrame()

    
    @async_retry(retries=4, backoff_factor=2.0)
    async def send_prompt(self, prompt: str, system_prompt:str=None):
        """
        Send the prepared prompt to the OpenAI API for generating abbreviations using futures.

        Args:
            prompt (str): The prompt text to send.

        Returns:
            dict: Response content from the OpenAI API with generated abbreviations.
        """
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Define a function to make the request synchronously
        def make_request():
            chat_completion_zero = self.client.chat.completions.create(
                model=self.deployment_name,
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
    
    async def process_batch_task(self, batch_data:pd.DataFrame, task_prompt:str, system_prompt:str)-> tuple:
        """
        Takes in existing data and the current batch to check for new information. If it exists, it generates tasks and executes them.
        Returns a tuple containing the responses and costs
        """
        
        # List to store tasks for the current batch
        tasks = []
        # Create tasks for the current batch
        for content in batch_data['content']:
            prompt = self.construct_prompt(task_prompt, content)
            task = asyncio.create_task(self.send_prompt(prompt, system_prompt=system_prompt))
            tasks.append(task)

        # Wait for all tasks in the current batch to complete and calculate costs
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        costs = self.calculate_cost(responses=responses, input_token_price=0.15e-6, output_token_price=0.6e-6)

        return responses, costs
    
    async def execute_task(self, results_dir:str, data:pd.DataFrame, task:str,task_prompt:str, system_prompt:str = None, batch_size:int=20):
        """
        Takes in the integrity of documents and generates questions.
        """
        all_responses = []
        
        # # Load existing processed data if available
        processed_dir = os.path.join(results_dir, "processed")
        existing_data = self.load_existing_data(results_dir=processed_dir)
        all_responses.append(existing_data) # Append existing data 

        # Calculate the number of batches
        num_batches = (len(data) + batch_size - 1) // batch_size

        for i in tqdm(range(num_batches)):
            # Slice the DataFrame to get the current batch
            batch_data = data.iloc[i * batch_size:(i + 1) * batch_size]

            if not existing_data.empty:
                batch_data = batch_data[~batch_data['url'].isin(existing_data['url'])]
                if batch_data.empty:
                    logging.info("Batch data is empty after existing url verification, skipping batch...")
                    continue    
            
            responses, costs = await self.process_batch_task(batch_data, task_prompt, system_prompt)
            
            # Adapts response to schema 
            current_data = (batch_data[["url","source","content"]]
                            .assign(task=task)
                            .assign(total_tokens = [cost[1] for cost in costs])
                            .assign(generated_text = [response.choices[0].message.content for response in responses])
                            .assign(costs = [cost[0] for cost in costs])
                            )

            # Save and append data
            all_responses.append(current_data)
            current_data.to_csv(os.path.join(processed_dir,f"{uuid.uuid4().hex[:5]}.csv"),index=False)
            time.sleep(random.uniform(0.3,1.2))

        return all_responses
    

    def store_total_result(self, results:list[pd.DataFrame], store_dir:str, task_name:str) -> None:
        """
        Stores total results into a directory
        """
        total = pd.concat(results,ignore_index=True)
        total.to_csv(os.path.join(store_dir,f"{task_name}.csv"),index=False)
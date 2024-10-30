from utils import OpenAIPromptHandler
import pandas as pd
import asyncio
import time 
import random
import os


BASE_PROMPT = """
    Given the following text:
    ´´´
    {context}
    ´´´
    Generate question/answer pairs relevant to the text you observe. These questions must be formulated in a way such that:
    a. The question is focused on knowing more about open source software licensing and applications
    b. The question must have a financial regulatory intent
    c. The answer distills knowledge in a concise and factual manner in order to answer the question's intent.

    Return them in a numerated list following this format:
    ´´´
    1. <question> - <answer>
    2. <question> - <answer>
    .
    .
    .
    n. <question> - <answer>
    ´´´
    ONLY provide this list, nothing else, nothing extra.
"""

SYSTEM_PROMPT = "You are an accurate, articulate and knowledgeable in open source licensing knowledge for financial and business applications."

async def generate_osi_qa(data: pd.DataFrame, api_handler: OpenAIPromptHandler, results_dir: str, batch_size: int = 20):
    """
    Takes in the integrity of documents and generates questions.
    """
    all_responses = []

    # Load existing processed data if available
    processed_dir = os.path.join(results_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)  # Ensure the directory exists
    existing_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    existing_data = pd.concat([pd.read_csv(os.path.join(processed_dir, f)) for f in existing_files], ignore_index=True) if existing_files else pd.DataFrame()

    # Calculate the number of batches
    num_batches = (len(data) + batch_size - 1) // batch_size

    for i in range(num_batches):
        # Slice the DataFrame to get the current batch
        batch_data = data.iloc[i * batch_size:(i + 1) * batch_size]

        if not existing_data.empty:
            batch_data = batch_data[~batch_data['url'].isin(existing_data['url'])]
            if batch_data.empty:
                continue  # Skip to the next iteration if all data in the batch has been processed before
        
        # List to store tasks for the current batch
        tasks = []

        # Create tasks for the current batch
        for content in batch_data['content']:
            prompt = api_handler.construct_prompt(BASE_PROMPT, content)
            task = asyncio.create_task(api_handler.send_prompt(prompt, system_prompt=SYSTEM_PROMPT))
            tasks.append(task)

        # Wait for all tasks in the current batch to complete and calculate costs
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        costs = api_handler.calculate_cost(responses=responses, input_token_price=0.15e-6, output_token_price=0.6e-6)

        current_data = (batch_data[["url","source"]]
                        .assign(task="osi_qa")
                        .assign(total_tokens = [cost[1] for cost in costs])
                        .assign(generated_text = [response.choices[0].message.content for response in responses])
                        .assign(costs = [cost[0] for cost in costs])
                        )


        all_responses.extend(current_data)
        time.sleep(random.uniform(0.3,1.2))

    return all_responses


async def main():

    results_dir = "results/osi"
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    df = df[df.source == "OSI"].head(5)

    handler = OpenAIPromptHandler()
    qa = await generate_osi_qa(data=df, api_handler=handler, results_dir=results_dir, batch_size=20)

    breakpoint()
    


    
asyncio.run(main())




from utils import OpenAIPromptHandler
import pandas as pd
import asyncio
import time 
import random
import os
from tqdm import tqdm 
import uuid
import logging
from prompts import PROMPT_LINKS, SYSTEM_PROMPT_GENERAL
from sources import LINKS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def generate_abbrev(data: pd.DataFrame, api_handler: OpenAIPromptHandler, results_dir: str, batch_size: int = 20):
    """
    Takes in the integrity of documents and generates questions.
    """
    all_responses = []
    
    # # Load existing processed data if available
    processed_dir = os.path.join(results_dir, "processed")
    existing_data = api_handler.load_existing_data(results_dir=processed_dir)
    all_responses.append(existing_data) # Append existing data 

    # Calculate the number of batches
    num_batches = (len(data) + batch_size - 1) // batch_size

    for i in tqdm(range(num_batches)):
        # Slice the DataFrame to get the current batch
        batch_data = data.iloc[i * batch_size:(i + 1) * batch_size]
        responses, costs = await api_handler.process_batch_task(existing_data, batch_data, PROMPT_LINKS, SYSTEM_PROMPT_GENERAL)

        if not responses:
            continue ## If responses are empty, continue with the iteration
        
        breakpoint()
        current_data = (batch_data[["url","source","content"]]
                        .assign(task="links")
                        .assign(total_tokens = [cost[1] for cost in costs])
                        .assign(generated_text = [response.choices[0].message.content for response in responses])
                        .assign(costs = [cost[0] for cost in costs])
                        )

        # Save and append data
        all_responses.append(current_data)
        current_data.to_csv(os.path.join(processed_dir,f"{uuid.uuid4().hex[:5]}.csv"),index=False)
        time.sleep(random.uniform(0.3,1.2))

    return all_responses

async def main():
    out_path = "links.csv"
    results_dir = "results/links"
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    df = (df[df['source'].isin(ABBREV)]#.head(2)
          .reset_index(drop=True)
          .drop_duplicates(subset="url")
          )

    handler = OpenAIPromptHandler()
    abbrev = await generate_abbrev(data=df, api_handler=handler, results_dir=results_dir, batch_size=15)

    results_complete = pd.concat(abbrev, ignore_index=True)
    (results_complete
    .reset_index(drop=True)
    .to_csv(os.path.join(results_dir,f"{out_path}.csv"),index=False))

asyncio.run(main())

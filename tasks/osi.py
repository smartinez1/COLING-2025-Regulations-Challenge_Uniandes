from utils import OpenAIPromptHandler
import pandas as pd
import asyncio
import time 
import random
import os
from tqdm import tqdm
import uuid
import logging
from prompts import PROMPT_OSI_QA, SYSTEM_PROMPT_OSI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# BASE_PROMPT = """
#     Given the following text:
#     ´´´
#     {context}
#     ´´´
#     Generate question/answer pairs relevant to the text you observe. These questions must be formulated in a way such that:
#     a. The question is focused on knowing more about open source software licensing and applications
#     b. The question must have a financial regulatory intent
#     c. The answer distills knowledge in a concise and factual manner in order to answer the question's intent.

#     Return them in a numerated list following this format:
#     ´´´
#     1. <question> - <answer>
#     2. <question> - <answer>
#     .
#     .
#     .
#     n. <question> - <answer>
#     ´´´
#     ONLY provide this list, nothing else, nothing extra.
# """

# SYSTEM_PROMPT = "You are an accurate, articulate and knowledgeable in open source licensing knowledge for financial and business applications."

async def generate_osi_qa(data: pd.DataFrame, api_handler: OpenAIPromptHandler, results_dir: str, batch_size: int = 20):
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
        responses, costs = await api_handler.process_batch_task(existing_data, batch_data, PROMPT_OSI_QA, SYSTEM_PROMPT_OSI)

        if not responses:
            continue ## If responses are empty, continue with the iteration
        
        breakpoint()
        current_data = (batch_data[["url","source","content"]]
                        .assign(task="osi_qa")
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

    results_dir = "results/osi"
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    df = (df[df.source == "OSI"]
          .reset_index(drop=True)
          .drop_duplicates(subset="url")
          )

    handler = OpenAIPromptHandler()
    qa = await generate_osi_qa(data=df, api_handler=handler, results_dir=results_dir, batch_size=15)

    results_complete = pd.concat(qa,ignore_index=True)
    (results_complete
    .reset_index(drop=True)
    .to_csv(os.path.join(results_dir,"osi_qa.csv"),index=False))
    
asyncio.run(main())




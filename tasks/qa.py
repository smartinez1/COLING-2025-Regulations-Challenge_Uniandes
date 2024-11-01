import argparse
import asyncio
from utils import OpenAIPromptHandler
from prompts import PROMPT_OSI_QA, PROMPT_OSI_ABBREV, SYSTEM_PROMPT_OSI
import pandas as pd
import os

def store_total_result(results:list[pd.DataFrame], store_dir:str, task_name:str) -> None:
    """
    Stores total results into a directory
    """
    total = pd.concat(results,ignore_index=True)
    total.to_csv(os.path.join(store_dir,f"{task_name}.csv"),index=False)

async def osi_qa_task(handler: OpenAIPromptHandler):
    output_path = "results/osi_qa"
    task_name = output_path.split('/')[-1]
    data = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    data = data[data.source == "OSI"].head(30)  # Assuming you have a path for the CSV
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_OSI_QA,
                                         system_prompt=SYSTEM_PROMPT_OSI,
                                         batch_size=10)
    
    breakpoint()


async def osi_abbrev_task(handler: OpenAIPromptHandler):
    output_path = "results/osi_abbrev"
    task_name = output_path.split('/')[-1]
    data = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    data = data[data.source == "OSI"]  # Assuming you have a path for the CSV


    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_OSI_ABBREV,
                                         system_prompt=SYSTEM_PROMPT_OSI,
                                         batch_size=15)
    
    store_total_result(results,output_path, task_name)


async def main():
    parser = argparse.ArgumentParser(description="QA related tasks with OSI and another task")
    parser.add_argument("task", type=str, choices=["osi_qa", "osi_abbrev"], help="The task to execute: 'classif' for classification, 'cleaning' for data cleaning.")
    args = parser.parse_args()

    handler = OpenAIPromptHandler()
    if args.task == "osi_qa":
        await osi_qa_task(handler)
    elif args.task == "osi_abbrev":
        await osi_abbrev_task(handler)

if __name__ == "__main__":
    asyncio.run(main())
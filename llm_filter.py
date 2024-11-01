import argparse
import asyncio
from tasks.utils import OpenAIPromptHandler
from tasks.prompts import CLASSIF_PROMPT, CLASSIF_SYSTEM, CLEANING_PROMPT, CLEANING_SYSTEM
import pandas as pd

async def text_classif_task(handler: OpenAIPromptHandler):
    output_path = "results/classif"
    # data = pd.read_csv("recursive_data/total/total_cleanedv2.csv").sample(20)
    data = pd.read_csv("high_trash.csv")
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task="classif",
                                         task_prompt=CLASSIF_PROMPT,
                                         system_prompt=CLASSIF_SYSTEM,
                                         batch_size=10)
    
    breakpoint()


async def text_cleaning_task(handler: OpenAIPromptHandler):
    output_path = "results/cleaning"
    # data = pd.read_csv("recursive_data/total/total_cleanedv2.csv").sample(2)  # Assuming you have a path for the CSV
    data = pd.read_csv("high_trash.csv")
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task="cleaning",
                                         task_prompt=CLEANING_PROMPT,
                                         system_prompt=CLEANING_SYSTEM,
                                         batch_size=15)
    
    breakpoint()

async def main():
    parser = argparse.ArgumentParser(description="Execute text classification or cleaning tasks.")
    parser.add_argument("task", type=str, choices=["classif", "cleaning"], help="The task to execute: 'classif' for classification, 'cleaning' for data cleaning.")
    args = parser.parse_args()

    handler = OpenAIPromptHandler()
    if args.task == "classif":
        await text_classif_task(handler)
    elif args.task == "cleaning":
        await text_cleaning_task(handler)

if __name__ == "__main__":
    asyncio.run(main())
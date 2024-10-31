from utils import OpenAIPromptHandler, store_total_result
import pandas as pd
import asyncio
import time 
import random
import os
from tqdm import tqdm 
import uuid
import logging
import argparse
from prompts import PROMPT_ABBREV, PROMPT_DEFS, PROMPT_LINKS, SYSTEM_PROMPT_GENERAL
from sources import ABBREV, LINKS, DEFS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def abbrev_task(handler: OpenAIPromptHandler):
    output_path = "results/abbrev"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv").head(20)  # Assuming you have a path for the CSV
    data = df[df['source'].isin(ABBREV)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_ABBREV,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=10)
    handler.store_total_result(results, output_path, task_name)

async def definition_task(handler: OpenAIPromptHandler):
    output_path = "results/definitions"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv").head(20)  # Assuming you have a path for the CSV
    data = df[df['source'].isin(DEFS)]

    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_DEFS,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=15)
    handler.store_total_result(results, output_path, task_name)

async def links_task(handler: OpenAIPromptHandler):
    output_path = "results/links"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv").head(20)  # Assuming you have a path for the CSV
    data = df[df['source'].isin(LINKS)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_LINKS,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=15)
    

    handler.store_total_result(results, output_path, task_name)

async def main():
    parser = argparse.ArgumentParser(description="QA related tasks with OSI and another task")
    parser.add_argument("task", type=str, choices=["abbrev", "definitions", "links"], help="The task to execute: 'classif' for classification, 'cleaning' for data cleaning.")
    args = parser.parse_args()

    handler = OpenAIPromptHandler()
    if args.task == "abbrev":
        await abbrev_task(handler)
    elif args.task == "definitions":
        await definition_task(handler)
    elif args.task == "links":
        await definition_task(handler)

if __name__ == "__main__":
    asyncio.run(main())

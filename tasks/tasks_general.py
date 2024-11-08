from utils import OpenAIPromptHandler
import pandas as pd
import asyncio
from tqdm import tqdm 
import logging
import argparse
from prompts import PROMPT_ABBREV, PROMPT_DEFS, PROMPT_LINKS, SYSTEM_PROMPT_GENERAL, QA_SYSTEM, PROMPT_QA_TASK, CDM_SYSTEM, PROMPT_CDM_TASK, PROMPT_NER
from sources import ABBREV, LINKS, DEFS, QA_TASK, NER_TASK

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CLEAN_DATA = "results/cleaning/cleaning.csv"

async def abbrev_task(handler: OpenAIPromptHandler):
    output_path = "results/abbrev"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA)
    data = df[df['source'].isin(ABBREV)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_ABBREV,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=40)
    handler.store_total_result(results, output_path, task_name)

async def definition_task(handler: OpenAIPromptHandler):
    output_path = "results/definitions"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA)
    data = df[df['source'].isin(DEFS)]

    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_DEFS,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=30)
    handler.store_total_result(results, output_path, task_name)

async def links_task(handler: OpenAIPromptHandler):
    output_path = "results/links"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA)
    data = df[df['source'].isin(LINKS)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_LINKS,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=30)
    

    handler.store_total_result(results, output_path, task_name)

async def qa_task(handler: OpenAIPromptHandler):
    output_path = "results/qa_task"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA)
    data = df[df["source"].isin(QA_TASK)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_QA_TASK,
                                         system_prompt=QA_SYSTEM,
                                         batch_size=30)
    
    handler.store_total_result(results, output_path, task_name)


async def cdm_task(handler: OpenAIPromptHandler):
    output_path = "results/cdm_task"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA)
    data = df[df["source"].isin(["CDM"])]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_CDM_TASK,
                                         system_prompt=CDM_SYSTEM,
                                         batch_size=30)
    
    handler.store_total_result(results, output_path, task_name)

async def ner_task(handler: OpenAIPromptHandler):
    output_path = "results/ner_task"
    task_name = output_path.split('/')[-1]
    df = pd.read_csv(CLEAN_DATA) 
    data = df[df["source"].isin(NER_TASK)]
    results = await handler.execute_task(results_dir=output_path,
                                         data=data,
                                         task=task_name,
                                         task_prompt=PROMPT_NER,
                                         system_prompt=SYSTEM_PROMPT_GENERAL,
                                         batch_size=30)
    handler.store_total_result(results, output_path, task_name)


async def main():
    parser = argparse.ArgumentParser(description="QA related tasks with OSI and another task")
    parser.add_argument("task", type=str, choices=["abbrev", "definitions", "links","qa_task","cdm_task", "ner_task"], help="The task to execute: 'classif' for classification, 'cleaning' for data cleaning.")
    args = parser.parse_args()

    handler = OpenAIPromptHandler()
    if args.task == "abbrev":
        await abbrev_task(handler)
    elif args.task == "definitions":
        await definition_task(handler)
    elif args.task == "links":
        await links_task(handler)
    elif args.task == "qa_task":
        await qa_task(handler)
    elif args.task == "cdm_task":
        await cdm_task(handler)
    elif args.task == "ner_task":
        await ner_task(handler)

if __name__ == "__main__":
    asyncio.run(main())

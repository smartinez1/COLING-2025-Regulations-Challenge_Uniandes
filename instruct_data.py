import pandas as pd
import os
import re
import json
import argparse
from typing import Dict

# Define the path to the directory containing the data files
FOLDER_PATH = "results/allresults/"

def parse(raw_text: str) -> Dict[str, str]:
    """
    Parse the raw string output in <raw_text> into a dictionary.

    Args:
        raw_text (str): Raw output string containing raw text and their corresponding ´answer´.

    Returns:
        Dict[str, str]: A dictionary mapping abbreviations to their expanded versions.
    """
    abbs_dict = {}
    for line in raw_text.strip().split('\n'):
        if " - " in line:
            abbr, expanded = line.split(" - ", 1)
            abbr = abbr.split('.', 1)[-1].strip()  # Remove index and leading spaces
            abbs_dict[abbr] = expanded.strip()
    return abbs_dict

def save_json(data, file_name: str):
    """
    Save data to a JSON file.

    Args:
        data (Any): Data to be saved in JSON format.
        file_name (str): The name of the output JSON file.
    """
    output_file = os.path.join(FOLDER_PATH, file_name)
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to '{output_file}'.")

def process_link_retrieval():
    csv_file = os.path.join(FOLDER_PATH, "links.csv")
    df = pd.read_csv(csv_file)

    output_data = []
    law_pattern = r"^\d+\.\s*(.+)$"

    for _, row in df.iterrows():
        content, url = row['generated_text'], row['url']
        if pd.notna(content):
            laws = re.findall(law_pattern, content, re.MULTILINE)
            for law in laws:
                prompt = {
                    "instruction": "Provide a link for {} law.",
                    "input": law,
                    "output": f"{law}: {url}" if url else f"{law}: Not able to find a link for the law"
                }
                output_data.append(prompt)

    save_json(output_data, "link_retrieval_prompts.json")

def process_abbreviation_recognition(task_type: str):
    csv_file = os.path.join(FOLDER_PATH, f"{task_type}.csv")
    df = pd.read_csv(csv_file)

    abbreviation_dict = {}
    for _, row in df.iterrows():
        abbreviations = row['generated_text']
        if pd.notna(abbreviations) and abbreviations:
            abbreviation_dict.update(parse(abbreviations))

    output_data = [
        {
            "instruction": "Expand the following acronym into its full form: {}",
            "input": abbr,
            "output": expansion
        }
        for abbr, expansion in abbreviation_dict.items()
    ]

    save_json(output_data, f"{task_type}_recognition_prompts.json")

def process_task(instruction_prompt: str, csv_file_suffix: str):
    """
    Generalized function to process CSV files for various tasks.

    Args:
        instruction_prompt (str): Instruction template for each prompt, using '{}' as a placeholder for the term/question.
        csv_file_suffix (str): Suffix for the CSV file name to load (e.g., 'definitions' or 'qa').
    """
    csv_file = os.path.join(FOLDER_PATH, f"{csv_file_suffix}.csv")
    df = pd.read_csv(csv_file)

    result_dict = {}
    for _, row in df.iterrows():
        result = row['generated_text']
        if pd.notna(result) and result:
            result_dict.update(parse(result))

    output_data = [
        {
            "instruction": instruction_prompt,
            "input": term_or_question,
            "output": definition_or_answer
        }
        for term_or_question, definition_or_answer in result_dict.items()
    ]

    save_json(output_data, f"{csv_file_suffix}_prompts.json")

def cfa_data(output_file: str = "cfa_prompts.json"):
    df = pd.read_parquet("hf://datasets/ChanceFocus/flare-cfa/data/test-00000-of-00001-6e96e3a2bc65fdb8.parquet")
    # Reformatting the dataset into the desired JSON structure
    json_list = []
    for index, row in df.iterrows():
        formatted_entry = {
            "instruction": f"{row.query.split('Q:')[0]}",
            "input": f"{row.query.split('Q:')[1][:-8]}",
            "output": f"{row.answer}"
        }
        json_list.append(formatted_entry)

    save_json(json_list, output_file)

def xbrl_data(output_file: str = "xbrl_prompts.json"):
    df_xbrl = pd.read_json("hf://datasets/mirageco/XBRLBench/test.json")
    # Reformatting the dataset into the desired JSON structure
    json_list = []
    for index, row in df_xbrl.iterrows():
        formatted_entry = {
            "instruction": "Answer the question based on the xbrl.",
            "input": f"Context: {row.text}.\n  {row.query}",
            "output": f"{row.answer.split('Answer:')[-1]}"
        }
        json_list.append(formatted_entry)

    save_json(json_list, output_file)

def consolidate_json_files(output_file: str = "consolidated.json"):
    """
    Consolidates and deduplicates all JSON files in FOLDER_PATH into a single JSON file.
    Removes duplicate outputs for abbreviations and definitions tasks.

    Args:
        output_file (str): The name of the output consolidated JSON file.
    """
    all_data = []
    unique_prompts = {}  # Dictionary to store unique input-output pairs

    for file_name in os.listdir(FOLDER_PATH):
        if file_name.endswith("_prompts.json"):
            file_path = os.path.join(FOLDER_PATH, file_name)
            with open(file_path, "r") as f:
                file_data = json.load(f)
                
                for entry in file_data:
                    task_type = None
                    try:
                        if "Expand the following acronym" in entry["instruction"]:
                            task_type = "abbreviation"
                    except TypeError:
                        breakpoint()
                    
                    key = (entry["instruction"], entry["input"])  # Unique key for input-instruction pair
                    
                    # For abbreviations and definitions, keep only the first unique entry per input
                    if task_type=="abbreviation":
                        if key not in unique_prompts:
                            unique_prompts[key] = entry
                    else:
                        all_data.append(entry)  # Directly add other task entries

    # Add unique abbreviation and definition entries to the final data
    all_data.extend(unique_prompts.values())

    consolidated_file = os.path.join(FOLDER_PATH, output_file)
    with open(consolidated_file, "w") as f:
        json.dump(all_data, f, indent=4)
    print(f"Consolidated data saved to '{consolidated_file}'.")


if __name__ == "__main__":
    choices=['link', 'abbrev', 'abbrev_osi', 'definition', 
             'qa', 'qa_osi', 'cdm', 'cfa', 'xbrl', 'all']
    parser = argparse.ArgumentParser(description="Process CSV files for various tasks.")
    parser.add_argument(
        '--task', choices=choices,
        required=True, help="Task to run"
    )
    args = parser.parse_args()

    task_map = {
        'link': process_link_retrieval,
        'abbrev': lambda: process_abbreviation_recognition('abbrev'),
        'abbrev_osi': lambda: process_abbreviation_recognition('osi_abbrev'),
        'definition': lambda: process_task("Define the following term: {}", "definitions"),
        'qa': lambda: process_task("Provide a concise answer to the following question: {}", "qa_task"),
        'qa_osi': lambda: process_task("Provide a concise answer to the following question: {}", "osi_qa"),
        'cfa': lambda: cfa_data(),
        'xbrl': lambda: xbrl_data(),
        'cdm': lambda: process_task("Provide a concise answer to the following question related to Financial Industry Operating Network's (FINO) Common Domain Model (CDM): {}", "cdm_task")
    }
    if args.task!='all':
        task_map[args.task]()
    else:
        for choice in choices:
            if choice!='all':
                task_map[choice]() 
        consolidate_json_files()

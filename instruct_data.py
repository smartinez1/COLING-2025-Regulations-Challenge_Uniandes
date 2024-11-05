import pandas as pd
import os
import re
import json
import argparse

# Define the path to the directory containing the data files
folder_path = "results/allresults/"

def parse(resultado: str):
    """
    Parse the raw string output of abbreviations into a dictionary.

    Args:
        resultado (str): Raw output string containing abbreviations and their meanings.

    Returns:
        Dict[str, str]: A dictionary mapping abbreviations to their expanded versions.
    """
    lines = resultado.strip().split('\n')
    abbs_dict = {}
    
    for line in lines:
        if " - " in line:  # Check to find the abbreviation
            abbr, expanded = line.split(" - ", 1)
            # Remove any leading index (digits followed by a dot)
            abbr = abbr.split('.', 1)[-1].strip()  # Strip index and any leading spaces
            abbs_dict[abbr] = expanded.strip()

    return abbs_dict

# Function for Link Retrieval Task
def link_retrieval_task():
    csv_file = os.path.join(folder_path, "links.csv")
    output_data = []
    
    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Regular expression to match laws in numbered list format
    law_pattern = r"^\d+\.\s*(.+)$"

    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        content = row['generated_text']  # Assuming 'generated_text' contains the list of laws
        url = row['url']

        # Skip rows with missing content
        if pd.notna(content):
            # Find each law in the numbered list format
            laws = re.findall(law_pattern, content, re.MULTILINE)
            
            # Create prompts for each law
            for law in laws:
                prompt = {
                    "instruction": "Provide a link for {} law.",
                    "input": f"{law}",
                    "output": f"{law}: {url}" if url else f"{law}: Not able to find a link for the law"
                }
                output_data.append(prompt)

    # Save the results to a JSON file
    output_file = os.path.join(folder_path, "link_retrieval_prompts.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Link Retrieval Prompts have been created and saved to '{output_file}'.")

# Function for Abbreviation Recognition Task
def abbreviation_recognition_task(csv_):
    folder_path = "results/allresults/"
    if csv_ == 'abbrev':
        csv_file = os.path.join(folder_path, "abbrev.csv")
    elif csv_ == 'abbrev_osi':
        csv_file = os.path.join(folder_path, "osi_abbrev.csv")
    output_data = []
    abbreviation_dict = {}

    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Iterate over the rows of the DataFrame
    for _, row in df.iterrows():
        abbreviations = row['generated_text']  # Assuming 'content' contains the abbreviations and expansions

        # Skip rows with missing content
        if pd.notna(abbreviations) and abbreviations!="":
            # Use the parse_abbreviations function to extract abbreviation-expansion pairs
            abbreviations_in_content = parse(abbreviations)
            abbreviation_dict.update(abbreviations_in_content)

    # Create prompts in the JSON structure for each unique abbreviation
    for acronym, expansion in abbreviation_dict.items():
        prompt = {
            "instruction": "Expand the following acronym into its full form:{}",
            "input": f"{acronym}",
            "output": f"{expansion}"
        }
        output_data.append(prompt)

    # Save the results to a JSON file
    output_file = os.path.join(folder_path, f"{csv_}_recognition_prompts.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"Abbreviation Recognition Prompts have been created and saved to '{output_file}'.")

# Function for Abbreviation Recognition Task
def definitions_recognition_task():
    folder_path = "results/allresults/"
    csv_file = os.path.join(folder_path, "definitions.csv")
    output_data = []
    result_dict = {}

    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Iterate over the rows of the DataFrame
    for _, row in df.iterrows():
        result = row['generated_text']  # Assuming 'content' contains the abbreviations and expansions

        # Skip rows with missing content
        if pd.notna(result) and result!="":
            # Use the parse_abbreviations function to extract abbreviation-expansion pairs
            result_in_content = parse(result)
            result_dict.update(result_in_content)

    # Create prompts in the JSON structure for each unique abbreviation
    for result, answer in result_dict.items():
        prompt = {
            "instruction": "Define the following term:{}",
            "input": f"{result}",
            "output": f"{answer}"
        }
        output_data.append(prompt)

    # Save the results to a JSON file
    output_file = os.path.join(folder_path, "definitions_prompts.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"Abbreviation Recognition Prompts have been created and saved to '{output_file}'.")

# Function for Abbreviation Recognition Task
def qa_task(csv_):
    folder_path = "results/allresults/"
    if csv_ == 'qa':
        csv_file = os.path.join(folder_path, "qa_task.csv")
    elif csv_ == 'qa_osi':
        csv_file = os.path.join(folder_path, "osi_qa.csv")

    output_data = []
    result_dict = {}

    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Iterate over the rows of the DataFrame
    for _, row in df.iterrows():
        result = row['generated_text']  # Assuming 'content' contains the abbreviations and expansions

        # Skip rows with missing content
        if pd.notna(result) and result!="":
            # Use the parse_abbreviations function to extract abbreviation-expansion pairs
            result_in_content = parse(result)
            result_dict.update(result_in_content)

    # Create prompts in the JSON structure for each unique abbreviation
    for result, answer in result_dict.items():
        prompt = {
            "instruction": "Provide a concise answer to the following question {}: Answer:",
            "input": f"{result}",
            "output": f"{answer}"
        }
        output_data.append(prompt)

    # Save the results to a JSON file
    output_file = os.path.join(folder_path, f"{csv_}_prompts.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"Abbreviation Recognition Prompts have been created and saved to '{output_file}'.")


# Main function to parse arguments and run the selected task
def main():
    parser = argparse.ArgumentParser(description="Process CSV files for link retrieval or abbreviation recognition tasks.")
    parser.add_argument('--task', choices=['link', 'abbrev', 'abbrev_osi' ,'definition', "qa", "qa_osi"], required=True, help="Choose the task to run: 'link' for Link Retrieval Task or 'abbrev' for Abbreviation Recognition Task")
    args = parser.parse_args()

    if args.task == 'link':
        link_retrieval_task()
    elif args.task == 'abbrev' or args.task == 'abbrev_osi':
        abbreviation_recognition_task(args.task)
    elif args.task == 'definition':
        definitions_recognition_task()
    elif args.task == 'qa' or args.task == 'qa_osi':
        qa_task(args.task)

if __name__ == "__main__":
    main()

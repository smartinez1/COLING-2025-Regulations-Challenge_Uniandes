import os
import openai
from dotenv import load_dotenv
from openai import AzureOpenAI
from pydantic import BaseModel
from typing import List, Dict
import time
from pprint import pprint
import pandas as pd
import numpy as np
import json
from scraper_links import ABBREV

load_dotenv()

API_KEY_MINI = os.getenv("AZURE_OPENAI_API_KEY") 
API_BASE_GPMINI = os.getenv("AZURE_OPENAI_ENDPOINT")
API_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

class ContextWithAbbreviations(BaseModel):
    """
    Pydantic model to represent the context and its associated abbreviations.

    Attributes:
        text (str): The original text from which abbreviations are extracted.
        abbreviations (Dict[str, str]): A dictionary mapping abbreviations to their expanded versions.
    """
    text: str
    abbreviations: Dict[str, str]

def extract_abbreviations(context: str) -> List[str]:
    """
    Extracts abbreviations from a given context using the OpenAI API.

    This function constructs a prompt for the OpenAI model to identify and 
    extract abbreviations present in the provided context. It returns a 
    list of abbreviations as strings.

    Args:
        context (str): The text context from which to extract abbreviations.

    Returns:
        Dict[str, str]: A list of abbreviations and their corresponding expansion extracted from the context.
    """
    prompt_template = """
    Given the following text:
    ´´´
    {context}
    ´´´
    extract all abbreviations that appear along with their expanded versions.
    return them in a numerated list following this format
    ´´´
    1. <abbreaviation> - <expanded version>
    2. <abbreaviation> - <expanded version>
    .
    .
    .
    n. <abbreaviation> - <expanded version>
    ´´´
    ONLY provide this list, nothing else, nothing extra.
    """

    prompt = prompt_template.format(context=context)

    while True:
        try:
            full_result = send_prompt(prompt)
            result = full_result.choices[0].message.content
            abbreviations = parse_abbreviations(result)
            return abbreviations, full_result
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting before retrying...")
            time.sleep(60)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def send_prompt(prompt: str) -> str:
    """
    Send the prepared prompt to the OpenAI API for generating abbreviations.

    Args:
        prompt (str): The prompt text to send.
    
    Returns:
        str: Response content from the OpenAI API with generated abbreviations.
    """
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    chat_completion_zero = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.0
    )
    return chat_completion_zero

def parse_abbreviations(resultado: str) -> Dict[str, str]:
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

# Estimate the cost based on the token count of the first example and append it to the result #TODO generalize to other tasks
def estimate_cost_and_extract_abbreviations(context_text, api_cost_per_1k_tokens=0.000150):
    """
    Estimate the cost of processing all examples based on the first example's token usage
    and append the first result to the output.

    Args:
        context_text (str): Text content to be processed by the API.
        api_cost_per_1k_tokens (float): Cost per 1000 tokens, defaulted to $0.000150.

    Returns:
        tuple: (estimated cost, first_result_df) - The estimated cost and the DataFrame with the first result.
    """
    # Call the API once with the first context text to get token usage and first result (simulated here)
    result, full_result = extract_abbreviations(context_text)  # Adjusted function to return token count and result
    token_usage = full_result.usage.total_tokens # Assuming the structure includes 'usage'
    # Calculate estimated cost
    estimated_cost = token_usage * api_cost_per_1k_tokens / 1000
    # Extract the abbreviations from the first result to append to output
    return result, estimated_cost

if __name__ == "__main__":
    # Define file paths and parameters and load data
    df = pd.read_csv('recursive_data/total/total_cleaned.csv')
    csv_filename = 'generated_data/processed_abbreviations.csv'
    cost_limit = 0.5  # Set your cost limit in dollars, e.g., $0.05
    api_cost_per_1k_tokens = 0.000150  # API cost per 1000 tokens in dollars

    # Initialize or load the CSV file for abbreviation-expansion pairs
    if os.path.exists(csv_filename):
        processed_df = pd.read_csv(csv_filename)
        processed_urls = set(processed_df['url'].unique())  # Track already processed URLs
    else:
        processed_df = pd.DataFrame(columns=["url", "result", "cost"])
        processed_urls = set()

    # Filter the main DataFrame
    filtered_df = df[df['source'].isin(ABBREV)]

    if os.path.exists(csv_filename):
        processed_df = pd.read_csv(csv_filename)
        costs = processed_df['cost'].tolist()  # Load existing costs from the "cost" column
    else:
        costs = []  # Start with an empty list if the CSV doesn't exist

    # Process each row in the filtered DataFrame
    for ind, row in filtered_df.iterrows():
        source = row["source"]
        content_text = row["content"]
        url = row["url"]

        # Skip row if it has already been processed
        if url in processed_urls:
            print(f"URL {url} already processed")
            continue

        print(f"Processing URL: {url} from source {source}")

        # Extract abbreviations and get token usage and cost
        extracted_abbreviations, row_cost = estimate_cost_and_extract_abbreviations(content_text, api_cost_per_1k_tokens=api_cost_per_1k_tokens)
        costs.append(row_cost)
        cumulative_cost = np.sum(costs)
        average_cost = np.mean(costs)
        total_examples = len(filtered_df)

        print(f"Average cost per transaction: {average_cost}")
        # Check if cumulative cost exceeds the limit
        if cumulative_cost > cost_limit:
            print(f"WARNING: Cumulative cost ${cumulative_cost:.2f} exceeded the limit of ${cost_limit:.2f}. Stopping process.")
            break
        elif average_cost * total_examples > cost_limit:
            print(f"WARNING: Expected final cost estimation: ${average_cost * total_examples:.2f} exceeding the limit of ${cost_limit:.2f}. The process may stop before finishing.")
        # Append extracted abbreviations with the URL to processed_df, avoiding duplicates
        new_entries = pd.DataFrame({
            'url': [url],  # Make sure to pass a list
            'result': [json.dumps(extracted_abbreviations)],
            'cost': [row_cost]
        })
        processed_df = pd.concat([processed_df, new_entries])
        # Save to CSV after processing each row
        new_entries.to_csv(csv_filename, mode='a', header=not os.path.exists(csv_filename), index=False)

        # Mark this URL as processed
        processed_urls.add(url)

        print("Extracted abbreviations:")
        pprint(extracted_abbreviations)

    print("All abbreviations processed and saved (or stopped due to cost limit).")

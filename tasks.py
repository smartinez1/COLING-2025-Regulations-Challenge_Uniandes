import os
import random
import openai
import re
from dotenv import load_dotenv
from openai import AzureOpenAI
from pydantic import BaseModel, ValidationError
from typing import List, Dict
import time
from pprint import pprint
import pandas as pd

load_dotenv()
# Placeholder values for API key and endpoint
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
            resultado = send_prompt(prompt)
            abbreviations = parse_abbreviations(resultado)
            return abbreviations
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
    return chat_completion_zero.choices[0].message.content

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

if __name__ == "__main__":
    # Reading CSV and creating the context with abbreviations
    csv_filename = 'recursive_data/total/total_cleaned.csv'
    df = pd.read_csv(csv_filename)
    ind = 1000
    context_text = df.iloc[ind]["content"]

    print("Source:")
    print(df.iloc[ind]["source"])

    # Extract abbreviations using the OpenAI model
    extracted_abbreviations = extract_abbreviations(context_text)

    pprint(extracted_abbreviations)

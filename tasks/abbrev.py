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
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from the correct module
from scraper_links import ABBREV
from utils import OpenAIPromptHandler

from typing import Dict
import asyncio

class OpenAIAbbreviationExtractor(OpenAIPromptHandler):
    async def extract_abbreviations(self, context: str) -> Dict[str, str]:
        """
        Extracts abbreviations from a given context using the OpenAI API.

        This method constructs a prompt for the OpenAI model to identify and 
        extract abbreviations present in the provided context. It returns a 
        dictionary of abbreviations and their corresponding expansions.

        Args:
            context (str): The text context from which to extract abbreviations.

        Returns:
            Dict[str, str]: A dictionary of abbreviations and their expansions.
        """
        prompt_template = """
        Given the following text:
        ```
        {context}
        ```
        extract all abbreviations that appear along with their expanded versions.
        return them in a numerated list following this format:
        ```
        1. <abbreviation> - <expanded version>
        2. <abbreviation> - <expanded version>
        ...
        ```
        ONLY provide this list, nothing else.
        """

        # Construct the prompt using the method from the parent class
        prompt = self.construct_prompt(prompt_template, context)

        try:
            # Send the prompt using the parent's send_prompt method
            full_result = await self.send_prompt(prompt)
            result = full_result.__dict__['choices'][0].__dict__['message'].__dict__['content']
            abbreviations = self.parse_abbreviations(result)
            return abbreviations
        except Exception as e:
            print(f"An error occurred while extracting abbreviations: {e}")
            return {}

    def parse_abbreviations(self, response_text: str) -> Dict[str, str]:
        """
        Parses the list of abbreviations and expansions from the response text.

        Args:
            response_text (str): The raw text response from the OpenAI API.

        Returns:
            Dict[str, str]: A dictionary where keys are abbreviations and values are their expansions.
        """
        abbreviations = {}
        for line in response_text.strip().splitlines():
            if ". " in line:
                _, pair = line.split(". ", 1)
                abbr, expansion = map(str.strip, pair.split(" - ", 1))
                abbreviations[abbr] = expansion
        return abbreviations

async def main():
    # File and data configurations
    df = pd.read_csv('recursive_data/total/total_cleanedv2.csv')
    csv_filename = 'generated_data/processed_abbreviations.csv'
    cost_limit = 5.0  # Set in dollars
    api_cost_per_1k_tokens = 0.0006

    # Source, link, task, num_tokens, generated, cost
    # Load or initialize processed data
    if os.path.exists(csv_filename):
        processed_df = pd.read_csv(csv_filename)
        processed_urls = set(processed_df['url'].unique())
    else:
        processed_df = pd.DataFrame(columns=["source", "link", "task", "num_tokens", "generated", "cost"])
        processed_urls = set()

    # Filter the DataFrame for relevant sources
    filtered_df = df[df['source'].isin(ABBREV)]

    # Initialize the extractor
    extractor = OpenAIAbbreviationExtractor(api_cost_per_1k_tokens=api_cost_per_1k_tokens)
    total_costs = processed_df['cost'].tolist() if 'cost' in processed_df.columns else []

    for ind, row in filtered_df.iterrows():
        url = row["url"]
        content_text = row["content"]

        # Skip if already processed
        if url in processed_urls:
            print(f"URL {url} already processed")
            continue

        print(f"Processing URL: {url}")

        # Extract abbreviations asynchronously and calculate cost
        extracted_abbreviations = await extractor.extract_abbreviations(content_text)
        row_cost = extractor.calculate_cost([extracted_abbreviations], 0.15e-6, 0.6e-6)  # Adjust token pricing if necessary
        total_costs.append(row_cost[0][0])

        # Calculate cumulative cost
        cumulative_cost = np.sum(total_costs)
        average_cost = np.mean(total_costs)

        # Check cost thresholds
        if cumulative_cost > cost_limit:
            print(f"Exceeded cost limit: ${cumulative_cost:.2f} (limit: ${cost_limit:.2f}). Stopping.")
            break

        # Source, link, task, num_tokens, generated, cost
        # Append new data to the DataFrame
        processed_df = pd.concat([processed_df, pd.DataFrame({
            'source':[filtered_df["source"]],
            'link': [url],  
            'task': "ABBREVIATION",
            'num_tokens': 
            'result': [json.dumps(extracted_abbreviations)],
            'cost': [row_cost[0][0]]
        })], ignore_index=True)

    # Save results to CSV
    processed_df.to_csv(csv_filename, index=False)
    print("Completed processing and saved results.")

# Run the main asynchronous function
if __name__ == "__main__":
    asyncio.run(main())

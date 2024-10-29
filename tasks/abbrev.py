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
            result = full_result['choices'][0]['message']['content']
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
    # Define file paths, parameters, and load data
    df = pd.read_csv('recursive_data/total/total_cleanedv2.csv')
    csv_filename = 'generated_data/processed_abbreviations.csv'
    cost_limit = 0.5  # Set your cost limit in dollars, e.g., $0.05
    api_cost_per_1k_tokens = 0.0006  # API cost per 1000 tokens in dollars

    # Initialize or load the CSV file for abbreviation-expansion pairs
    if os.path.exists(csv_filename):
        processed_df = pd.read_csv(csv_filename)
        processed_urls = set(processed_df['url'].unique())  # Track already processed URLs
    else:
        processed_df = pd.DataFrame(columns=["url", "result", "cost"])
        processed_urls = set()

    # Filter the main DataFrame
    filtered_df = df[df['source'].isin(ABBREV)]

    # Initialize the abbreviation extractor
    extractor = OpenAIAbbreviationExtractor(api_cost_per_1k_tokens=api_cost_per_1k_tokens)

    # Process each row in the filtered DataFrame
    costs = processed_df['cost'].tolist() if 'cost' in processed_df.columns else []
    for ind, row in filtered_df.iterrows():
        source = row["source"]
        content_text = row["content"]
        url = row["url"]

        # Skip row if it has already been processed
        if url in processed_urls:
            print(f"URL {url} already processed")
            continue

        print(f"Processing URL: {url} from source {source}")

        # Extract abbreviations asynchronously
        extracted_abbreviations = await extractor.extract_abbreviations(content_text)
        row_cost = extractor.calculate_cost(len(content_text))  # Adjust token count if needed
        costs.append(row_cost)
        cumulative_cost = np.sum(costs)
        average_cost = np.mean(costs)
        total_examples = len(filtered_df)

        print(f"Average cost per transaction: {average_cost:.4f}")

        # Check if cumulative cost exceeds the limit
        if cumulative_cost > cost_limit:
            print(f"WARNING: Cumulative cost ${cumulative_cost:.2f} exceeded the limit of ${cost_limit:.2f}. Stopping process.")
            break
        elif average_cost * total_examples > cost_limit:
            print(f"WARNING: Expected final cost estimation: ${average_cost * total_examples:.2f} exceeding the limit of ${cost_limit:.2f}. The process may stop before finishing.")

        # Append extracted abbreviations with the URL to processed_df
        new_entries = pd.DataFrame({
            'url': [url],  
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

# Entry point
if __name__ == "__main__":
    asyncio.run(main())

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from urllib.parse import urljoin
import logging
import time
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# The main webpage URL
url = "https://www.fdic.gov/federal-deposit-insurance-act"  

# Simulate a browser user-agent to avoid 403 error
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_filename_from_url(url):
    # Remove protocol (http:// or https://) and get the main domain
    domain = url.split("//")[-1].split("/")[0]  
    # Extract the part between "www." and ".com/.gov/.edu/etc."
    base_name = domain.split('.')[1] if domain.startswith("www.") else domain.split('.')[0]
    # Construct the CSV file name using the extracted base name
    filename = f"scraped_{base_name}_content.csv"
    return filename

# Function to scrape content from a given URL
def scrape_link_content(link, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(link, headers=headers, timeout=10)  # Set a timeout for the request
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_text = soup.get_text(separator=" ", strip=True)
                return page_text
            else:
                logging.warning(f"Failed to access {link}: Status code {response.status_code}")
        except Exception as e:
            logging.error(f"Error scraping {link}: {e}")
            time.sleep(2)  # Wait for 2 seconds before retrying

    logging.error(f"Max retries reached for {link}")
    return None

# Function to scrape links from the main page based on multiple conditions
def scrape_links_from_main_page(url, link_conditions=["regulations", "accounting", "auditing"]):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"Failed to access main page {url}: Status code {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        # Loop through all anchor tags with href attributes
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Check if any condition in the list matches the href
            if any(condition in href.lower() for condition in link_conditions):  # Convert href to lowercase to ensure case-insensitive match
                full_link = urljoin(url, href)  # Use urljoin to properly handle relative URLs
                links.append(full_link)

        logging.info(f"Found {len(links)} links that match one of the conditions: {link_conditions}")
        return links

    except Exception as e:
        logging.error(f"Error scraping main page {url}: {e}")
        return []

# Main scraping process
def main():
    # Scraping links from the main page
    links = scrape_links_from_main_page(url)

    if not links:
        logging.warning("No links found matching the given condition.")
        return

    # Structure to save the scraped data
    scraped_data = []

    # Scrape content from each link
    for link in tqdm(links, desc="Scraping Links"):
        logging.info(f"Scraping content from: {link}")
        content = scrape_link_content(link)
        if content:
            scraped_data.append({'link': link, 'content': content})
        else:
            logging.warning(f"No content found or an error occurred for: {link}")

    # Save the scraped data to CSV
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        csv_filename = get_filename_from_url(url)
        df.to_csv(csv_filename, index=False)
        logging.info(f"Scraping completed and data saved to {csv_filename}.csv")
    else:
        logging.warning("Scraping finished, but no content to save.")

if __name__ == "__main__":
    main()

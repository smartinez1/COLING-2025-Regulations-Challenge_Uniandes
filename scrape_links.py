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

# List of URLs to process
QA_urls = [
    "https://www.sec.gov/",
    "https://www.federalreserve.gov/",
    "https://www.fdic.gov/federal-deposit-insurance-act",
    "https://www.iii.org/publications/insurance-handbook/regulatory-and-financial-environment/",
    "https://files.fasab.gov/pdffiles/2023_FASAB_Handbook.pdf",
    "https://www.in.gov/sboa/about-us/sboa-glossary-of-accounting-and-audit-terms/"
]

LR_urls = [
    "https://eur-lex.europa.eu/oj/daily-view/L-series/default.html?ojDate=10102024",
    "https://www.esma.europa.eu/",
    "https://www.sec.gov/rules-regulations",
    "https://www.ecfr.gov/",
    "https://www.fdic.gov/laws-and-regulations/fdic-law-regulations-related-acts",
    "https://www.federalreserve.gov/supervisionreg/reglisting.htm"
]

# Simulate a browser user-agent to avoid 403 error
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_filename_from_url(url):
    """Helper function to create a safe filename from a URL"""
    return url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '')

# Function to create a directory if it doesn't exist
def create_directory(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        logging.info(f"Created directory: {folder_name}")
    else:
        logging.info(f"Directory already exists: {folder_name}")

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

# Function to log URLs that produced no results into a file
def log_failed_urls(failed_urls, folder_name="logs", log_file_name="failed_urls.txt"):
    create_directory(folder_name)  # Ensure the log folder exists
    log_file_path = os.path.join(folder_name, log_file_name)
    
    with open(log_file_path, 'w') as log_file:
        log_file.write("Links that produced no results:\n")
        log_file.write("=" * 50 + "\n")
        for url, reason in failed_urls:
            log_file.write(f"URL: {url}\nReason: {reason}\n\n")
    
    logging.info(f"Logged failed URLs to {log_file_path}")

# Main scraping process
def main():
    # List to store URLs that produced no results
    failed_urls = []

    # Process QA URLs
    failed_urls.extend(process_urls(QA_urls, "QA"))
    
    # Process LR URLs
    failed_urls.extend(process_urls(LR_urls, "LR"))
    
    # Log the failed URLs to a file if there are any
    if failed_urls:
        log_failed_urls(failed_urls)

# Helper function to process a list of URLs and save scraped data in the corresponding folder
def process_urls(urls, directory):
    failed_urls = []

    # Create the directory for the URL type if it doesn't exist
    create_directory(directory)
    
    for url in urls:
        # Create a CSV filename based on the URL
        csv_filename = os.path.join(directory, f"scraped_{get_filename_from_url(url)}.csv")
        
        # Check if the CSV already exists
        if os.path.exists(csv_filename):
            print(f"Skipping {url}, CSV already exists.")
            continue

        try:
            # Use scrape_link_content to scrape the page content
            page_content = scrape_link_content(url)
            if page_content:
                df = pd.DataFrame({"content": [page_content]})
            
                # Save the scraped data to CSV, with escapechar to handle special characters
                df.to_csv(csv_filename, index=False, escapechar='\\')
                print(f"Scraping completed for {url} and data saved to {csv_filename}.")
            else:
                raise Exception("No content found.")
        
        except Exception as e:
            print(f"Failed to process {url}: {str(e)}")
            failed_urls.append((url, str(e)))
    
    return failed_urls

if __name__ == "__main__":
    main()

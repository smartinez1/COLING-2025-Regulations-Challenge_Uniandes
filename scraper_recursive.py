import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from urllib.parse import urljoin
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define QA and LR URLs
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

# Keywords to look for in the page content
keywords = ["regulation", "financial", "insurance", "deposit", "law", "act"]  # Add more keywords as needed

# Simulate a browser user-agent to avoid 403 error
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Function to create a directory if it doesn't exist
def create_directory(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        logging.info(f"Created directory: {folder_name}")

# Function to scrape content from a given URL
def scrape_link_content(link, non_working_links):
    try:
        response = requests.get(link, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=" ", strip=True)
            return page_text
        else:
            logging.warning(f"Failed to access {link}: Status code {response.status_code}")
            non_working_links.append(link)  # Add to non-working links
            return None
    except Exception as e:
        logging.error(f"Error scraping {link}: {e}")
        non_working_links.append(link)  # Add to non-working links
        return None

# Function to check if any keywords are present in the text
def contains_keywords(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

# Function to scrape links from a page recursively
def scrape_links_from_page(url, depth, max_depth, visited, base_directory, non_working_links):
    if depth > max_depth or url in visited:
        return  # Stop if maximum depth reached or URL already visited

    visited.add(url)  # Mark this URL as visited
    logging.info(f"Scraping {url} at depth {depth}")

    # Create a subdirectory for the current depth
    depth_directory = os.path.join(base_directory, f"depth_{depth}")
    create_directory(depth_directory)

    # Scrape content from the current page
    page_content = scrape_link_content(url, non_working_links)  # Pass non_working_links
    if page_content and contains_keywords(page_content, keywords):
        # Define CSV filename
        csv_filename = os.path.join(depth_directory, f"page_{len(os.listdir(depth_directory)) + 1}.csv")

        # Check if the CSV file already exists
        if not os.path.exists(csv_filename):
            df = pd.DataFrame({"url": [url], "content": [page_content]})
            df.to_csv(csv_filename, mode='a', index=False, header=True)
            logging.info(f"Saved content from {url} to {csv_filename}")
        else:
            logging.info(f"Content from {url} already saved in {csv_filename}, skipping.")

    # Extract links from the current page to scrape recursively
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Loop through all anchor tags with href attributes
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_link = urljoin(url, href)  # Use urljoin to handle relative URLs

            # Recur for the new link
            scrape_links_from_page(full_link, depth + 1, max_depth, visited, base_directory, non_working_links)

    except Exception as e:
        logging.error(f"Error extracting links from {url}: {e}")

# Main function to start the recursive scraping
def main(start_urls, directory, max_depth=2):
    base_directory = f"recursive_data/{directory}"  # Base directory for this type of URLs
    create_directory("recursive_data")  # Create the main recursive data directory
    create_directory(base_directory)  # Create the subdirectory for the URL type
    visited = set()  # Keep track of visited URLs
    non_working_links = []  # List to store non-working links

    for url in start_urls:
        scrape_links_from_page(url, 0, max_depth, visited, base_directory, non_working_links)

    # Save non-working links to a CSV after scraping
    if non_working_links:
        df_non_working = pd.DataFrame(non_working_links, columns=["non_working_links"])
        df_non_working.to_csv(os.path.join(base_directory, "non_working_links.csv"), index=False)
        logging.info(f"Saved non-working links to {os.path.join(base_directory, 'non_working_links.csv')}")

if __name__ == "__main__":
    # Starting URLs
    main(QA_urls, directory="QA", max_depth=2)  # Scrape QA URLs
    main(LR_urls, directory="LR", max_depth=2)  # Scrape LR URLs

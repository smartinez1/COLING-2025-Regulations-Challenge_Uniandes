import os
import time
import logging
import pandas as pd
from tqdm import tqdm
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

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

# List of banned domains
banned_domains = [
    "facebook.com", "twitter.com", "youtube.com", "instagram.com",
    "linkedin.com", "t.co", "x.com", "pinterest.com", "reddit.com", "flickr.com",
    "threads.net"
]

# Keywords to look for in the page content
keywords = ["regulation", "financial", "insurance", "deposit", "law", "act"]

# Function to generate a safe filename based on the URL type
def generate_csv_filename(url_type):
    return f"{url_type}.csv"

# Decorator for exponential backoff
def retry_with_exponential_backoff(max_attempts=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, WebDriverException) as e:
                    attempts += 1
                    wait_time = 2 ** attempts  # Exponential backoff
                    logging.warning(f"Error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            logging.error(f"Max attempts reached for {func.__name__}.")
            return None
        return wrapper
    return decorator

# Function to initialize Selenium WebDriver
def init_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service('path/to/chromedriver')  # Replace with your chromedriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

# Function to scrape content from a given URL using Selenium
@retry_with_exponential_backoff(max_attempts=5)
def scrape_link_content(link):
    driver = init_webdriver()
    try:
        driver.get(link)
        time.sleep(2)  # Allow time for the page to load
        page_text = driver.find_element("tag name", "body").text
        return page_text, None  # Return page text and None for no error
    except Exception as e:
        return None, str(e)  # Return None for content and error message
    finally:
        driver.quit()  # Close the browser

# Function to check if any keywords are present in the text
def contains_keywords(text):
    return any(keyword.lower() in text.lower() for keyword in keywords)

# Function to check if a domain is banned
def is_banned_domain(domain):
    return any(banned_domain in domain for banned_domain in banned_domains)

# Function to append data to the CSV or update existing entries
def update_csv(csv_filename, url, page_content):
    if os.path.exists(csv_filename):
        try:
            df = pd.read_csv(csv_filename, encoding='utf-8', on_bad_lines='skip', engine='python')
        except Exception as e:
            logging.error(f"Error reading {csv_filename}: {e}")
            return
    else:
        df = pd.DataFrame(columns=["url", "content"])

    new_row = pd.DataFrame({"url": [url], "content": [page_content]})
    df = pd.concat([df, new_row], ignore_index=True)

    try:
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logging.info(f"Updated {csv_filename} successfully.")
    except Exception as e:
        logging.error(f"Error updating {csv_filename}: {e}")

# Function to scrape links from a page recursively with depth control
def scrape_links_from_page(url, visited, csv_filename, non_working_links, max_depth, current_depth=0):
    if url in visited or current_depth > max_depth:
        return

    visited.add(url)
    logging.info(f"Scraping {url} at depth {current_depth}")

    page_content, error = scrape_link_content(url)

    if error:
        non_working_links.append((url, error))
        return

    if page_content and contains_keywords(page_content):
        update_csv(csv_filename, url, page_content)

    try:
        driver = init_webdriver()
        driver.get(url)
        time.sleep(2)  # Allow time for the page to load
        links = driver.find_elements("tag name", "a")
        
        for a in links:
            href = a.get_attribute('href')
            if href:
                full_link = urljoin(url, href)
                full_link_domain = get_root_domain(full_link)

                if is_banned_domain(full_link_domain):
                    logging.info(f"Skipping {full_link} (banned domain)")
                    continue

                scrape_links_from_page(full_link, visited, csv_filename, non_working_links, max_depth, current_depth + 1)
    except Exception as e:
        logging.error(f"Error extracting links from {url}: {e}")
    finally:
        driver.quit()  # Close the browser

# Function to scrape links in parallel
def parallel_scrape(start_urls, directory, max_depth):
    base_directory = f"recursive_data/{directory}"
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    visited = set()
    non_working_links = []
    csv_filename = os.path.join(base_directory, generate_csv_filename(directory))

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scrape_links_from_page, url, visited, csv_filename, non_working_links, max_depth): url for url in start_urls}
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in scraping task: {e}")

    if non_working_links:
        df_non_working = pd.DataFrame(non_working_links, columns=["url", "error_reason"])
        df_non_working.to_csv(os.path.join(base_directory, "non_working_links.csv"), index=False)
        logging.info(f"Saved non-working links to {os.path.join(base_directory, 'non_working_links.csv')}")

# Main function to start the recursive scraping
def main(start_urls, directory, max_depth=2):
    parallel_scrape(start_urls, directory, max_depth)

if __name__ == "__main__":
    max_depth = 3
    main(QA_urls, directory="QA", max_depth=max_depth)  # Scrape QA URLs
    main(LR_urls, directory="LR", max_depth=max_depth)  # Scrape LR URLs

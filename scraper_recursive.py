
import PyPDF2
import docx
import io

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
from scraper_links import BANNED_DOMAINS, SCRAP_LINKS
import traceback
import threading

lock = threading.Lock()
batch_lock = threading.Lock()
batch_data = []
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Keywords to look for in the page content
keywords = ["regulation", "financial", "insurance", "deposit", "law", "act"]
# Batching settings
BATCH_SIZE = 10 
batch_writing_in_progress = False 

# Define QA and LR URLs
# QA_urls = [
#     "https://www.sec.gov/",
#     "https://www.federalreserve.gov/",
#     "https://www.fdic.gov/federal-deposit-insurance-act",
#     "https://www.iii.org/publications/insurance-handbook/regulatory-and-financial-environment/",
#     "https://files.fasab.gov/pdffiles/2023_FASAB_Handbook.pdf",
#     "https://www.in.gov/sboa/about-us/sboa-glossary-of-accounting-and-audit-terms/"
# ]

# LR_urls = [
#     "https://eur-lex.europa.eu/oj/daily-view/L-series/default.html?ojDate=10102024",
#     "https://www.esma.europa.eu/",
#     "https://www.sec.gov/rules-regulations",
#     "https://www.ecfr.gov/",
#     "https://www.fdic.gov/laws-and-regulations/fdic-law-regulations-related-acts",
#     "https://www.federalreserve.gov/supervisionreg/reglisting.htm"
# ]

# Function to download and extract content from PDFs and DOCX files
def download_and_extract_file(link, download_dir="downloads"):
    try:
        # Make sure the download directory exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Get the file extension to identify the file type
        response = requests.get(link)
        filename = link.split("/")[-1]
        file_path = os.path.join(download_dir, filename)
        
        # Save the file locally
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Extract text based on the file type
        if filename.lower().endswith(".pdf"):
            return extract_text_from_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            return extract_text_from_docx(file_path)
        else:
            logging.info(f"Unsupported file type: {filename}")
            return None
    except Exception as e:
        logging.error(f"Failed to download or extract file {link}: {e}")
        return None

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text += page.extractText()
    except Exception as e:
        logging.error(f"Error extracting text from PDF {pdf_path}: {e}")
    return text

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_path):
    text = ""
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from DOCX {docx_path}: {e}")
    return text

# Function to generate a safe filename based on the URL type
def generate_csv_filename(url_type):
    return f"{url_type}.csv"


def get_root_domain(url):
    """
    Extract the root domain from a URL.

    Args:
        url (str): The URL from which to extract the root domain.

    Returns:
        str: The root domain of the URL.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        root_domain = domain.split('.')[-2] + '.' + domain.split('.')[-1]  # Extracts the last two parts of the domain
        return root_domain
    except Exception as e:
        logging.error(f"Error extracting root domain from {url}: {e}")
        return None

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
    
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver

# Function to scrape content from a given URL using Selenium
@retry_with_exponential_backoff(max_attempts=5)
def scrape_link_content(link):
    try:
        driver = init_webdriver()
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
    return any(banned_domain in domain for banned_domain in BANNED_DOMAINS)

# Function to append data to the CSV or update existing entries
def update_csv(csv_filename, url, source, page_content):
    # Locking the block to prevent simultaneous writes
    with lock:
        if os.path.exists(csv_filename):
            try:
                df = pd.read_csv(csv_filename, encoding='utf-8', on_bad_lines='skip', engine='python')
            except Exception as e:
                logging.error(f"Error reading {csv_filename}: {e}")
                return
        else:
            df = pd.DataFrame(columns=["url", "source","content"])

        new_row = pd.DataFrame({"url": [url], "source": [source], "content": [page_content]})
        df = pd.concat([df, new_row], ignore_index=True)

        try:
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            logging.info(f"Updated {csv_filename} successfully.")
        except Exception as e:
            logging.error(f"Error updating {csv_filename}: {e}")

def update_csv_batch(csv_filename, url, source, page_content):
    global batch_data, batch_writing_in_progress

    # Wait until batch writing is not in progress
    while batch_writing_in_progress:
        time.sleep(0.5)  # Sleep to wait for the batch writing to complete

    # Create a new row
    new_row = {"url": url, "source": source, "content": page_content}

    # Lock for thread-safe data modification
    with lock:
        batch_data.append(new_row)

        # Write to CSV if the batch size is reached
        if len(batch_data) >= BATCH_SIZE:
            write_batch_to_csv(csv_filename)

            # Reset the batch after writing
            batch_data = []

# Function to write the accumulated batch to the CSV file
def write_batch_to_csv(csv_filename):
    global batch_data, batch_writing_in_progress

    # Acquire the lock and set the flag to indicate batch writing in progress
    with batch_lock:
        batch_writing_in_progress = True  # Set flag before writing

        if len(batch_data) > 0:
            # Convert the batch data to a DataFrame
            df_batch = pd.DataFrame(batch_data)

            # Append the batch to the CSV file
            if not os.path.exists(csv_filename):
                df_batch.to_csv(csv_filename, index=False, encoding='utf-8')
            else:
                df_batch.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8')

            logging.info(f"Batch of {len(batch_data)} rows written to {csv_filename}")

            # Reset the batch after writing
            batch_data = []

        batch_writing_in_progress = False  # Reset flag after writing


# Function to scrape links from a page recursively with depth control
def scrape_links_from_page(url_tuple, csv_filename, current_depth=0):
    visited = set()
    # Unpack tuple
    source, url, max_depth = url_tuple

    if url in visited or current_depth > max_depth:
        return

    visited.add(url)
    logging.info(f"Scraping {url} at depth {current_depth}")

    page_content, error = scrape_link_content(url)

    # if error:
    #     non_working_links.append((url, error))
    #     return

    if page_content and contains_keywords(page_content):
        update_csv_batch(csv_filename, url, source, page_content)

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
                # Check if the link is a downloadable file (PDF/DOCX)
                if full_link.endswith((".pdf", ".docx")):
                    logging.info(f"Found a file link: {full_link}")
                    file_content = download_and_extract_file(full_link)
                    if file_content:
                        update_csv_batch(csv_filename, full_link, source, file_content)
                else:
                    scrape_links_from_page((source, full_link, max_depth), csv_filename, current_depth + 1)
    except Exception as e:
        logging.error(f"Error extracting links from {url}: {e}")
    finally:
        driver.quit()  # Close the browser

# Function to scrape links in parallel
def parallel_scrape(start_urls, directory):
    # non_working_links = []

    base_directory = f"recursive_data/{directory}"
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    csv_filename = os.path.join(base_directory, generate_csv_filename(directory))

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scrape_links_from_page, url_tuple, csv_filename): url_tuple for url_tuple in start_urls}
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in scraping task: {e}")

    # if non_working_links:
    #     df_non_working = pd.DataFrame(non_working_links, columns=["url", "error_reason"])
    #     df_non_working.to_csv(os.path.join(base_directory, "non_working_links.csv"), index=False)
    #     logging.info(f"Saved non-working links to {os.path.join(base_directory, 'non_working_links.csv')}")

if __name__ == "__main__":
    parallel_scrape(start_urls=SCRAP_LINKS, directory="total")
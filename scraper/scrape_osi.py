from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import requests
import time
import re

# Initialize the Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
# Initialize the Selenium WebDriver with the Chrome options
driver = webdriver.Chrome(options=chrome_options)

# Base URL and number of pages
base_url = "https://opensource.org/licenses/page/"
num_pages = 11

# List to store document links
document_links = []

def extract_paragraph_text(links):
    result = []
    for link in tqdm(links):
        try:
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find the div that contains the license information
            license_content_div = soup.find('div', class_='entry-content post--content license-content')

            # Extract and print the text within this div
            if license_content_div:
                text = license_content_div.get_text(strip=True)
            else:
                print("License information not found.")
            result.append((link, text))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {link}: {e}")
            result.append((link,e))
    return result


# Iterate through the pages
for page_num in range(1, num_pages + 1):
    # Construct the URL for the current page
    url = base_url + str(page_num)
    driver.get(url)

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    # Get the page source
    page_source = driver.page_source

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    for link in soup.find_all('a'):
        href = link.get('href')
        
        #if href and ('pdf' in href or 'doc' in href or 'docx' in href or 'html' in href):
        if href and "https://opensource.org/license/" in href:
            document_links.append(href)


# Define the regex pattern
pattern = r'^https://opensource\.org/license/[^/]+$'

# Filter the list using the pattern
filtered_links = [link for link in document_links if re.match(pattern, link)]
text_tuples = extract_paragraph_text(filtered_links)

data = (pd.DataFrame()
        .assign(url = [_tuple[0] for _tuple in text_tuples])
        .assign(source = "OSI")
        .assign(content = [_tuple[1] for _tuple in text_tuples])
        ).to_csv("osi.csv",index=False)

# Close the WebDriver
driver.quit()

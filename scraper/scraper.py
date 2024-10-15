from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import time
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
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text() for p in paragraphs])
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


text_tuples = extract_paragraph_text(document_links)
for link, text in text_tuples:
    print(f"Link: {link}")
    print(f"Concatenated text: {text}")
    print("-" * 80)

breakpoint()

# Close the WebDriver
driver.quit()

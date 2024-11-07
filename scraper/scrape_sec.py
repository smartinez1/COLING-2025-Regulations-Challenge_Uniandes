
from bs4 import BeautifulSoup
import logging
import os
import random
import re
import pickle
import pypdf
import pandas as pd
import requests
import time
import traceback
# HEADERS = 	{
# 'user-agent':'introxx.96@gmail.com'
# }
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {'User-Agent':'Dummy Company introxx.96@gmail.com','Accept-Encoding':'gzip, deflate','Host':'www.sec.gov'}

HEADERS_2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
}

 # Function to extract text from a DOCX file

def fetch_document_links(base_url):
    document_links = []
    pattern = r'/compliance/risk-alerts/|/newsroom/whats-new/'
    for page_num in range(3):
        url = base_url + str(page_num)
        print(url)

        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

# Iterate through links and append those that match the pattern
        for link in soup.find_all('a', href=True):
            if re.search(pattern, link['href']):
                document_links.append(link['href'])

    return set(["https://www.sec.gov" + link if not link.startswith("https://www.sec.gov") else link and isinstance(link,str) for link in document_links])

# def filter_links(document_links):
#     pattern = r'^https://opensource\.org/license/[^/]+$'
#     return [link for link in document_links if re.match(pattern, link)]


def extract_text_from_pdf(pdf_path):
    text = ""

    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()

    print(text)
    return text

def download_file(link, download_dir="downloads"):
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
        
    except Exception as e:
        logging.error(f"Failed to download or extract file {link}: {traceback.print_exc()}")
        return None

def get_pdf_links(links):
    result = []
    for link in tqdm(links):
        try:
            response = requests.get(link, headers=HEADERS)
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_link = soup.find('a', href=lambda href: href and ".pdf" in href)
            logging.info(f"Fetched pdf link: {pdf_link}")
            result.append(pdf_link["href"])
            time.sleep(random.uniform(7,10))

        except Exception as e:
            logging.error(f"Error fetching link {link}: {e}")

    result.append("https://www.sec.gov/files/risk-alert-multi-branch-adviser-initiative.pdf")
    with open("results/pdf_sec_links.pkl", "wb") as f:
        pickle.dump(result, f)
    return result


def save_to_csv(text_tuples):
    data = pd.DataFrame({
        'url': [t[0] for t in text_tuples],
        'source': "OSI",
        'content': [t[1] for t in text_tuples]
    })
    data.to_csv("osi.csv", index=False)

def main():
    base_url = "https://www.sec.gov/compliance/risk-alerts?page="
    pdf_contents = []

    file_path = "results/pdf_sec_links.pkl"
    if os.path.exists(file_path):
        # Load the existing data
        with open(file_path, "rb") as f:
            pdf_links = pickle.load(f)
        print("Loaded PDF links from file.")
    else:
        document_links = fetch_document_links(base_url)
        pdf_links = get_pdf_links(document_links)

    pdf_links.append("https://www.sec.gov/file/exams-reg-bi-alert-13023.pdf")

    
    pdf_links = [link  for link in pdf_links if isinstance(link,str)]
    updated_links = ["https://www.sec.gov" + link if not link.startswith("https://www.sec.gov") and isinstance(link,str) else link for link in pdf_links]
    logging.info(f"Total pdf files: {len(pdf_links)}")
    updated_links = [link for link in updated_links if link.split('/')[-1] not in os.listdir("downloads/sec_pdfs")]

    for pdf_link in tqdm(updated_links):
        try:
            download_file(pdf_link, download_dir="downloads/sec_pdfs")
            time.sleep(random.uniform(10,20))
        except:
            logging.error(f"Failure scraping link {pdf_link}: {traceback.print_exc()}")
    


    pdf_root = "downloads/sec_pdfs"
    for pdf_file in os.listdir(pdf_root):
        pdf_contents.append((pdf_file, extract_text_from_pdf(os.path.join(pdf_root,pdf_file))))


    data = (pd.DataFrame()
        .assign(url = [_tuple[0] for _tuple in pdf_contents])
        .assign(source = "SEC")
        .assign(content = [_tuple[1] for _tuple in pdf_contents])
        ).to_csv("downloads/sec.csv",index=False)
        

if __name__ == "__main__":
    main()
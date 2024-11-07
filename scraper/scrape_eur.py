import random
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import argparse
import pandas as pd
import logging
import re
import os
import random
import re
import pickle
import time
import traceback
# HEADERS = 	{
# 'user-agent':'introxx.96@gmail.com'
# }
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


NUMS = range(200)

def save_to_csv(text_tuples,source, path_dir):
    data = pd.DataFrame({
        'url': [t[0] for t in text_tuples],
        'source': source,
        'content': [t[1] for t in text_tuples]
    })
    data.to_csv(path_dir, index=False)

def has_legal_content_href(tag):
    pattern = re.compile(r'/legal-content/EN/TXT/HTML')
    return tag.name == 'a' and tag.has_attr('href') and pattern.search(tag['href'])

def get_links():
    ## Create directory
    root_dir = "downloads/eurlex"
    os.makedirs(root_dir,exist_ok=True)

    scrape_links = [f"https://eur-lex.europa.eu/search.html?lang=en&text=%22financial+regulation%22&qid=1730846496804&type=quick&scope=EURLEX&FM_CODED=REG&page={num}" for num in range(200)]

    pdf_links = []
    for link in tqdm(scrape_links):
        
        try:
            #response = requests.get(link, headers=headers)
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            

            legal_content_links = soup.find_all(has_legal_content_href)
            href_values = [link['href'] for link in legal_content_links]

            for href in href_values:
                pdf_links.append(href)

            time.sleep(random.uniform(2,5))
        except:
            logging.error(f"Failure scraping link {link}: {traceback.print_exc()}")
            continue
    
    return pdf_links


def load_data(root_dir):
    pdf_links = os.listdir("downloads/eurlex")    
    results = []
    for link in pdf_links:
        with open(os.path.join(root_dir, link), 'r', encoding='utf-8') as file:
            content = file.read()
        results.append((link,content))
    return results


def concatenate_paragraphs(soup):
    """
    Fetches all <p> tags from a BeautifulSoup object and concatenates their text into a single string.
    
    Args:
    soup (BeautifulSoup): A BeautifulSoup object containing parsed HTML.
    
    Returns:
    str: A single string containing the concatenated text of all <p> tags.
    """
    # Find all <p> tags
    paragraphs = soup.find_all('p')
    
    # Concatenate the text of each paragraph
    concatenated_text = ' '.join(paragraph.text for paragraph in paragraphs)
    
    return concatenated_text

def download_file(link, download_dir="downloads"):
    try:
        # Make sure the download directory exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Get the file extension to identify the file type
        headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Accept': 'application/pdf',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Cookie': 'cck1=%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%2C%22closed%22%3Afalse%7D; PP4=0; AWSALB=WF1XL71WaGunanYXISoDCCZ31R2LhUSS8DKMfZbg7kRZsGBQEn34Z+CmB13Um6xjnq9+ZptCuf+jgzjewrGcNk1pBIj4GNObosG/Kzl6XQlU0QJWfNUuMkF7FkUP; dtCookie=v_4_srv_36_sn_5C77D4D36EFA6E55F8C468A713068F87_perc_100000_ol_0_mul_1_app-3A47d4c64c3b67ec69_1_rcs-3Acss_0; ELX_SESSIONID=a_j_aOdnvFLotQ_ddR3dtV8Mw1ERZ-Lwwq-oADihXZGBWKbMfiZa!1299971279; experimentalFeaturesActivated=false; ecsi=%7B%22https%3A%2F%2Fec.europa.eu%2Fwel%2Fsurveys%2Fwr_survey03%2Fdata%2Finvitation_settings%2Feur-lex%2Finvitation_settings.js%22%3A%7B%22en%22%3A%7B%22show_welcome_pop_up%22%3Afalse%2C%22show_reminder_pop_up%22%3Afalse%7D%7D%7D',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i'}
        
        response = requests.get(link, headers=headers)
        filename = link.split("/")[-1] + '.txt'
        file_path = os.path.join(download_dir, filename)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = concatenate_paragraphs(soup=soup)
        save_text_to_file(text,file_path)
        
        
        
        
    except Exception as e:
        logging.error(f"Failed to download or extract file {link}: {traceback.print_exc()}")
        return None
    
def save_text_to_file(text, output_dir):
    try:
        # Open the file in write mode ('w') and create it if it doesn't exist
        with open(output_dir, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"File successfully saved at: {output_dir}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def main():
    parser = argparse.ArgumentParser(description='Process some tasks.')
    parser.add_argument('task', type=str, help='Task to be executed')
    
    args = parser.parse_args()
    
    if args.task == 'links':
        links = get_links()
        with open("downloads/eurlex.pkl", "wb") as f:
            pickle.dump(links, f)


    elif args.task == "download":
        download_dir = "downloads/eurlex"
        with open("downloads/eurlex.pkl", "rb") as f:
                content = pickle.load(f)


        pdf_links = set([("https://eur-lex.europa.eu" + link).replace(".eu./",".eu/") if not link.startswith("https://eur-lex.europa.eu") else link and isinstance(link,str) for link in content])

        logging.info(f"Amount of links present in eurlex: {len(pdf_links)}")

        scraped_parts = [link.split('?')[-1].split('.')[0] for link in os.listdir(download_dir)]
        scrape_links = [link for link in pdf_links if link.split('?')[-1] not in scraped_parts]
        logging.info(f"len scrape links after filtering out elements already scraped: {len(scrape_links)}")
        for link in tqdm(scrape_links):
            download_file(link, download_dir)
            time.sleep(random.uniform(0.3,2))


    elif args.task == 'load':
        results = load_data(root_dir="downloads/eurlex")

        data = (pd.DataFrame()
        .assign(url = [_tuple[0] for _tuple in results])
        .assign(source = "EUR-LEX")
        .assign(content = [_tuple[1] for _tuple in results])
        ).to_csv("downloads/eurlex.csv",index=False)


    else:
        logging.error(f"Unknown task: {args.task}")

if __name__ == "__main__":
    main()


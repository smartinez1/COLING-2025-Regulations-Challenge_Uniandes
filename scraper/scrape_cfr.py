
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import argparse
import pandas as pd
import logging
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


NUMS = ["1","2","3","4","5","7","9", "10", "11", "12", "13", "14", "15","16","17","18", "19", "20",
               "21", "22", "23", "30", "31", "32", "33", "34", "35", "36" , "37", "38", "39", "40", "41", "42",
               "43", "44", "45", "46", "48", "49", "50", "75", "100", "140", "141", "142", "143", "144", "145",
               "146", "147", "148", "149", "150", "155", "156", "160", "162", "165", "166", "170", "172", "180",
               "190", "200", "201", "202", "203", "204", "205", "209", "210", "211", "227", "229", "230", "231",
                "232", "239", "240", "241", "242", "243", "244", "245", "246", "247", "248", "249", "249b", "250",
                "255", "260", "261", "269", "270", "271", "274", "275", "276", "279", "281", "285", "286", "287",
                "288", "289", "290", "300", "301", "302", "400", "401", "402", "403", "404", "405", "420", "449",
                "450"
               ]

def save_to_csv(text_tuples,task_name):
    data = pd.DataFrame({
        'url': [t[0] for t in text_tuples],
        'source': task_name,
        'content': [t[1] for t in text_tuples]
    })
    data.to_csv("osi.csv", index=False)


def save_text_to_file(text, output_dir):
    try:
        # Open the file in write mode ('w') and create it if it doesn't exist
        with open(output_dir, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"File successfully saved at: {output_dir}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def process_section_divs(section_divs):
    results = []
    for div in section_divs:
        result = process_single_div(div)
        results.append(result)
    return results

def process_single_div(div):
    content = ""
    
    # Check for <h4> tag and if it contains '§'
    h4_tag = div.find('h4')
    if h4_tag and '§' in h4_tag.text:
        content += h4_tag.text + "\n"
    
    # Fetch all divs with "id" attribute
    inner_divs = div.find_all('div', id=True)
    for inner_div in inner_divs:
        content += process_inner_div(inner_div)
    
    return content

def process_inner_div(inner_div):
    content = ""
    div_id = inner_div.get('id')
    if div_id:
        content += div_id + "\n"
    
    # Append <p> tag value
    p_tag = inner_div.find('p')
    if p_tag:
        content += p_tag.text + "\n"
    
    return content

def scrape_cfd():
    ## Create directory
    root_dir = "downloads/cfr"
    os.makedirs(root_dir,exist_ok=True)

    scrape_links = [f"https://www.ecfr.gov/current/title-17/chapter-I/part-{num}" for num in NUMS]
    logging.info(f"Amount of links present in title 17 cfd: {len(scrape_links)}")

    scraped_parts = [link.split('/')[-1].split('.')[0] for link in os.listdir(root_dir)]
    scrape_links = [link for link in scrape_links if link.split('/')[-1] not in scraped_parts]
    logging.info(f"len scrape links after filtering out elements already scraped: {len(scrape_links)}")

    headers = []
    for link in scrape_links:
        headers.append({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': link,
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'cors'
})

    for link, headers in tqdm(zip(scrape_links,headers)):
        try:
            response = requests.get(link, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            

            _inter_result = []
            for div in soup.find_all('div', class_='section'):
                _inter_result.append(process_single_div(div))
            combined_text = "".join(_inter_result)
            save_text_to_file(text=combined_text, output_dir=os.path.join(root_dir,link.split('/')[-1] + ".txt"))
            time.sleep(random.uniform(10,20))
        except:
            logging.error(f"Failure scraping link {link}: {traceback.print_exc()}")
            continue
    

def load_cfd_data():
    root_dir = "downloads/cfr"
    read_links = [link for link in os.listdir(root_dir)]

    results = []

    for link in read_links:
        with open(os.path.join(root_dir, link), 'r', encoding='utf-8') as file:
            content = file.read()
        results.append((link,content))

    return results



def main():
    parser = argparse.ArgumentParser(description='Process some tasks.')
    parser.add_argument('task', type=str, help='Task to be executed')
    
    args = parser.parse_args()
    
    if args.task == 'scrape_cfd':
        scrape_cfd()
    elif args.task == 'load':
        results = load_cfd_data()

        data = (pd.DataFrame()
        .assign(url = [_tuple[0] for _tuple in results])
        .assign(source = "CFR")
        .assign(content = [_tuple[1] for _tuple in results])
        ).to_csv("downloads/cfr.csv",index=False)


    else:
        logging.error(f"Unknown task: {args.task}")

if __name__ == "__main__":
    main()


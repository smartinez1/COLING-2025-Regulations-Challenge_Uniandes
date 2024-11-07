
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import logging
import traceback
import random
import requests
import tiktoken
import os
import re
import numpy as np
import time
from gensim import corpora, models, similarities
from gensim.parsing.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from gensim.parsing.preprocessing import remove_stopwords

encoding = tiktoken.encoding_for_model("gpt-4o-mini")



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {'User-Agent':'Dummy Company introxx.96@gmail.com','Accept-Encoding':'gzip, deflate','Host':'www.sec.gov'}

# Load dictionary, corpus, and similarity index
dictionary = corpora.Dictionary.load('midict.dict')
corpus = corpora.MmCorpus('corpus.mm')
index = similarities.MatrixSimilarity.load('similmatrix.index')

# Load the pre-trained TF-IDF model
tfidf = models.TfidfModel(corpus)

# Keywords to look for in the page content
pos_query = """Regulation, law, statute, council, commission, article, compliance, directive, guideline, standard,
legislation, regulatory framework, policy, decree, act, provision, rule, amendment, enforcement, 
supervisory authority, financial conduct, oversight, legal framework, code of practice, 
prudential regulation, anti-money laundering (AML), know your customer (KYC), 
sanction, financial service, banking law, securities regulation, corporate governance, 
fiduciary duty, disclosure requirements, risk management, audit, inspection, 
financial stability, consumer protection, data protection, privacy, cybersecurity, 
financial crime, fraud prevention, capital requirement, solvency, liquidity, 
market abuse, insider trading, conflict of interest, transparency, reporting obligation, 
whistleblower protection, ethical standards, financial oversight, investment guideline, 
tax law, fiscal policy, monetary policy, currency regulation, exchange control, 
credit regulation, insurance regulation, pension regulation, derivative, 
financial instrument, payment system, financial market infrastructure, 
clearing, settlement, fintech, digital currency, blockchain, cryptocurrency, 
initial coin offering (ICO), electronic money, payment service, crowdfunding, 
peer-to-peer lending, robo-advisory, virtual asset, financial innovation, open source, Permissive License, Dual Licensing, Source Code, Binary Form, Distribution, Contribution,
derivative work, attribution, Patent Grant, warranty, liability, trademark"""
 
neg_query = """"cookies", "submenu", "toggle", "contact", "help", "home", "about", "navigation", "footer", "header", "sidebar", "dropdown", 
"sitemap", "login", "register", "user interface", "UI", "UX", "user experience", "breadcrumbs", "carousel", "slider", 
"accordion", "tab", "widget", "modal", "popup", "overlay", "hamburger menu", "footer menu", "social media links", 
"privacy policy", "terms of use", "disclaimer", "search bar", 
"login form", "sign up", "account settings", "profile", "logout", "dashboard", "settings", "preferences", 
"site map", "accessibility", "mobile menu", "responsive design", "click here", "more info", "gallery",
"webmaster", "copyright", "legal notice", "back to top", "scroll to", "navigation bar", "menu item", 
"site navigation", "page layout", "layout", "theme", "template", "CSS", "HTML", "JavaScript", "web development", 
"web design", "frontend", "backend", "server-side", "client-side", "framework", "library", "API", "REST", "SOAP", "web service", "HTTP", "HTTPS", "SSL", "secure connection", "domain name", "URL", "URI", "web hosting", "cloud hosting", 
"server", "database", "SQL", "NoSQL", "CMS", "content management system", "WordPress", "Joomla", "Drupal", "Magento", 
"Shopify", "Wix", "Squarespace", "web page", "landing page", "homepage", "blog", "post", "comment section", "linkedin", "flickr", "facebook", "instagram", "threads", "x", "twitter"""


p = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')
# Función de preprocesamiento, se usará para todos los inputs al modelo (queries y documentos)
def preprocess_text(text: str):
    """Preprocesa un texto para eliminar palabras vacías, aplicar stemming y convertir a minúsculas.

    Args:
        text (str): El texto a preprocesar.

    Returns:
        List: Una lista con las palabras del texto preprocesado.
    """
    text = text.strip().lower()  # Normalización del texto, todo en minúscula y se quitan espacios innecesarios.
    doc_sw = remove_stopwords(text)
    doc_stem = p.stem_sentence(doc_sw)
    return tokenizer.tokenize(doc_stem)

def num_tokens_from_string(string, encoding) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens

def score_new_document(text_input, pos_query=pos_query, neg_query=neg_query):
    # Convert the positive, negative queries, and new text input into bag-of-words format
    query_pos_bow = dictionary.doc2bow(preprocess_text(pos_query))
    query_neg_bow = dictionary.doc2bow(preprocess_text(neg_query))
    text_input_bow = dictionary.doc2bow(preprocess_text(text_input))

    # Convert the BOW representations to TF-IDF
    query_pos_tfidf = tfidf[query_pos_bow]
    query_neg_tfidf = tfidf[query_neg_bow]
    text_input_tfidf = tfidf[text_input_bow]

    # Ensure all TF-IDF vectors are of the same length based on the dictionary
    pos_vector_dense = np.zeros(len(dictionary))
    for idx, value in query_pos_tfidf:
        pos_vector_dense[idx] = value

    neg_vector_dense = np.zeros(len(dictionary))
    for idx, value in query_neg_tfidf:
        neg_vector_dense[idx] = value

    input_vector_dense = np.zeros(len(dictionary))
    for idx, value in text_input_tfidf:
        input_vector_dense[idx] = value

    # Compute cosine similarity scores
    pos_similarity = np.dot(input_vector_dense, pos_vector_dense)
    neg_similarity = np.dot(input_vector_dense, neg_vector_dense)

    # Calculate the final score by subtracting the negative similarity from the positive similarity
    final_score = pos_similarity - neg_similarity
    
    print("Score:", final_score)
    print("For:", text_input[:20])
    
    return final_score


def truncate_text(text, tokenizer, max_tokens=128000, target_tokens=115000):
    """
    Truncates the text to a target token count if it exceeds the maximum allowed tokens.

    Args:
    text (str): The text to be processed.
    tokenizer: The tokenizer instance used to tokenize the text.
    max_tokens (int): The maximum number of tokens allowed before truncation.
    target_tokens (int): The target number of tokens for truncation.

    Returns:
    str: The processed text.
    """
    # Tokenize the text and check the number of tokens
    tokens = tokenizer.encode(text)
    if len(tokens) > max_tokens:
        # Truncate the tokens to the target number and decode back to text
        truncated_tokens = tokens[:target_tokens]
        return tokenizer.decode(truncated_tokens)
    return text


if __name__ == "__main__":
    # url = "https://cdm.finos.org/docs/home"
    # response = requests.get(url)
    # soup = BeautifulSoup(response.content, 'html.parser')
    # scrapable_links = set([a['href'] for a in soup.find_all('a', href=re.compile(r'/docs/'))])
    # scrapable_links = [link if link.startswith("https://cdm.finos.org") else "https://cdm.finos.org" + link for link in scrapable_links] 

    # text = ""

    # for link in tqdm(scrapable_links):
    #     try:
    #         _req = requests.get(link)
    #         _soup = BeautifulSoup(_req.content, 'html.parser')
    #         for tag in _soup.find_all('p'):
    #             text += tag.get_text()
    #         print(text)
    #         time.sleep(random.uniform(0.4,3))
    #     except:
    #         logging.error(f"Could not get information for page {link}. Error: {traceback.print_exc()}")


    # logging.info(f"Scraped document has {num_tokens_from_string(text, encoding)} tokens")

    # df = (pd.DataFrame()
    #  .assign(url= ["CDM docs"])
    #  .assign(source = ["CDM"])
    #  .assign(content = [text]))
    # df.to_csv("downloads/cdm.csv",index=False)

    df = pd.read_csv("results/cleaning/cleaning_v1.csv")
    df1 = pd.read_csv("downloads/sec.csv")
    df2 = pd.read_csv("downloads/cdm.csv")
    df3 = pd.read_csv("downloads/cfr.csv").dropna()
    df4 = pd.read_csv("results/cleaning_eurlex/cleaning.csv")
    df5 = pd.read_csv("downloads/fdic.csv")



    df1 = (df1
           .assign(task = "")
           .assign(total_tokens = df1["content"].apply(lambda x: num_tokens_from_string(x,encoding)))
           .assign(generated_text = "")
           .assign(costs = 0)
           )
    
    df2 = (df2
           .assign(task = "")
           .assign(total_tokens = df2["content"].apply(lambda x: num_tokens_from_string(x,encoding)))
           .assign(generated_text = "")
           .assign(costs = 0)
           )

    df3 = (df3
           .dropna()
           .assign(task = "")
           .assign(total_tokens = df3["content"].apply(lambda x: num_tokens_from_string(x,encoding)))
           .assign(generated_text = "")
           .assign(costs = 0)
           )
    
    df4 = (df4
           .dropna()
           .assign(task = "")
           .assign(total_tokens = df4["content"].apply(lambda x: num_tokens_from_string(x,encoding)))
           .assign(generated_text = "")
           .assign(costs = 0)
           )
    
    df5 = (df5
           .dropna()
           .assign(task = "")
           .assign(total_tokens = df5["content"].apply(lambda x: num_tokens_from_string(x,encoding)))
           .assign(generated_text = "")
           .assign(costs = 0)
           )


    total_df = pd.concat([df,df1,df2,df3,df4, df5],ignore_index=True)
    total_df = total_df.assign(content = total_df["content"].apply(lambda x: truncate_text(x, encoding, max_tokens=120000)))
    total_df = total_df.drop_duplicates()
    total_df.to_csv("results/cleaning/cleaning.csv",index=False)

import pandas as pd
import numpy as np
import logging
from gensim.parsing.preprocessing import remove_stopwords
from gensim.parsing.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from gensim import corpora, models, similarities
from smart_open import smart_open
import tiktoken

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


COMPOSITE_TERMS = [
    "market abuse", "payment system", "anti money laundering", "know your customer",
    "capital requirement", "financial service", "banking law", "securities regulation",
    "corporate governance", "fiduciary duty", "disclosure requirements", "risk management",
    "financial stability", "consumer protection", "data protection", "financial crime",
    "fraud prevention", "insider trading", "conflict of interest", "reporting obligation",
    "whistleblower protection", "ethical standards", "financial oversight", "investment guideline",
    "tax law", "fiscal policy", "monetary policy", "currency regulation", "exchange control",
    "credit regulation", "insurance regulation", "pension regulation", "financial instrument",
    "financial market infrastructure", "clearing and settlement", "digital currency",
    "blockchain", "cryptocurrency", "initial coin offering", "electronic money", "payment service",
    "crowdfunding", "peer to peer lending", "robo advisory", "virtual asset", "financial innovation","user interface", "user experience", "hamburger menu", "footer menu", "social media links", 
"privacy policy", "terms of use", "disclaimer", "FAQ", "frequently asked questions", "search bar", 
"login form", "sign up", "account settings", "site map", "accessibility", "mobile menu", "responsive design", "click here", "more info", "gallery", "portfolio", "legal notice", "back to top", "scroll to", "navigation bar", "menu item", 
"site navigation", "page layout", "web development", "web design", "web service", "secure connection", "domain name", "web hosting", "cloud hosting", "content management system"
]

POS_QUERY = """Regulation, law, statute, council, commission, article, compliance, directive, guideline, standard,
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
peer-to-peer lending, robo-advisory, virtual asset, financial innovation"""


NEG_QUERY = """"cookies", "submenu", "toggle", "contact", "help", "home", "about", "navigation", "footer", "header", "sidebar", "dropdown", 
"sitemap", "login", "register", "user interface", "UI", "UX", "user experience", "breadcrumbs", "carousel", "slider", 
"accordion", "tab", "widget", "modal", "popup", "overlay", "hamburger menu", "footer menu", "social media links", 
"privacy policy", "terms of use", "disclaimer", "search bar", 
"login form", "sign up", "account settings", "profile", "logout", "dashboard", "settings", "preferences", 
"site map", "accessibility", "mobile menu", "responsive design", "click here", "more info", "gallery",
"webmaster", "copyright", "legal notice", "back to top", "scroll to", "navigation bar", "menu item", 
"site navigation", "page layout", "layout", "theme", "template", "CSS", "HTML", "JavaScript", "web development", 
"web design", "frontend", "backend", "server-side", "client-side", "framework", "library", "API", "REST", "SOAP", "web service", "HTTP", "HTTPS", "SSL", "secure connection", "domain name", "URL", "URI", "web hosting", "cloud hosting", 
"server", "database", "SQL", "NoSQL", "CMS", "content management system", "WordPress", "Joomla", "Drupal", "Magento", 
"Shopify", "Wix", "Squarespace", "web page", "landing page", "homepage", "blog", "post", "comment section", "linkedin", "flickr", "facebook", "instagram", "threads", "x", "twitter
"WordPress", "Joomla", "Drupal", "Magento","Shopify", "Wix", "Squarespace", "web page", "landing page", "homepage", "blog", "article", "post", "comment section", "linkedin", "flickr", "facebook", "instagram", "threads", "x", "twitter",
"page layout", "layout", "theme", "template", "CSS", "HTML", "JavaScript"
"""



def load_data(filepath):
    return pd.read_csv(filepath)

def encode_text(df, encoding):
    def num_tokens_from_string(string):
        return len(encoding.encode(string))
    df = df.assign(num_tokens=df["content"].apply(num_tokens_from_string))
    return df

def preprocess_text(text):
    p = PorterStemmer()
    tokenizer = RegexpTokenizer(r'\w+')
    text = text.strip().lower()
    doc_sw = remove_stopwords(text)
    doc_stem = p.stem_sentence(doc_sw)
    return tokenizer.tokenize(doc_stem)

def preprocess_composite_terms(text, composite_terms):
    for term in composite_terms:
        new_text = text.replace(term, term.replace(" ", ""))
        if text != new_text:
            text = new_text
    return text

def create_corpus_file(df, composite_terms, corpus_file_path):
    with open(corpus_file_path, 'w', encoding='utf-8') as corpus_file:
        for row in df.iterrows():
            content = row[1].content
            content = preprocess_composite_terms(content, composite_terms)
            content_without_newlines = content.replace('\n', '')
            encoded_content = content_without_newlines.encode('utf-8', errors='ignore').decode('utf-8')
            corpus_file.write(encoded_content + '\n')

def build_dictionary_and_corpus(df, corpus_file_path):
    dictionary = corpora.Dictionary(df['preproc_text'].tolist())
    dictionary.save("midict.dict")
    class MyCorpus(object):
        def __iter__(self):
            for line in smart_open(corpus_file_path, "rb"):
                yield dictionary.doc2bow(preprocess_text(line))
    corpus_memory_friendly = MyCorpus()
    corpora.MmCorpus.serialize("corpus.mm", corpus_memory_friendly)
    return dictionary, corpora.MmCorpus("corpus.mm")

def build_tfidf_model(corpus):
    return models.TfidfModel(corpus)

def retrieve_and_rank_documents(tfidf, dictionary, corpus, pos_query, neg_query):
    index = similarities.MatrixSimilarity(tfidf[corpus])
    query_pos_doc_bow = dictionary.doc2bow(preprocess_text(pos_query))
    query_neg_doc_bow = dictionary.doc2bow(preprocess_text(neg_query))
    sims_pos = index[tfidf[query_pos_doc_bow]]
    sims_neg = index[tfidf[query_neg_doc_bow]]
    final_scores = [(index, pos_score - neg_score) for index, (pos_score, neg_score) in enumerate(zip(sims_pos, sims_neg))]
    sorted_scores = sorted(final_scores, key=lambda x: x[1], reverse=True)
    return sorted_scores

def filter_thru_thresh(df:pd.DataFrame, thresh:float= 0.8):

    df_sorted = df.sort_values(by='score', ascending=True)
    threshold = int(len(df_sorted) * thresh)
    return df_sorted.tail(threshold)


def main():
    df = load_data("recursive_data/total/total_cleaned.csv")
    df_osi = load_data("osi.csv")

    df = pd.concat([df,df_osi],ignore_index=True)

    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    df = encode_text(df, encoding)

    logging.info(f"len before drop: {len(df)}")
    df = df[df.num_tokens > 500].reset_index(drop=True)
    logging.info(f"len after drop: {len(df)}")

    df['preproc_text'] = df['content'].apply(preprocess_text)
    corpus_file_path = "mycorpusGensim.txt"
    create_corpus_file(df, COMPOSITE_TERMS, corpus_file_path)
    dictionary, corpus = build_dictionary_and_corpus(df, corpus_file_path)
    tfidf = build_tfidf_model(corpus)

    ranking = retrieve_and_rank_documents(tfidf, dictionary, corpus, POS_QUERY, NEG_QUERY)
    ranking_df = pd.DataFrame(ranking, columns=['index', 'score'])
    df['index'] = df.index
    df = pd.merge(df, ranking_df, on='index', how='left')
    df.loc[df['source'] == 'OSI', 'score'] = float(0.3)

    logging.info(f"Len before TFIDF filtering: {len(df)}")
    df_filt = filter_thru_thresh(df=df, thresh= 0.8)
    logging.info(f"len after TFIDF filtering: {len(df_filt)}")
    df_filt.to_csv("recursive_data/total/refined_data.csv",index=False)

if __name__ == "__main__":
    main()
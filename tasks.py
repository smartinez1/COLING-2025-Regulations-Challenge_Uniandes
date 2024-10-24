import pandas as pd 
from scraper_links import ABBREV
from openai import AzureOpenAI
import openai
import time
from dotenv import load_dotenv
import os
import traceback
from langchain.prompts import PromptTemplate

load_dotenv()

def load_data(data_path:str)-> pd.DataFrame:
    return pd.read_csv(data_path)

def generar_preguntas_y_respuestas(text):
    # Define a prompt template for generating questions and answers
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template="""
        Below, you have the following text: "{text}". Based on this text:

        1. Write 1 question that covers the main aspects of the text.
        2. Provide a detailed answer based on the information from the text.

        Follow the format:
        ´´´
        Question: [Question]
        Answer: [Answer]
        ´´´
        The question should be clear, and should not reference the provided text.
        """
    )
    # Format the input text into the template
    prompt = prompt_template.format(text=text)


    try:
        resultado_completo = send_prompt(prompt)
        return resultado_completo
    
    except:
        print(traceback.print_exc())
        #print("Rate limit exceeded. Waiting before retrying...")
        #time.sleep(60)


def send_prompt(prompt):
    
    deployment_name2 = "gpt-4o-mini"
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

    chat_completion_zero = client.chat.completions.create(
        model=deployment_name2,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.1
    )
    return chat_completion_zero # Extract the response




if __name__ == "__main__":
    # sexius = AzureOpenAI()

    # Example raw text input (replace with your actual input text)
    texto_raw = """
    Federal Reserve Board - Site Map Skip to main content Back to Home Board of Governors of the Federal Reserve System Stay Connected Federal Reserve Facebook Page Federal Reserve Instagram Page Federal Reserve YouTube Page Federal Reserve Flickr Page Federal Reserve LinkedIn Page Federal Reserve Threads Page Federal Reserve Twitter Page Subscribe to RSS Subscribe to Email Recent Postings Calendar Publications Site Map A-Z index Careers FAQs Videos Contact Search Submit Search Button Advanced Toggle Dropdown Menu Board of Governors of the Federal Reserve System The Federal Reserve, the central bank of the United States, provides
            the nation with a safe, flexible, and stable monetary and financial
            system. Main Menu Toggle Button Sections Search Toggle Button Search Search Submit Button Submit About the Fed Structure of the Federal Reserve System The Fed Explained Board Members Advisory Councils Federal Reserve Banks Federal Reserve Bank and Branch Directors Federal Reserve Act Currency Board Meetings Board Votes Diversity & Inclusion Careers Do Business with the Board Holidays Observed - K.8 Ethics & Values Contact Requesting Information (FOIA) FAQs Economic Education Fed Financial Statements Innovation News & Events Press Releases Speeches Testimony Calendar Videos Photo Gallery Conferences Monetary Policy Federal Open Market Committee About the FOMC Meeting calendars and information Transcripts and other historical materials FAQs Monetary Policy Principles and Practice Notes Policy Implementation Policy Normalization Policy Tools Reports Monetary Policy Report Beige Book Federal Reserve Balance Sheet Developments Review of Monetary Policy Strategy, Tools, and Communications Overview Supervision & Regulation Institution Supervision Novel Activities Supervision Program .
            ."
    """
    # Generate questions and answers based on the raw input text
    preguntas_y_respuestas = generar_preguntas_y_respuestas(texto_raw)

    # Print the generated questions and answers
    print(preguntas_y_respuestas)


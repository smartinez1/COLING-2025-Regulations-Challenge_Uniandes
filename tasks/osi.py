from utils import OpenAIPromptHandler
import pandas as pd
import asyncio



BASE_PROMPT = """
    Given the following text:
    ´´´
    {context}
    ´´´
    Generate question/answer pairs relevant to the text you observe. These questions must be formulated in a way such that:
    a. The question is focused on knowing more about open source software licensing and applications
    b. The question must have a financial regulatory intent
    c. The answer distills knowledge in a concise and factual manner in order to answer the question's intent.

    Return them in a numerated list following this format:
    ´´´
    1. <question> - <answer>
    2. <question> - <answer>
    .
    .
    .
    n. <question> - <answer>
    ´´´
    ONLY provide this list, nothing else, nothing extra.
"""

SYSTEM_PROMPT = "You are an accurate, articulate and knowledgeable in open source licensing knowledge for financial and business applications."



def generate_osi_qa(data:pd.DataFrame,q_dir:str, api_handler:OpenAIPromptHandler):
    """
    Takes in the integrity of documents and generates questions.
    """





def main():

    df = pd.read_csv("recursive_data/total/total_cleanedv2.csv")
    df = df[df.source == "OSI"]
    

    handler = OpenAIPromptHandler()


    
asyncio.run(main())





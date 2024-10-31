from tasks.utils import OpenAIPromptHandler

CLASSIF_PROMPT = """
Given the following text:
    ´´´
    {context}
    ´´´

Examine the document given and check the following:
    1. Is the document in English?
    2. Are the document's contents about topics related to financial regulation, industry standards, compliance processes, open source documentation and licensing?
    

    If either of them is false, then say "no", otherwise say "yes". Output your choice only.
"""


CLEANING_PROMPT = """
Given the following text:
    ´´´
    {context}
    ´´´

Examine the given document and clean its contents. I'd like you to do the following:
    1. Cut off irrelevant parts of the text that are involved with social media links or with a site's navigation menu.
    2. Summarize the text so that it is more concise in its ideas and facts.

The resulting text must not differ much in its contents. It is for restructuring purposes only. Output the summary text.

<text>
"""




CLASSIF_SYSTEM = """
You are an expert in financial regulation and compliance, managing knowledge from both the USA and Europe, You are also well versed in open source technologies.
"""

CLEANING_SYSTEM = """
You are a diligent editor and proofreader expert in cleaning articles.
"""

class LLMFilter(OpenAIPromptHandler):

    pass





def main():
    pass



if __name__ == "__main__":
    main()
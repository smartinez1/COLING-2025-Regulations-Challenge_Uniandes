PROMPT_OSI_QA = """
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

PROMPT_OSI_ABBREV = """
    Given the following text:
    ´´´
    {context}
    ´´´
    Extract all abbreviations that appear along with their expanded versions such that:
    a. The abbreviations have to do with open source licensing
    b. The question must have a financial regulatory intent
    c. The answer distills knowledge in a concise and factual manner in order to answer the abbreviation's factual meaning.

    Return them in a numerated list following this format:
    ´´´
    1. <abbreviation> - <expanded version>
    2. <abbreviation> - <expanded version>
    .
    .
    .
    n. <abbreviation> - <expanded version>
    ´´´
    ONLY provide this list, nothing else, nothing extra.
"""

SYSTEM_PROMPT_OSI = "You are an accurate, articulate and knowledgeable in open source licensing knowledge for financial and business applications."



## DATA PROCESSOR

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



### SOURCE CATEGORIES 

ABBREV = ["EUR-LEX", 
          "ESMA", 
          "SEC", 
          "CFTC", 
          "FINRA",
          "FED",
          "FDIC",
          "III",
          "FASAB",
          "SBOA",
          "NYSE"
          ]


QA_TASK = ["SEC",
           "FED",
           "FDIC",
           "III",
           "FASAB",
           "SBOA"
           ]

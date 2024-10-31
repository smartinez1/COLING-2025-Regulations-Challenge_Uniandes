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

SYSTEM_PROMPT_OSI = "You are an accurate, articulate and knowledgeable in open source licensing knowledge for financial and business applications."

##
# ABBREVIATIONS, LINKS, Definitions

PROMPT_ABBREV = """
        Pay close attention to the following text:
        ```
        {context}
        ```
        extract all abbreviations that appear along with their expanded versions.
        return them in a numerated list following this format:
        ```
        1. <abbreviation> - <expanded version>
        2. <abbreviation> - <expanded version>
        .
        .
        .
        n. <abbreviation> - <expanded version>
        ```
        ONLY provide this list, nothing else.
        """

PROMPT_LINKS = """
        Pay close attention to the following text:
        ```
        {context}
        ```
        Is the text explaining a law/s or regulation/s explicitly by name? (ej: Regulation (EU) 2019/834)
        if so, please provide a list with this format:
        ```
        1. <law>
        2. <law>
        .
        .
        n. <law>
        ```
        if no law is found, provide an empty response
        ONLY provide this list, nothing else.
        """

PROMPT_DEFS = """
        Pay close attention to the following text:
        ```
        {context}
        ```
        Are there any content domain specific terms being defined?:
        if so privide a list of all found terms and ther definitions with this format:
        ```
        1. <term> - <definition>
        2. <term> - <definition>
        .
        .
        n. <term> - <definition>
        ```
        if no term is found, provide an empty response
        ONLY provide this list, nothing else.
        """

SYSTEM_PROMPT_GENERAL = "You are an accurate transliterator, articulate and knowledgeable in law and regulation for the US and EU"

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





BANNED_DOMAINS = [
    "facebook.com", "twitter.com", "youtube.com", "instagram.com",
    "linkedin.com", "t.co", "x.com", "pinterest.com", "reddit.com", "flickr.com",
    "threads.net"
]

SCRAP_LINKS = [("EUR-LEX","https://eur-lex.europa.eu/oj/direct-access.html",4),
                ("ESMA","https://www.esma.europa.eu/",4),
                ("SEC","https://www.sec.gov/",4),
                ("SEC_RULES","https://www.sec.gov/rules-regulations",3),
                ("CFTC","https://www.cftc.gov/",4),
                ("FINRA","https://www.finra.org/registration-exams-ce/qualification-exams/terms-and-acronyms",2),
                ("FED","https://www.federalreserve.gov/",4),
                ("FDIC","https://www.fdic.gov/federal-deposit-insurance-act",2),
                ("III","https://www.iii.org/publications/insurance-handbook/regulatory-and-financial-environment/",2),
                #("FASAB","https://files.fasab.gov/pdffiles/2023_FASAB_Handbook.pdf"),
                ("SBOA","https://www.in.gov/sboa/about-us/sboa-glossary-of-accounting-and-audit-terms/",2),
                ("NYSE","https://www.nyse.com/index",4),
                ("ECFR","https://www.ecfr.gov/",4),
                ("XBRL_WEB","https://www.xbrl.org/guidance/xbrl-glossary/",1), # Seems like its just a static page here
                ("XBRL_DOC","https://www.sec.gov/data-research/osd_xbrlglossary",1), # One static page as well
                #("XBRL_REP_FIN","https://arxiv.org/abs/2311.11944"), PDF
                #("XBRL_REP_DOW",), Points to the SEC
                ("CDM","https://cdm.finos.org/",4),
                ("FINOS","https://www.finos.org/faq",1),
                ("OSI","https://opensource.org/licenses",4)    
                ] #TODO: When we handle pdfs, scrape the last link

## TODO: Most of the categories share links, we can just create a mapping to retrieve relevant documents per dataset section


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
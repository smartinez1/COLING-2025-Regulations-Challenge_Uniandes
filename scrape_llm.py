from scrapegraphai.graphs import SmartScraperGraph
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

graph_config = {
    "llm": {
        "api_key": api_key,
        "model": deployment_name,
        "endpoint": endpoint,
    },
    "verbose": True,
    "headless": True,
}

smart_scraper_graph = SmartScraperGraph(
    prompt="Fetch me all the documents related to financial laws and regulations. These must be lengthly documents with extreme detail about the financial domain.",
    source="https://www.fdic.gov/laws-and-regulations/fdic-law-regulations-related-acts",
    config=graph_config
)

result = smart_scraper_graph.run()
print(result)
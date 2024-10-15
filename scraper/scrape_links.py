from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
import os

from dotenv import load_dotenv


load_dotenv()

llm_model_instance = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
)

# graph_config = {
#     "llm": {
#         "model_instance": llm_model_instance,
#     },
# }
breakpoint()

graph_config = {
    "llm": {
        "api_key": os.environ["AZURE_OPENAI_API_KEY"],
        "model": llm_model_instance,
    },
    "verbose": True,
    "headless": False
}

from scrapegraphai.graphs import SmartScraperGraph
from scrapegraphai.utils import prettify_exec_info

smart_scraper_graph = SmartScraperGraph(
    prompt="List me all the projects with their description.",
    # also accepts a string with the already downloaded HTML code
    source="https://perinim.github.io/projects",
    config=graph_config
)

result = smart_scraper_graph.run()
print(result)
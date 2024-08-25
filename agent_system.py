import threading
from queue import Queue
from typing import List, Dict, Any
from plugin_manager import PluginManager
from llm.llama import LLM
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import logging
import concurrent.futures
from colorlog import ColoredFormatter
import re
from urllib.parse import urlparse, parse_qs
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOG_FORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
logger = logging.getLogger('pythonConfig')
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

class Agent:
    def __init__(self, name: str, plugin_manager: PluginManager, llm: LLM, session: aiohttp.ClientSession):
        self.name = name
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.session = session
        self.results = {}
        self.training_data = []
        self.final_message = ""
        logger.debug(f"Agent '{name}' initialized")

    async def __aenter__(self):
        logger.debug(f"Agent '{self.name}' entering context")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.session = None
        logger.debug(f"Agent '{self.name}' exiting context")

    async def run_analysis(self, prompt):
        logger.debug(f"Agent {self.name} starting analysis with prompt: {prompt[:50]}...")
        try:
            url_match = re.search(r'https?://\S+', prompt)
            if not url_match:
                logger.error("No valid URL found in the prompt")
                raise ValueError("No valid URL found in the prompt")
            url = url_match.group(0)
            logger.debug(f"Extracted URL: {url}")

            async with self.session.get(url) as response:
                logger.debug(f"Fetched content from {url}")
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
            
            logger.debug("Starting form and GET parameter checks")
            tasks = [
                self._check_forms(url, soup),
                self._check_get_params(url)
            ]
            results = await asyncio.gather(*tasks)
            self.results = [result for result in results if result]
            logger.debug(f"Analysis completed. Found {len(self.results)} potential vulnerabilities.")

        except Exception as e:
            logger.error(f"Error in run_analysis for {self.name}: {str(e)}")

    async def _check_forms(self, url, soup):
        forms = soup.find_all('form')
        results = []
        for form in forms:
            result = await self._check_form(url, form)
            if result:
                results.append(result)
        return results

    async def _check_form(self, url, form):
        # Implement form checking logic here
        # This is a placeholder implementation
        return None

    async def _check_get_params(self, url):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        vulnerable_params = []

        for param, value in params.items():
            test_value = "' OR '1'='1"
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{param}={test_value}"
            
            async with self.session.get(test_url) as response:
                content = await response.text()
                if "error in your SQL syntax" in content.lower():
                    vulnerable_params.append(param)

        if vulnerable_params:
            return f"Potential SQL injection vulnerability found in GET parameters: {', '.join(vulnerable_params)}"
        return None

    async def get_results(self):
        return self.results

    async def get_training_data(self):
        return self.training_data

    async def get_final_message(self):
        return self.final_message

class AgentSystem:
    def __init__(self, plugin_manager: PluginManager, llm: LLM):
        self.agents: List[Agent] = []
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.session = aiohttp.ClientSession()
        logger.debug("AgentSystem initialized")

    async def create_agent(self, name: str) -> Agent:
        agent = Agent(name, self.plugin_manager, self.llm, self.session)
        self.agents.append(agent)
        logger.debug(f"Created agent: {name}")
        return agent
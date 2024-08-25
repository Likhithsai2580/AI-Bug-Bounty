import threading
from queue import Queue
from typing import List, Dict, Any
from plugin_manager import PluginManager
from llm.llama import LLM
import requests
from bs4 import BeautifulSoup
import json
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, plugin_manager: PluginManager, llm: LLM):
        self.name = name
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.results = {}
        self.training_data = []
        self.final_message = ""
        logger.debug(f"Agent '{name}' initialized")

    def run_analysis(self, prompt: str):
        logger.debug(f"Agent '{self.name}' running analysis")
        self.scan_website(prompt)
        self.analyze_results()

    def scan_website(self, url: str):
        logger.debug(f"Agent '{self.name}' scanning {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            threads = []
            for plugin_name in self.plugin_manager.list_plugins():
                thread = threading.Thread(target=self.run_plugin, args=(plugin_name, url, soup))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            llm_prompt = f"Analyze the following website content for vulnerabilities:\n{soup.prettify()}\n\nProvide a summary of potential vulnerabilities."
            llm_analysis = self.llm.generate(llm_prompt)
            self.results['llm_analysis'] = llm_analysis
            self.training_data.append(llm_analysis)

            logger.debug(f"Agent '{self.name}' completed scanning {url}")
        except Exception as e:
            logger.error(f"Error scanning website {url}: {str(e)}")
            self.results['error'] = str(e)

    def run_plugin(self, plugin_name, url, soup):
        try:
            result = self.plugin_manager.run_plugin(plugin_name, {'url': url, 'content': soup.prettify()})
            self.results[plugin_name] = result
            self.training_data.append(str(result))
        except Exception as e:
            logger.error(f"Error running plugin {plugin_name}: {str(e)}")
            self.results[plugin_name] = {'error': str(e)}

    def analyze_results(self):
        logger.debug(f"Agent '{self.name}' analyzing results")
        try:
            analyzed_results = {}
            for plugin_name, result in self.results.items():
                if isinstance(result, dict) and 'vulnerabilities' in result:
                    analyzed_results[plugin_name] = []
                    for vuln in result['vulnerabilities']:
                        analysis = self.llm.analyze_vulnerability(vuln)
                        analyzed_results[plugin_name].append({
                            'vulnerability': vuln,
                            'analysis': analysis
                        })

            llm_prompt = f"Analyze the following scan results and provide insights:\n{json.dumps(analyzed_results, indent=2)}\n\nProvide a summary of the most critical findings and recommendations."
            final_analysis = self.llm.generate(llm_prompt)
            self.final_message = final_analysis
            self.training_data.append(final_analysis)
            logger.debug(f"Agent '{self.name}' completed analysis")
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            self.results['analysis_error'] = str(e)

    def get_results(self):
        return self.results

    def get_training_data(self):
        return self.training_data

    def get_final_message(self):
        return self.final_message

class AgentSystem:
    def __init__(self, plugin_manager: PluginManager, llm: LLM):
        self.agents: List[Agent] = []
        self.plugin_manager = plugin_manager
        self.llm = llm
        logger.debug("AgentSystem initialized")

    def create_agent(self, name: str) -> Agent:
        agent = Agent(name, self.plugin_manager, self.llm)
        self.agents.append(agent)
        logger.debug(f"Created agent: {name}")
        return agent
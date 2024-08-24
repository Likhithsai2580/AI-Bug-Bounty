import threading
from queue import Queue
from typing import List, Dict, Any
from plugin_manager import PluginManager
from llm.llama import LLM
import requests
from bs4 import BeautifulSoup
import json
import logging

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, plugin_manager: PluginManager, llm: LLM):
        self.name = name
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.task_queue = Queue()
        self.results = {}

    def add_task(self, task: Dict[str, Any]):
        self.task_queue.put(task)

    def run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            self.execute_task(task)
            self.task_queue.task_done()

    def execute_task(self, task: Dict[str, Any]):
        task_type = task.get('type')
        if task_type == 'scan':
            self.scan_website(task['url'])
        elif task_type == 'analyze':
            self.analyze_results(task['results'])
        # Add more task types as needed

    def scan_website(self, url: str):
        logger.info(f"Agent {self.name} scanning {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Run plugins
            for plugin_name in self.plugin_manager.list_plugins():
                plugin_result = self.plugin_manager.run_plugin(plugin_name, {'url': url, 'content': soup.prettify()})
                self.results[plugin_name] = plugin_result

            # Use LLM for additional analysis
            llm_prompt = f"Analyze the following website content for vulnerabilities:\n{soup.prettify()}\n\nProvide a summary of potential vulnerabilities."
            llm_analysis = self.llm.generate(llm_prompt)
            self.results['llm_analysis'] = llm_analysis

        except Exception as e:
            logger.error(f"Error scanning {url}: {str(e)}")
            self.results['error'] = str(e)

    def analyze_results(self, results: Dict[str, Any]):
        logger.info(f"Agent {self.name} analyzing results")
        try:
            # Combine results from scanning and any provided results
            all_results = {**self.results, **results}
            
            # Use LLM to generate insights
            llm_prompt = f"Analyze the following scan results and provide insights:\n{json.dumps(all_results, indent=2)}\n\nProvide a summary of the most critical findings and recommendations."
            analysis = self.llm.generate(llm_prompt)
            
            self.results['final_analysis'] = analysis
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            self.results['analysis_error'] = str(e)

class AgentSystem:
    def __init__(self, plugin_manager: PluginManager, llm: LLM):
        self.agents: List[Agent] = []
        self.plugin_manager = plugin_manager
        self.llm = llm

    def create_agent(self, name: str) -> Agent:
        agent = Agent(name, self.plugin_manager, self.llm)
        self.agents.append(agent)
        return agent

    def start_agents(self):
        threads = []
        for agent in self.agents:
            thread = threading.Thread(target=agent.run)
            thread.start()
            threads.append(thread)
        return threads

    def stop_agents(self):
        for agent in self.agents:
            agent.add_task(None)  # Signal the agent to stop

    def assign_task(self, agent_name: str, task: Dict[str, Any]):
        for agent in self.agents:
            if agent.name == agent_name:
                agent.add_task(task)
                break
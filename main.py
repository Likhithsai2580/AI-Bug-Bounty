import requests
from bs4 import BeautifulSoup
import re
import logging
from llm.llama import LLM
import time
import os
import json
from typing import List, Dict, Tuple
import subprocess
from exploitdb import ExploitDB
from report_generator import generate_report
from plugin_manager import PluginManager
from agent_system import AgentSystem
import asyncio
from notifiers import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_success_rate(vulnerability_type, success):
    global vulnerability_success_rates
    if vulnerability_type not in vulnerability_success_rates:
        vulnerability_success_rates[vulnerability_type] = {'successes': 0, 'attempts': 0}
    vulnerability_success_rates[vulnerability_type]['attempts'] += 1
    if success:
        vulnerability_success_rates[vulnerability_type]['successes'] += 1

vulnerability_success_rates = {}

def scan_website(url, llm, max_iterations=5, rate_limit=5):
    thought_process = ""
    exploitdb = ExploitDB()
    plugin_manager = PluginManager()
    
    with requests.Session() as session:
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for i in range(max_iterations):
            success_rates = json.dumps(vulnerability_success_rates, indent=2)
            prompt = f"""
            Analyze the following website content for vulnerabilities:
            {soup.prettify()}

            Previous thoughts: {thought_process}

            Current vulnerability check success rates:
            {success_rates}

            Think step by step about potential vulnerabilities, considering the success rates of previous checks. Then, provide Python code to check for one or more specific vulnerabilities.
            You can use system commands, Python code, or a combination of both. You have full terminal access and can execute multiple commands.

            If you want to search for exploits in ExploitDB, use the following function:
            search_exploitdb(query: str) -> List[Dict]

            Format your response as follows:
            Thoughts: [Your step-by-step analysis]
            Code: ```python
            [Your Python code here]
            ```
            """
            
            response = llm.generate(prompt)
            
            thoughts, code = extract_thoughts_and_code(response)
            thought_process += f"Iteration {i+1} Thoughts:\n{thoughts}\n"
            
            # Add ExploitDB search functionality to the execution environment
            exec_globals = {
                'os': os,
                'subprocess': subprocess,
                'search_exploitdb': exploitdb.search,
                'run_plugin': plugin_manager.run_plugin
            }
            
            logger.warning("Executing potentially dangerous code. Review before running in a production environment.")
            result = execute_code(code, exec_globals)
            thought_process += f"Iteration {i+1} Code execution result:\n{result}\n"
            
            # Update success rates based on the result
            # This is a simplified example; you'd need to implement logic to determine success
            update_success_rate("example_vulnerability", "vulnerable" in result.lower())
            
            logger.info(f"Iteration {i+1} complete.")
            time.sleep(rate_limit)  # Rate limiting
    
    return thought_process

def extract_thoughts_and_code(response):
    thoughts_match = re.search(r'Thoughts:(.*?)Code:', response, re.DOTALL)
    code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
    
    thoughts = thoughts_match.group(1).strip() if thoughts_match else "No thoughts found."
    code = code_match.group(1).strip() if code_match else "No code found."
    
    return thoughts, code

def execute_code(code, exec_globals):
    try:
        exec(code, exec_globals)
        return exec_globals.get('result', 'No result found')
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return f"Error executing code: {str(e)}"

def train(data_path: str, output_path: str):
    """
    Simulate training process by collecting and preprocessing data.
    This function prepares data that could be used for fine-tuning if we had direct access to the model.
    
    :param data_path: Path to the directory containing training data
    :param output_path: Path to save the preprocessed data
    """
    logger.info("Starting training data preparation...")
    
    # Collect and preprocess data
    training_data = collect_training_data(data_path)
    preprocessed_data = preprocess_data(training_data)
    
    # Save preprocessed data
    with open(output_path, 'w') as f:
        json.dump(preprocessed_data, f, indent=2)
    
    logger.info(f"Training data preparation complete. Saved to {output_path}")
    
    # If we had direct access to the model, we would fine-tune it here
    logger.info("Note: Actual model fine-tuning not implemented due to API limitations.")

def collect_training_data(data_path: str) -> List[Dict[str, str]]:
    """Collect training data from files in the specified directory."""
    training_data = []
    for filename in os.listdir(data_path):
        if filename.endswith('.json'):
            with open(os.path.join(data_path, filename), 'r') as f:
                training_data.extend(json.load(f))
    return training_data

def preprocess_data(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Preprocess the collected data for training."""
    preprocessed_data = []
    for item in data:
        # Example preprocessing steps:
        # 1. Clean HTML content
        cleaned_html = BeautifulSoup(item['html_content'], 'html.parser').prettify()
        # 2. Truncate if too long
        if len(cleaned_html) > 4096:  # Adjust based on model's max token limit
            cleaned_html = cleaned_html[:4096]
        # 3. Format as a prompt-response pair
        preprocessed_item = {
            "prompt": f"Analyze the following website content for vulnerabilities:\n{cleaned_html}\n\nIdentify potential vulnerabilities and explain your reasoning.",
            "response": item['vulnerability_analysis']
        }
        preprocessed_data.append(preprocessed_item)
    return preprocessed_data

async def main():
    llm = LLM()
    plugin_manager = PluginManager()
    agent_system = AgentSystem(plugin_manager, llm)
    notifier = NotificationManager()

    # Create agents
    scanner_agent = agent_system.create_agent("scanner")
    analyzer_agent = agent_system.create_agent("analyzer")

    # Start agents
    agent_threads = agent_system.start_agents()

    # Assign tasks to agents
    target_url = "http://example.com"  # Replace with the target website
    scanner_agent.add_task({"type": "scan", "url": target_url})
    analyzer_agent.add_task({"type": "analyze", "results": {}})

    # Wait for tasks to complete
    for thread in agent_threads:
        thread.join()

    # Stop agents
    agent_system.stop_agents()

    # Generate report
    report_file = "vulnerability_report.pdf"
    generate_report(agent_system.get_results(), report_file)

    logger.info(f"Report generated and saved to {report_file}")

    # Send notification and report via Telegram and Discord
    await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)

if __name__ == "__main__":
    asyncio.run(main())
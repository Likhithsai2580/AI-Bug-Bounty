import threading
import queue
import asyncio
import logging
import re
import json
from llm.llama import LLM
from plugin_manager import PluginManager
from agent_system import AgentSystem, Agent
from notifiers import NotificationManager
from report_generator import generate_report
from vector_db import VectorDB
from model_trainer import ModelTrainer
import subprocess
from colorlog import ColoredFormatter
from monitor import Monitor
from vulnerability_db import VulnerabilityDB

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

def execute_python_code(code):
    try:
        # Create a string buffer to capture print output
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()

        exec(code)

        sys.stdout = old_stdout
        output = redirected_output.getvalue()

        return output, None
    except Exception as e:
        return None, str(e)

async def main():
    logger.debug("Starting main function")
    try:
        logger.debug("Initializing components")
        llm_instance = LLM()
        plugin_manager = PluginManager()
        await plugin_manager.initialize()
        agent_system = AgentSystem(plugin_manager, llm_instance)
        agent = await agent_system.create_agent("main_agent")
        notifier = NotificationManager()
        vector_db = VectorDB(dimension=768)
        vulnerability_db = VulnerabilityDB()
        monitor = Monitor(["https://example.com"])  # Add target URLs to monitor

        target_url = "https://ridewithvia.com"

        # Initial prompt
        prompt = f"Analyze the website {target_url} for vulnerabilities. You have full control of the terminal. You can execute commands, list running processes, and stop processes as needed."

        async with agent:
            analysis_result = await agent.run_analysis(prompt)
            vulnerabilities = await vulnerability_db.search_vulnerabilities(target_url)
            
            report_data = {
                "final_analysis": analysis_result,
                "vulnerabilities": vulnerabilities
            }

            report_file = "vulnerability_report.pdf"
            await generate_report(report_data, report_file)

            logger.info(f"Report generated and saved to {report_file}")

            await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)

        # Start monitoring
        await monitor.start_monitoring()

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(main())
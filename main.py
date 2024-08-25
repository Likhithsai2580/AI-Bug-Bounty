import threading
import queue
import asyncio
import logging
import re
import json
from llm.llama import LLM
from plugin_manager import PluginManager
from agent_system import AgentSystem
from notifiers import NotificationManager
from report_generator import generate_report
from parallel_executor import ParallelExecutor
from vector_db import VectorDB
from model_trainer import ModelTrainer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.debug("Starting main function")
    try:
        llm = LLM()
        plugin_manager = PluginManager()
        agent_system = AgentSystem(plugin_manager, llm)
        notifier = NotificationManager()
        parallel_executor = ParallelExecutor()
        vector_db = VectorDB(dimension=768)  # Adjust dimension based on your embedding size
        training_data = []  # New list to collect training data

        target_url = "https://ridewithvia.com"

        prompt = f"Analyze the website {target_url} for vulnerabilities. Use the available tools and provide a detailed report."

        vulnerabilities = []
        execution_complete = False

        # Create multiple agents
        num_agents = 3  # Adjust based on your needs
        agents = [agent_system.create_agent(f"Agent-{i}") for i in range(num_agents)]

        while not execution_complete:
            threads = []
            for agent in agents:
                thread = threading.Thread(target=agent.run_analysis, args=(prompt,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            for agent in agents:
                vulnerabilities.extend(agent.get_results())
                training_data.extend(agent.get_training_data())

            # Generate a new prompt based on current findings
            current_findings = "\n".join([str(v) for v in vulnerabilities])
            llm_response = llm.generate(f"Based on these findings, what should we investigate next? If you have found vulnerabilities, respond with 'FINAL ANSWER:' followed by a summary. Otherwise, provide Python code to continue the investigation.\n\n{current_findings}")

            if "FINAL ANSWER:" in llm_response:
                execution_complete = True
                final_analysis = llm_response.split("FINAL ANSWER:")[1].strip()
            else:
                # Extract and execute Python code
                code_match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
                if code_match:
                    code = code_match.group(1)
                    try:
                        exec(code)
                    except Exception as e:
                        logger.error(f"Error executing LLM-provided code: {str(e)}")
                prompt = llm.generate(f"Based on the execution results, what should we investigate next?\n\n{current_findings}")

        report_data = {"vulnerabilities": vulnerabilities, "final_analysis": final_analysis}
        report_file = "vulnerability_report.pdf"
        generate_report(report_data, report_file)

        logger.info(f"Report generated and saved to {report_file}")

        await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)
        logger.info("Notification sent. Main function completed.")

        # Save training data
        with open("training_data.json", "w") as f:
            json.dump(training_data, f)
        logger.info("Training data saved to training_data.json")

    except Exception as e:
        logger.error(f"An error occurred in the main function: {str(e)}")
    finally:
        logger.debug("Main function finished execution")

if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(main())
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
        logger.debug("Initializing LLM instance")
        llm_instance = LLM()
        plugin_manager = PluginManager()
        await plugin_manager.initialize()
        agent_system = AgentSystem(plugin_manager, llm_instance)
        agent = await agent_system.create_agent("main_agent")
        notifier = NotificationManager()
        vector_db = VectorDB(dimension=768)
        training_data = []

        target_url = "https://ridewithvia.com"

        # Initial prompt
        prompt = f"Analyze the website {target_url} for vulnerabilities. You have full control of the terminal. You can execute commands, list running processes, and stop processes as needed."

        async with agent:
            while True:
                try:
                    LLM_response = await llm_instance.generate(prompt)
                    
                    if LLM_response is not None:
                        if "FINAL ANSWER:" in LLM_response:
                            final_analysis = LLM_response.split("FINAL ANSWER:")[1].strip()
                            break
                        
                        if "EXECUTE:" in LLM_response:
                            command = LLM_response.split("EXECUTE:")[1].strip()
                            executor_id = await llm_instance.execute_command(command)
                            prompt = f"Command execution started with ID: {executor_id}. What would you like to do next?"
                        elif "GET_RESULT:" in LLM_response:
                            executor_id = LLM_response.split("GET_RESULT:")[1].strip()
                            result = await llm_instance.get_command_result(executor_id)
                            prompt = f"Command result: {result}\nWhat would you like to do next?"
                        elif "STOP_COMMAND:" in LLM_response:
                            executor_id = LLM_response.split("STOP_COMMAND:")[1].strip()
                            last_output = await llm_instance.stop_command(executor_id)
                            prompt = f"Command stopped. Last output: {last_output}\nWhat would you like to do next?"
                        elif "LIST_PROCESSES" in LLM_response:
                            processes = llm_instance.list_running_processes()
                            prompt = f"Running processes: {processes}\nWhat would you like to do next?"
                        elif "INPUT:" in LLM_response:
                            input_parts = LLM_response.split("INPUT:")[1].strip().split("|")
                            executor_id = input_parts[0].strip()
                            input_data = input_parts[1].strip()
                            success = await llm_instance.handle_command_input(executor_id, input_data)
                            prompt = f"Input {'sent successfully' if success else 'failed'}. What would you like to do next?"
                        else:
                            prompt = "Please provide a valid command (EXECUTE, GET_RESULT, STOP_COMMAND, LIST_PROCESSES, or INPUT) or a final analysis."
                    else:
                        logger.error("Failed to generate LLM response")
                except Exception as e:
                    logger.error(f"Error during LLM generation: {str(e)}")

            # After the loop, get results from the agent
            results = await agent.get_results()
            training_data.extend(await agent.get_training_data())
            final_message = await agent.get_final_message()
    except Exception as e:
        logger.error(f"Error during agent execution: {str(e)}")
        raise

    if not final_analysis:
        logger.warning("No vulnerabilities were found after extensive scanning.")
        final_analysis = "No vulnerabilities were detected after thorough investigation. However, this doesn't guarantee the absence of security issues. Consider performing manual testing or using additional specialized tools."

    report_data = {"final_analysis": final_analysis}
    report_file = "vulnerability_report.pdf"
    await generate_report(report_data, report_file)

    logger.info(f"Report generated and saved to {report_file}")

    try:
        await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)
        logger.info("Notification sent. Main function completed.")
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")

    # Save training data
    with open("training_data.json", "w") as f:
        json.dump(training_data, f)
    logger.info("Training data saved to training_data.json")

if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(main())
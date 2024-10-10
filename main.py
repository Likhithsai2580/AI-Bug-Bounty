import asyncio
import traceback
from llm.llama import LLM
from plugin_manager import PluginManager
from agent_system import AgentSystem
from notifiers import NotificationManager
from report_generator import generate_report
from vector_db import VectorDB
from monitor import Monitor
from vulnerability_db import VulnerabilityDB
from colorama import Fore, Style
import logging

# Configure colorful logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log(message, color=Fore.WHITE):
    logger.info(f"{color}{message}{Style.RESET_ALL}")

async def analyze_website(agent_system, target_url, use_llm=True):
    log(f"Analyzing website: {target_url}", Fore.CYAN)
    analysis_result = await agent_system.analyze_website(target_url, use_llm)
    return analysis_result

async def search_vulnerabilities(vulnerability_db, target_url):
    vulnerabilities = await vulnerability_db.search_vulnerabilities(target_url)
    return vulnerabilities or []

async def main():
    log("Initializing AI-Bug-Bounty system", Fore.CYAN)
    agent_system = None
    monitor = None
    try:
        llm_instance = LLM()
        plugin_manager = PluginManager()
        agent_system = AgentSystem(plugin_manager, llm_instance)
        notifier = NotificationManager()
        vulnerability_db = VulnerabilityDB()
        vector_db = VectorDB(768)  # Assuming 768-dimensional vectors
        monitor = Monitor(['https://example.com'], check_interval=3600)

        target_url = "https://ridewithvia.com"  # Replace with your target URL
        log(f"Starting vulnerability scan for {target_url}", Fore.GREEN)

        vulnerabilities_found = False
        retry_count = 0
        max_retries = 5
        while not vulnerabilities_found and retry_count < max_retries:
            try:
                async with agent_system:
                    analysis_result = await analyze_website(agent_system, target_url)
                    log(f"Analysis result: {analysis_result}", Fore.GREEN)

                    if "No vulnerabilities detected" not in analysis_result and "Error during analysis" not in analysis_result:
                        vulnerabilities_found = True
                        try:
                            vulnerabilities = await search_vulnerabilities(vulnerability_db, target_url)
                            log(f"Found {len(vulnerabilities)} vulnerabilities", Fore.YELLOW)
                        except Exception as e:
                            log(f"Error searching vulnerabilities: {str(e)}", Fore.RED)
                            vulnerabilities = []

                        report_data = {
                            "final_analysis": analysis_result,
                            "vulnerabilities": vulnerabilities
                        }

                        report_file = "vulnerability_report.pdf"
                        try:
                            await generate_report(report_data, report_file)
                            log(f"Report generated: {report_file}", Fore.GREEN)
                            await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)
                            log("Notification sent", Fore.GREEN)
                        except Exception as e:
                            log(f"Error generating report: {str(e)}", Fore.RED)
                    else:
                        retry_count += 1
                        log(f"No vulnerabilities found or analysis failed. Retrying ({retry_count}/{max_retries})...", Fore.YELLOW)
                        await asyncio.sleep(60)  # Wait for 1 minute before retrying
            except Exception as e:
                log(f"Error during analysis: {str(e)}", Fore.RED)
                log(traceback.format_exc(), Fore.RED)
                retry_count += 1
                await asyncio.sleep(60)  # Wait for 1 minute before retrying

        if not vulnerabilities_found:
            log("Max retries reached. No vulnerabilities found or analysis failed.", Fore.RED)

    except Exception as e:
        log(f"Error: {str(e)}", Fore.RED)
        log(traceback.format_exc(), Fore.RED)
    finally:
        if monitor:
            await monitor.stop_monitoring()
        if agent_system:
            await agent_system.close()

if __name__ == "__main__":
    asyncio.run(main())
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
import argparse

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
    return vulnerabilities

async def scan_target(agent_system, vulnerability_db, notifier, target_url, mode):
    log(f"Starting vulnerability scan for {target_url}", Fore.GREEN)
    
    while True:
        try:
            async with agent_system:
                analysis_result = await analyze_website(agent_system, target_url)
                log(f"Analysis result: {analysis_result}", Fore.GREEN)

                vulnerabilities = await search_vulnerabilities(vulnerability_db, target_url)
                log(f"Found {len(vulnerabilities)} vulnerabilities", Fore.YELLOW)

                report_data = {
                    "final_analysis": analysis_result,
                    "vulnerabilities": vulnerabilities
                }

                report_file = f"vulnerability_report_{target_url.replace('://', '_').replace('/', '_')}.pdf"
                await generate_report(report_data, report_file)
                log(f"Report generated: {report_file}", Fore.GREEN)
                await notifier.notify(f"Vulnerability scan completed for {target_url}", report_file)
                log("Notification sent", Fore.GREEN)

                if mode != 'monitor':
                    break

                await asyncio.sleep(3600)  # Wait for 1 hour before next scan in monitor mode
        except Exception as e:
            log(f"Error during analysis: {str(e)}", Fore.RED)
            log(traceback.format_exc(), Fore.RED)
            await asyncio.sleep(60)  # Wait for 1 minute before retrying

async def main():
    parser = argparse.ArgumentParser(description="AI-Bug-Bounty Scanner")
    parser.add_argument("urls", nargs="+", help="Target URLs to scan")
    parser.add_argument("--mode", choices=['regular', 'monitor'], default='regular', help="Scanning mode")
    args = parser.parse_args()

    log("Initializing AI-Bug-Bounty system", Fore.CYAN)
    try:
        llm_instance = LLM()
        plugin_manager = PluginManager()
        agent_system = AgentSystem(plugin_manager, llm_instance)
        notifier = NotificationManager()
        vulnerability_db = VulnerabilityDB()
        vector_db = VectorDB(768)  # Assuming 768-dimensional vectors
        monitor = Monitor(args.urls, check_interval=3600, mode=args.mode)

        scan_tasks = [scan_target(agent_system, vulnerability_db, notifier, url, args.mode) for url in args.urls]
        await asyncio.gather(*scan_tasks)

    except Exception as e:
        log(f"Error: {str(e)}", Fore.RED)
        log(traceback.format_exc(), Fore.RED)
    finally:
        await monitor.stop_monitoring()
        await agent_system.close()

if __name__ == "__main__":
    asyncio.run(main())
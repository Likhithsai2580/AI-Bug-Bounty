import asyncio
from typing import List, Optional
import logging
from plugin_manager import PluginManager
from llm.llama import LLM
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs, urljoin
import aiohttp
from rate_limiter import RateLimiter
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Set up colorful logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log(message, color=Fore.WHITE):
    logger.info(f"{color}{message}{Style.RESET_ALL}")

class Agent:
    def __init__(self, name: str, plugin_manager: PluginManager, llm: LLM, session: Optional[aiohttp.ClientSession], rate_limiter: RateLimiter):
        self.name = name
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.session = session
        self.rate_limiter = rate_limiter
        self.results = []

    async def run_analysis(self, url: str, use_llm: bool = True):
        try:
            log(f"Agent {self.name} starting analysis on {url}", Fore.CYAN)
            content = await self._fetch_content(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            self.results = []
            try:
                self.results.extend(await self._check_forms(url, soup))
            except Exception as e:
                log(f"Error checking forms: {str(e)}", Fore.RED)
            
            try:
                get_param_results = await self._check_get_params(url)
                if get_param_results:
                    self.results.extend(get_param_results)
            except Exception as e:
                log(f"Error checking GET parameters: {str(e)}", Fore.RED)
            
            try:
                self.results.extend(await self._check_javascript(content))
            except Exception as e:
                log(f"Error checking JavaScript: {str(e)}", Fore.RED)
            
            try:
                self.results.extend(await self._check_headers(url))
            except Exception as e:
                log(f"Error checking headers: {str(e)}", Fore.RED)

            summary = self._generate_summary(url)

            if use_llm:
                try:
                    llm_analysis = await self.llm.analyze_vulnerability(summary)
                    final_report = f"Analysis for {url}:\n\n{summary}\n\nDetailed Analysis:\n{llm_analysis}"
                except Exception as e:
                    log(f"Error during LLM analysis: {str(e)}", Fore.RED)
                    final_report = f"Analysis for {url}:\n\n{summary}\n\nLLM analysis failed: {str(e)}"
            else:
                final_report = f"Analysis for {url}:\n\n{summary}"

            log(f"Agent {self.name} completed analysis on {url}", Fore.GREEN)
            return final_report

        except Exception as e:
            log(f"Error during analysis by agent {self.name}: {str(e)}", Fore.RED)
            return f"Error during analysis: {str(e)}"

    async def _fetch_content(self, url):
        async with self.session.get(url) as response:
            return await response.text()

    async def _check_forms(self, url, soup):
        forms = soup.find_all('form')
        results = []
        for form in forms:
            result = await self._check_form(url, form)
            if result:
                results.append(result)
        return results

    async def _check_form(self, url, form):
        action = form.get('action')
        method = form.get('method', 'get').lower()
        
        if not action:
            action = url
        else:
            action = urljoin(url, action)
        
        inputs = form.find_all('input')
        for input_field in inputs:
            input_type = input_field.get('type', '').lower()
            input_name = input_field.get('name')
            
            if input_type in ['text', 'password', 'hidden'] and input_name:
                for payload in self.plugin_manager.get_payloads():
                    data = {input_name: payload}
                    try:
                        async with self.rate_limiter:
                            if method == 'post':
                                async with self.session.post(action, data=data) as response:
                                    content = await response.text()
                            else:
                                async with self.session.get(action, params=data) as response:
                                    content = await response.text()
                        
                        if self._check_vulnerability(content, payload):
                            return {
                                "form_action": action,
                                "form_method": method,
                                "vulnerable_param": input_name,
                                "payload": payload,
                                "reason": "Potential vulnerability detected"
                            }
                    except aiohttp.ClientError:
                        continue
        
        return None

    async def _check_get_params(self, url):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        vulnerable_params = []

        for param, value in params.items():
            for payload in self.plugin_manager.get_payloads():
                test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{param}={payload}"
                
                async with self.rate_limiter:
                    async with self.session.get(test_url) as response:
                        content = await response.text()
                        if self._check_vulnerability(content, payload):
                            vulnerable_params.append(param)

        if vulnerable_params:
            return [{"type": "GET Parameter Vulnerability", "reason": f"Potential vulnerability found in GET parameters: {', '.join(vulnerable_params)}"}]
        return []

    async def _check_javascript(self, content):
        js_vulnerabilities = []
        # Check for potential eval() misuse
        if 'eval(' in content:
            js_vulnerabilities.append({
                "type": "Potential eval() misuse",
                "reason": "Use of eval() can lead to code injection vulnerabilities"
            })
        
        # Check for potential DOM-based XSS
        if 'document.write(' in content or 'innerHTML' in content:
            js_vulnerabilities.append({
                "type": "Potential DOM-based XSS",
                "reason": "Unsafe manipulation of DOM elements detected"
            })
        
        # Check for use of deprecated functions
        deprecated_functions = ['escape(', 'unescape(']
        for func in deprecated_functions:
            if func in content:
                js_vulnerabilities.append({
                    "type": f"Use of deprecated function {func}",
                    "reason": f"The {func} function is deprecated and may lead to security issues"
                })
        
        return js_vulnerabilities

    async def _check_headers(self, url):
        header_vulnerabilities = []
        async with self.session.get(url) as response:
            headers = response.headers
            if 'X-XSS-Protection' not in headers:
                header_vulnerabilities.append({
                    "type": "Missing X-XSS-Protection header",
                    "reason": "This header can help prevent XSS attacks in older browsers"
                })
            if 'Strict-Transport-Security' not in headers:
                header_vulnerabilities.append({
                    "type": "Missing HSTS header",
                    "reason": "This header helps enforce HTTPS connections"
                })
            if 'X-Frame-Options' not in headers:
                header_vulnerabilities.append({
                    "type": "Missing X-Frame-Options header",
                    "reason": "This header can prevent clickjacking attacks"
                })
            if 'Content-Security-Policy' not in headers:
                header_vulnerabilities.append({
                    "type": "Missing Content-Security-Policy header",
                    "reason": "This header helps prevent various types of attacks including XSS and data injection"
                })
        return header_vulnerabilities

    def _check_vulnerability(self, content, payload):
        try:
            return payload in content or any(plugin.check_vulnerability(content, payload) for plugin in self.plugin_manager.plugins)
        except Exception as e:
            log(f"Error checking vulnerability: {str(e)}", Fore.RED)
            return False

    def _generate_summary(self, url):
        summary = f"Vulnerability scan summary for {url}:\n"
        if not self.results:
            summary += "No vulnerabilities detected.\n"
        else:
            summary += f"Found {len(self.results)} potential vulnerabilities:\n"
            for result in self.results:
                if isinstance(result, dict):
                    summary += f"- {result['type']}: {result['reason']}\n"
                elif isinstance(result, str):
                    summary += f"- {result}\n"
        return summary

class AgentSystem:
    def __init__(self, plugin_manager: PluginManager, llm: LLM, num_agents: int = 1):
        self.agents: List[Agent] = []
        self.plugin_manager = plugin_manager
        self.llm = llm
        self.session = None
        self.rate_limiter = RateLimiter(rate_limit=10)  # 10 requests per second
        self.create_agents(num_agents)

    def create_agents(self, num_agents: int):
        for i in range(num_agents):
            agent = Agent(f"Agent-{i+1}", self.plugin_manager, self.llm, None, self.rate_limiter)
            self.agents.append(agent)

    async def analyze_website(self, target_url: str, use_llm: bool = True):
        if not self.agents:
            raise ValueError("No agents available for analysis")
        agent = self.agents[0]  # Use the first agent for simplicity
        try:
            async with aiohttp.ClientSession() as session:
                agent.session = session
                return await agent.run_analysis(target_url, use_llm)
        except Exception as e:
            log(f"Error during website analysis: {str(e)}", Fore.RED)
            return f"Error during website analysis: {str(e)}"

    async def close(self):
        pass  # We don't need to close the session here anymore

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
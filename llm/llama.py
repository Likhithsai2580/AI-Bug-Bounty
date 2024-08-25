import logging

logger = logging.getLogger(__name__)

from groq import Groq
import time
from config import GROK_API_KEY
import threading
import hashlib
import json
import os
import re
import uuid
from cachetools import TTLCache
from exploitdb import ExploitDB

class LLM:
    def __init__(self):
        self.client = Groq(api_key=GROK_API_KEY)
        self.messages = [
            {"role": "system", "content": """You are an advanced AI assistant specializing in web vulnerability scanning and analysis. Your task is to identify, analyze, and report potential security vulnerabilities in websites. You have access to various tools and techniques:

1. Network Scanning: Use tools like nmap to perform port scans and service detection.
2. Web Application Analysis: Employ tools such as nikto, sqlmap, and custom Python scripts to identify common web vulnerabilities.
3. Code Analysis: Examine source code, if available, for potential security flaws.
4. Traffic Analysis: Analyze network traffic using tools like Wireshark or tcpdump.
5. Exploitation Techniques: Understand and explain potential exploit methods for discovered vulnerabilities.
6. Reporting: Generate detailed, actionable reports on findings.
7. ExploitDB Search: Use the ExploitDB to find relevant exploits for identified vulnerabilities.
8. ***DONT STOP UNTIL ATLEAST ONE VULNERABILITY IS FOUND***
When providing code or commands:
- Use Python's subprocess module for executing system commands. and you can run tools nmap,nikto etc. if not installed you can install it with apt.
- Implement proper error handling and logging.
- Consider the security implications of your actions and always use ethical hacking practices.
- Provide clear explanations for each step of your analysis.

Your goal is to conduct a thorough security assessment while adhering to best practices in cybersecurity. Always prioritize the most critical vulnerabilities and provide remediation suggestions when possible.

When you've completed your analysis, include 'FINAL ANSWER:' followed by a comprehensive summary of your findings and recommendations."""}
        ]
        self.lock = threading.Lock()
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1-hour TTL
        self.exploitdb = ExploitDB()

    def generate(self, prompt, model="llama-3.1-70b-versatile", max_retries=100, retry_delay=60):
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]

        logger.info(f"Generating response using model: {model}")
        with self.lock:
            self.messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=self.messages,
                    model=model
                )
                response = chat_completion.choices[0].message.content
                with self.lock:
                    self.messages.append({"role": "assistant", "content": response})
                    self.cache[cache_key] = response
                return response
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Returning None.")
                    return None

    def chain_of_thought(self, prompt, max_iterations=5):
        self.messages.append({"role": "user", "content": prompt})
        for i in range(max_iterations):
            response = self.generate(f"Iteration {i + 1}: {prompt}")
            self.messages.append({"role": "assistant", "content": response})
            
            code_match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                executor_id = f"exec_{uuid.uuid4().hex[:8]}"
                yield executor_id, code
            
            if "FINAL ANSWER:" in response:
                break
        
        return self.messages[-1]["content"]

    def search_exploits(self, vulnerability):
        exploits = self.exploitdb.search(vulnerability)
        if exploits:
            return f"Relevant exploits found for {vulnerability}:\n" + "\n".join([f"- {e['title']} (ID: {e['id']})" for e in exploits[:5]])
        else:
            return f"No specific exploits found for {vulnerability} in the ExploitDB."

    def analyze_vulnerability(self, vulnerability):
        exploit_info = self.search_exploits(vulnerability)
        analysis_prompt = f"Analyze the following vulnerability and provide insights based on the available exploit information:\n\nVulnerability: {vulnerability}\n\nExploit Information:\n{exploit_info}\n\nProvide a detailed analysis, including potential impact, exploitation difficulty, and recommended mitigation steps."
        return self.generate(analysis_prompt)
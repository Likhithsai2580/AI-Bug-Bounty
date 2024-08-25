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
import asyncio

class LLM:
    def __init__(self):
        self.client = Groq(api_key=GROK_API_KEY)

    async def generate(self, prompt):
        logger.debug(f"Generating response for prompt: {prompt[:50]}...")
        try:
            loop = asyncio.get_running_loop()
            logger.debug("Creating chat completion")
            chat_completion = await loop.run_in_executor(None, lambda: self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt+" stay on topic of finding vulnerabilities in the target website. Whenever you want to install a tool install it by subprocess module apt install",
                    }
                ],
                model="llama3-groq-70b-8192-tool-use-preview",
                max_tokens=1024,
            ))
            logger.debug(f"LLM response received: {chat_completion.choices[0].message.content[:50]}...")
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
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
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug("started importing llm initiated")
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
import concurrent.futures
import ast
import subprocess
import psutil
from typing import Dict, Any

def is_safe_code(code):
    logger.debug(f"Checking if code is safe: {code[:50]}...")
    try:
        ast.parse(code)
        logger.debug("Code is safe")
        return True
    except SyntaxError:
        logger.debug("Code is not safe")
        return False

class ParallelExecutor:
    def __init__(self):
        logger.debug("Initializing ParallelExecutor")
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.running_tasks: Dict[str, Dict[str, Any]] = {}

    async def execute(self, code, executor_id=None):
        logger.debug("Starting execute method")
        if executor_id is None:
            logger.debug("Executor ID is None, generating new ID")
            executor_id = f"exec_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Executing code with ID: {executor_id}")
        logger.debug(f"Code to execute: {code[:50]}...")
        
        if not is_safe_code(code):
            logger.error(f"Syntax error in code: {code[:50]}...")
            return executor_id, SyntaxError("Invalid code syntax")
        
        logger.debug("Creating subprocess")
        process = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )
        logger.debug("Subprocess created")
        self.running_tasks[executor_id] = {
            "process": process,
            "start_time": time.time(),
            "last_output": ""
        }
        logger.debug("Returning executor ID and None")
        return executor_id, None

    async def get_result(self, executor_id):
        logger.debug("Starting get_result method")
        if executor_id in self.running_tasks:
            task = self.running_tasks[executor_id]
            process = task["process"]
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                del self.running_tasks[executor_id]
                logger.debug("Returning result")
                return stdout.decode() if stdout else stderr.decode()
            else:
                logger.debug("Process is still running")
                return None
        logger.debug("Executor ID not found")
        return None

    async def stop_execution(self, executor_id):
        if executor_id in self.running_tasks:
            task = self.running_tasks[executor_id]
            process = task["process"]
            process.terminate()
            await process.wait()
            stdout, stderr = await process.communicate()
            last_output = stdout.decode() if stdout else stderr.decode()
            del self.running_tasks[executor_id]
            logger.debug("Returning last output")
            return last_output
        logger.debug("Executor ID not found")
        return None

    def list_processes(self):
        logger.debug("Starting list_processes method")
        return [
            {
                "id": executor_id,
                "runtime": time.time() - task["start_time"],
                "command": f"Process {task['process'].pid}"
            }
            for executor_id, task in self.running_tasks.items()
        ]

    async def handle_input(self, executor_id, input_data):
        if executor_id in self.running_tasks:
            task = self.running_tasks[executor_id]
            process = task["process"]
            process.stdin.write(input_data.encode() + b'\n')
            await process.stdin.drain()
            logger.debug("Input handled")
            return True
        logger.debug("Executor ID not found")
        return False

class LLM:
    def __init__(self):
        self.client = Groq(api_key=GROK_API_KEY)
        self.parallel_executor = ParallelExecutor()
        self.exploitdb = ExploitDB()
        logger.debug("LLM initialized")

    async def generate(self, prompt):
        logger.debug(f"Generating response for prompt: {prompt[:50]}...")
        try:
            loop = asyncio.get_running_loop()
            logger.debug("Creating chat completion")
            chat_completion = await loop.run_in_executor(None, lambda: self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
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

    async def execute_command(self, command):
        logger.debug(f"Executing command: {command[:50]}...")
        executor_id, _ = await self.parallel_executor.execute(command)
        return executor_id

    async def get_command_result(self, executor_id):
        logger.debug(f"Getting command result for executor ID: {executor_id}")
        result = await self.parallel_executor.get_result(executor_id)
        logger.debug(f"Command result: {result[:50]}...")
        return result

    async def stop_command(self, executor_id):
        logger.debug(f"Stopping command for executor ID: {executor_id}")
        result = await self.parallel_executor.stop_execution(executor_id)
        logger.debug(f"Command stopped, result: {result[:50]}...")
        return result

    def list_running_processes(self):
        logger.debug("Listing running processes")
        return self.parallel_executor.list_processes()

    async def handle_command_input(self, executor_id, input_data):
        logger.debug(f"Handling input for executor ID: {executor_id}")
        return await self.parallel_executor.handle_input(executor_id, input_data)

    def chain_of_thought(self, prompt, max_iterations=5):
        logger.debug(f"Starting chain of thought with prompt: {prompt[:50]}...")
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
        logger.debug(f"Searching exploits for vulnerability: {vulnerability[:50]}...")
        if hasattr(self, 'exploitdb') and callable(getattr(self, 'exploitdb', None)):
            exploits = self.exploitdb(vulnerability)
            if exploits:
                return f"Relevant exploits found for {vulnerability}:\n" + "\n".join([f"- {e['title']} (ID: {e['id']})" for e in exploits[:5]])
        return f"No specific exploits found for {vulnerability} in the ExploitDB."

    def analyze_vulnerability(self, vulnerability):
        logger.debug(f"Analyzing vulnerability: {vulnerability[:50]}...")
        exploit_info = self.search_exploits(vulnerability)
        analysis_prompt = f"Analyze the following vulnerability and provide insights based on the available exploit information:\n\nVulnerability: {vulnerability}\n\nExploit Information:\n{exploit_info}\n\nProvide a detailed analysis, including potential impact, exploitation difficulty, and recommended mitigation steps."
        return self.generate(analysis_prompt)
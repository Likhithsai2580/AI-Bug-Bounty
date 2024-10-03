import asyncio
import concurrent.futures
import uuid
import logging
import ast
import subprocess
import time
import psutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

def is_safe_code(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

class ParallelExecutor:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.running_tasks: Dict[str, Dict[str, Any]] = {}

    async def execute(self, code, executor_id=None):
        if executor_id is None:
            executor_id = f"exec_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Executing code with ID: {executor_id}")
        logger.debug(f"Code to execute: {code[:50]}...")
        
        if not is_safe_code(code):
            logger.error(f"Syntax error in code: {code[:50]}...")
            return executor_id, SyntaxError("Invalid code syntax")
        
        process = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )
        
        self.running_tasks[executor_id] = {
            "process": process,
            "start_time": time.time(),
            "last_output": ""
        }
        
        return executor_id, None

    async def get_result(self, executor_id):
        if executor_id in self.running_tasks:
            task = self.running_tasks[executor_id]
            process = task["process"]
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                del self.running_tasks[executor_id]
                return stdout.decode() if stdout else stderr.decode()
            else:
                return None
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
            return last_output
        return None

    def list_processes(self):
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
            return True
        return False
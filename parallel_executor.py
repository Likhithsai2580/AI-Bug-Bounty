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
    logger.debug(f"Checking if code is safe: {code[:50]}...")
    try:
        ast.parse(code)
        logger.debug("Code parsed successfully")
        return True
    except SyntaxError:
        logger.debug("SyntaxError detected in code")
        return False

class ParallelExecutor:
    def __init__(self):
        logger.debug("Initializing ParallelExecutor")
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        logger.debug("ParallelExecutor initialized")

    async def execute(self, code, executor_id=None):
        logger.debug("Entering execute method")
        if executor_id is None:
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
        logger.debug(f"Subprocess created with PID: {process.pid}")
        
        self.running_tasks[executor_id] = {
            "process": process,
            "start_time": time.time(),
            "last_output": ""
        }
        logger.debug(f"Task added to running_tasks: {executor_id}")
        
        logger.debug("Exiting execute method")
        return executor_id, None

    async def get_result(self, executor_id):
        logger.debug(f"Getting result for executor_id: {executor_id}")
        if executor_id in self.running_tasks:
            logger.debug(f"Found task for executor_id: {executor_id}")
            task = self.running_tasks[executor_id]
            process = task["process"]
            if process.returncode is not None:
                logger.debug("Process has completed")
                stdout, stderr = await process.communicate()
                del self.running_tasks[executor_id]
                logger.debug(f"Removed task from running_tasks: {executor_id}")
                return stdout.decode() if stdout else stderr.decode()
            else:
                logger.debug("Process is still running")
                return None
        logger.debug(f"No task found for executor_id: {executor_id}")
        return None

    async def stop_execution(self, executor_id):
        logger.debug(f"Stopping execution for executor_id: {executor_id}")
        if executor_id in self.running_tasks:
            logger.debug(f"Found task for executor_id: {executor_id}")
            task = self.running_tasks[executor_id]
            process = task["process"]
            logger.debug(f"Terminating process with PID: {process.pid}")
            process.terminate()
            await process.wait()
            logger.debug("Process terminated")
            stdout, stderr = await process.communicate()
            last_output = stdout.decode() if stdout else stderr.decode()
            del self.running_tasks[executor_id]
            logger.debug(f"Removed task from running_tasks: {executor_id}")
            return last_output
        logger.debug(f"No task found for executor_id: {executor_id}")
        return None

    def list_processes(self):
        logger.debug("Listing all running processes")
        processes = [
            {
                "id": executor_id,
                "runtime": time.time() - task["start_time"],
                "command": f"Process {task['process'].pid}"
            }
            for executor_id, task in self.running_tasks.items()
        ]
        logger.debug(f"Found {len(processes)} running processes")
        return processes

    async def handle_input(self, executor_id, input_data):
        logger.debug(f"Handling input for executor_id: {executor_id}")
        if executor_id in self.running_tasks:
            logger.debug(f"Found task for executor_id: {executor_id}")
            task = self.running_tasks[executor_id]
            process = task["process"]
            logger.debug(f"Writing input to process stdin: {input_data}")
            process.stdin.write(input_data.encode() + b'\n')
            await process.stdin.drain()
            logger.debug("Input written and drained")
            return True
        logger.debug(f"No task found for executor_id: {executor_id}")
        return False
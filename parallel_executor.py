import asyncio
import concurrent.futures
import uuid
import logging
import ast

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
        self.running_tasks = {}

    async def execute(self, code, executor_id=None):
        if executor_id is None:
            executor_id = f"exec_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Executing code with ID: {executor_id}")
        logger.debug(f"Code to execute: {code[:50]}...")
        
        if not is_safe_code(code):
            logger.error(f"Syntax error in code: {code[:50]}...")
            return executor_id, SyntaxError("Invalid code syntax")
        
        loop = asyncio.get_running_loop()
        try:
            logger.debug(f"Starting execution for {executor_id}")
            result = await loop.run_in_executor(self.executor, exec, code, globals())
            self.running_tasks[executor_id] = result
            logger.debug(f"Execution completed for {executor_id}")
            return executor_id, result
        except SyntaxError as e:
            logger.error(f"Syntax error in code for {executor_id}: {str(e)}")
            return executor_id, e
        except Exception as e:
            logger.error(f"Error during execution of {executor_id}: {str(e)}", exc_info=True)
            return executor_id, e

    async def get_result(self, executor_id):
        if executor_id in self.running_tasks:
            future = self.running_tasks[executor_id]
            try:
                result = await asyncio.wait_for(future, timeout=1.0)
                del self.running_tasks[executor_id]
                return result
            except asyncio.TimeoutError:
                return None
        return None

    async def stop_execution(self, executor_id):
        if executor_id in self.running_tasks:
            future = self.running_tasks[executor_id]
            future.cancel()
            del self.running_tasks[executor_id]
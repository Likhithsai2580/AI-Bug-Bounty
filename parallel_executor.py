import concurrent.futures
import uuid

class ParallelExecutor:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.running_tasks = {}

    def execute(self, code, executor_id=None):
        if executor_id is None:
            executor_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        future = self.executor.submit(exec, code, globals())
        self.running_tasks[executor_id] = future
        return executor_id

    def get_result(self, executor_id):
        if executor_id in self.running_tasks:
            future = self.running_tasks[executor_id]
            if future.done():
                del self.running_tasks[executor_id]
                return future.result()
        return None

    def stop_execution(self, executor_id):
        if executor_id in self.running_tasks:
            future = self.running_tasks[executor_id]
            future.cancel()
            del self.running_tasks[executor_id]
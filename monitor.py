import asyncio
import aiohttp
from typing import List, Dict
import time
import logging

logger = logging.getLogger(__name__)

class Monitor:
    def __init__(self, targets: List[str], check_interval: int = 3600):
        self.targets = targets
        self.check_interval = check_interval
        self.session = aiohttp.ClientSession()

    async def start_monitoring(self):
        while True:
            tasks = [self.check_target(target) for target in self.targets]
            results = await asyncio.gather(*tasks)
            self.process_results(results)
            await asyncio.sleep(self.check_interval)

    async def check_target(self, target: str) -> Dict:
        try:
            start_time = time.time()
            async with self.session.get(target) as response:
                content = await response.text()
                response_time = time.time() - start_time
                return {
                    "target": target,
                    "status": response.status,
                    "response_time": response_time,
                    "content_length": len(content)
                }
        except Exception as e:
            logger.error(f"Error checking {target}: {str(e)}")
            return {"target": target, "error": str(e)}

    def process_results(self, results: List[Dict]):
        for result in results:
            if "error" in result:
                logger.warning(f"Target {result['target']} is unreachable: {result['error']}")
            else:
                logger.info(f"Target {result['target']}: Status {result['status']}, "
                            f"Response Time {result['response_time']:.2f}s, "
                            f"Content Length {result['content_length']} bytes")

    async def stop_monitoring(self):
        await self.session.close()
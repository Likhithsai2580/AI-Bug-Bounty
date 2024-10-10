import asyncio
import aiohttp
from typing import List, Dict
import time
import logging

logger = logging.getLogger(__name__)

class Monitor:
    def __init__(self, targets: List[str], check_interval: int = 3600):
        logger.debug(f"Initializing Monitor with targets: {targets} and check_interval: {check_interval}")
        self.targets = targets
        self.check_interval = check_interval
        self.session = aiohttp.ClientSession()
        logger.debug("Monitor initialized")

    async def start_monitoring(self):
        logger.debug("Starting monitoring loop")
        while True:
            logger.debug(f"Creating tasks for targets: {self.targets}")
            tasks = [self.check_target(target) for target in self.targets]
            logger.debug("Gathering results from tasks")
            results = await asyncio.gather(*tasks)
            logger.debug("Processing results")
            self.process_results(results)
            logger.debug(f"Sleeping for {self.check_interval} seconds")
            await asyncio.sleep(self.check_interval)

    async def check_target(self, target: str) -> Dict:
        logger.debug(f"Checking target: {target}")
        try:
            start_time = time.time()
            logger.debug(f"Sending GET request to {target}")
            async with self.session.get(target) as response:
                logger.debug(f"Received response from {target}")
                content = await response.text()
                response_time = time.time() - start_time
                logger.debug(f"Response time for {target}: {response_time:.2f}s")
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
        logger.debug(f"Processing {len(results)} results")
        for result in results:
            if "error" in result:
                logger.warning(f"Target {result['target']} is unreachable: {result['error']}")
            else:
                logger.info(f"Target {result['target']}: Status {result['status']}, "
                            f"Response Time {result['response_time']:.2f}s, "
                            f"Content Length {result['content_length']} bytes")
        logger.debug("Finished processing results")

    async def stop_monitoring(self):
        logger.debug("Stopping monitoring")
        await self.session.close()
        logger.debug("Monitoring stopped")
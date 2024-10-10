import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, rate_limit: int, time_period: float = 1.0):
        logger.debug(f"Initializing RateLimiter with rate_limit={rate_limit}, time_period={time_period}")
        self.rate_limit = rate_limit
        self.time_period = time_period
        self.tokens = rate_limit
        self.last_refill = time.time()
        logger.debug(f"RateLimiter initialized. Initial tokens: {self.tokens}")

    async def acquire(self):
        logger.debug("Entering acquire method")
        while True:
            current_time = time.time()
            time_passed = current_time - self.last_refill
            logger.debug(f"Time passed since last refill: {time_passed}")
            
            self.tokens += time_passed * (self.rate_limit / self.time_period)
            self.tokens = min(self.tokens, self.rate_limit)
            logger.debug(f"Tokens after refill: {self.tokens}")
            
            self.last_refill = current_time
            logger.debug(f"Last refill time updated to: {self.last_refill}")

            if self.tokens >= 1:
                self.tokens -= 1
                logger.debug(f"Token acquired. Remaining tokens: {self.tokens}")
                return
            else:
                logger.debug("No tokens available. Waiting...")
                await asyncio.sleep(0.1)

import asyncio
import time

class RateLimiter:
    def __init__(self, rate_limit: int, time_period: float = 1.0):
        self.rate_limit = rate_limit
        self.time_period = time_period
        self.tokens = rate_limit
        self.last_refill = time.time()

    async def acquire(self):
        while True:
            current_time = time.time()
            time_passed = current_time - self.last_refill
            self.tokens += time_passed * (self.rate_limit / self.time_period)
            self.tokens = min(self.tokens, self.rate_limit)
            self.last_refill = current_time

            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                await asyncio.sleep(0.1)

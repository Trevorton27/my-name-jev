from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 30.0
    retryable_status_codes: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    def delay(self, attempt: int) -> float:
        return min(self.backoff_base * (2 ** attempt), self.backoff_max)


def sync_retry(config: RetryConfig, attempt: int) -> None:
    time.sleep(config.delay(attempt))


async def async_retry(config: RetryConfig, attempt: int) -> None:
    await asyncio.sleep(config.delay(attempt))

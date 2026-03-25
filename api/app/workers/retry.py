"""Reusable async retry with exponential backoff."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    label: str = "operation",
) -> T:
    """Call *fn* with exponential backoff on failure.

    Args:
        fn: Zero-arg async callable to retry.
        max_retries: Number of retry attempts after the initial call.
        base_delay: Initial delay in seconds (doubles each retry).
        max_delay: Cap on the delay between retries.
        label: Human-readable label for log messages.

    Returns:
        The return value of *fn* on success.

    Raises:
        The last exception if all attempts fail.
    """
    last_exc: BaseException | None = None

    for attempt in range(1, max_retries + 2):  # 1 initial + max_retries
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if attempt > max_retries:
                logger.error(f"{label}: failed after {max_retries + 1} attempts — {e}")
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                f"{label}: attempt {attempt} failed ({type(e).__name__}: {e}), "
                f"retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    # Should never reach here, but satisfy the type checker
    raise last_exc  # type: ignore[misc]


__all__ = ["retry_with_backoff"]

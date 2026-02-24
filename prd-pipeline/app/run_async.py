"""Run async code from sync Streamlit context without blocking the main thread."""
import asyncio
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


def run_async(coro: object) -> Any:
    """Run an async coroutine from sync code via a thread pool. Returns the result."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.exception("Async task failed: %s", e)
        raise
    finally:
        loop.close()


def run_async_in_executor(coro: object) -> Future[Any]:
    """Submit async coroutine to run in executor. Returns a Future. Use from Streamlit callback."""
    def _run() -> Any:
        return run_async(coro)

    return _executor.submit(_run)

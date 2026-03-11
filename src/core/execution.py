import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)

from typing import Any

def execute_query_with_timeout(
    query_engine: Any,
    question: str,
    timeout: float,
    rate_limit_interval: float = 0.0
) -> str:
    """
    Executes a RAG query with timeout and basic thread pool management.
    """
    if rate_limit_interval > 0:
        time.sleep(rate_limit_interval)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(query_engine.query, question)
            response = future.result(timeout=timeout)

        return str(response)

    except FuturesTimeoutError:
        logger.exception("RAG Query timed out after %s seconds", timeout)
        msg = "Query execution timed out"
        raise RuntimeError(msg) from None
    except Exception as e:
        logger.exception("LlamaIndex query failed: %s", e.__class__.__name__)
        msg = f"Query execution failed: {e}"
        raise RuntimeError(msg) from e

import time

def rate_limit_wait(last_call_time: float, min_interval: float) -> float:
    """
    Simple blocking rate limiter.
    Returns the new last_call_time.
    """
    current = time.time()
    elapsed = current - last_call_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    return time.time()

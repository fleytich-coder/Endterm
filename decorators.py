import functools
import logging
import time

logger = logging.getLogger(__name__)


def log_call(func):


    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("Calling %s args=%s kwargs=%s", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.debug("Finished %s -> %r", func.__name__, result)
        return result

    return wrapper


def measure_time_sync(func):


    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("Function %s finished in %.4f seconds", func.__name__, elapsed)
        return result, elapsed

    return wrapper

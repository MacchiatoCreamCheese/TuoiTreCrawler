"""
Error handling utilities for the TuoiTre crawler
Includes retry logic, graceful degradation, and error recovery
"""

import logging
import time
import functools
from typing import Callable, Any, Optional, Tuple, Type
from requests.exceptions import RequestException, Timeout, ConnectionError

from .exceptions import (
    CrawlerException,
    NetworkError,
    RateLimitError
)

logger = logging.getLogger('TuoiTreCrawler.ErrorHandler')


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function on specific exceptions

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def handle_network_error(error: Exception, url: str = None) -> NetworkError:
    """
    Convert various network errors to NetworkError

    Args:
        error: Original exception
        url: URL that caused the error

    Returns:
        NetworkError instance
    """
    if isinstance(error, Timeout):
        return NetworkError(f"Request timeout for {url}", url=url)
    elif isinstance(error, ConnectionError):
        return NetworkError(f"Connection error for {url}", url=url)
    elif isinstance(error, RequestException):
        return NetworkError(f"Request failed for {url}: {error}", url=url)
    else:
        return NetworkError(f"Network error for {url}: {error}", url=url)



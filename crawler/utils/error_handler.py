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


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    error_msg: str = None,
    raise_on_error: bool = False,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling and optional default value

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default: Default value to return on error
        error_msg: Custom error message to log
        raise_on_error: Whether to re-raise the exception
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        msg = error_msg or f"Error executing {func.__name__}"
        logger.error(f"{msg}: {e}", exc_info=True)

        if raise_on_error:
            raise

        return default


class ErrorAggregator:
    """
    Aggregates errors during crawling for reporting
    """
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.error_counts = {}

    def add_error(self, error: Exception, context: str = None):
        """
        Add an error to the aggregator

        Args:
            error: Exception that occurred
            context: Additional context about where the error occurred
        """
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': time.time()
        }
        self.errors.append(error_info)

        # Update error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        logger.error(f"Error in {context}: {error}")

    def add_warning(self, message: str, context: str = None):
        """
        Add a warning to the aggregator

        Args:
            message: Warning message
            context: Additional context
        """
        warning_info = {
            'message': message,
            'context': context,
            'timestamp': time.time()
        }
        self.warnings.append(warning_info)
        logger.warning(f"Warning in {context}: {message}")

    def has_errors(self) -> bool:
        """Check if any errors were recorded"""
        return len(self.errors) > 0

    def get_summary(self) -> dict:
        """
        Get summary of all errors and warnings

        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'error_counts': self.error_counts,
            'errors': self.errors,
            'warnings': self.warnings
        }

    def print_summary(self):
        """Print error summary to log"""
        if not self.has_errors() and not self.warnings:
            logger.info("No errors or warnings recorded")
            return

        logger.info("="*60)
        logger.info("Error Summary")
        logger.info("="*60)
        logger.info(f"Total errors: {len(self.errors)}")
        logger.info(f"Total warnings: {len(self.warnings)}")

        if self.error_counts:
            logger.info("\nError breakdown:")
            for error_type, count in self.error_counts.items():
                logger.info(f"  {error_type}: {count}")

        logger.info("="*60)


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


def should_retry(error: Exception) -> bool:
    """
    Determine if an error is retryable

    Args:
        error: Exception to check

    Returns:
        True if the error should trigger a retry
    """
    # Network errors are usually retryable
    if isinstance(error, (NetworkError, Timeout, ConnectionError)):
        return True

    # Rate limit errors should be retried after delay
    if isinstance(error, RateLimitError):
        return True

    # Other exceptions should not be retried by default
    return False


def get_retry_delay(error: Exception, attempt: int, base_delay: float = 1.0) -> float:
    """
    Calculate retry delay based on error type and attempt number

    Args:
        error: Exception that occurred
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds

    Returns:
        Delay in seconds before retry
    """
    if isinstance(error, RateLimitError) and error.retry_after:
        return error.retry_after

    # Exponential backoff
    return base_delay * (2 ** attempt)

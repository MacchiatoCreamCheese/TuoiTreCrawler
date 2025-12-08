"""
Logging utilities for the TuoiTre crawler
Provides consistent logging across all modules
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class CrawlerLogger:
    """
    Custom logger wrapper for the crawler with additional utilities
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: str = 'INFO',
        console_output: bool = True
    ):
        """
        Initialize logger

        Args:
            name: Logger name
            log_file: Path to log file (optional)
            level: Logging level
            console_output: Whether to output to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler
            if console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, level.upper()))
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)

            # File handler
            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, level.upper()))
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, **kwargs)

# Convenience function for module-level logging
def create_module_logger(module_name: str, level: str = 'INFO') -> CrawlerLogger:
    """
    Create a logger for a specific module

    Args:
        module_name: Name of the module
        level: Logging level

    Returns:
        CrawlerLogger instance
    """
    logger_name = f"TuoiTreCrawler.{module_name}"
    return CrawlerLogger(logger_name, level=level, console_output=False)

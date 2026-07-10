"""
Logger module - Configures application-wide logging.
"""

import logging
import logging.handlers
import os
import json
from pathlib import Path
from typing import Optional


class Logger:
    """
    Handles application logging configuration and management.
    
    This class provides a singleton logger instance that logs to both
    file and console with configurable levels and formatting.
    """

    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> 'Logger':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the logger."""
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """
        Set up the logger with file and console handlers.
        
        Reads configuration from settings.json and sets up appropriate
        logging levels, formatters, and handlers.
        """
        self._logger = logging.getLogger('CDRS')
        self._logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        log_file = log_dir / 'cdrs.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self._logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)

        self._logger.info("Logger initialized successfully")

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.
        
        Returns:
            logging.Logger: The configured logger instance.
        """
        if self._logger is None:
            self._setup_logger()
        return self._logger

    def debug(self, message: str) -> None:
        """Log a debug message."""
        if self._logger:
            self._logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        if self._logger:
            self._logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        if self._logger:
            self._logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message."""
        if self._logger:
            self._logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        if self._logger:
            self._logger.critical(message)


def get_logger() -> logging.Logger:
    """
    Convenience function to get the logger instance.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    return Logger().get_logger()

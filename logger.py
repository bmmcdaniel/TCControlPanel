"""
logger.py - Logging configuration and functions for Torchcrawl GM Control Panel

Functions:
- setup_logging() -> None: Initialize logging configuration
- log_debug(message: str) -> None: Log debug message
- log_info(message: str) -> None: Log info message
- log_warning(message: str) -> None: Log warning message
- log_error(message: str) -> None: Log error message

Classes: None
"""

import logging
import os
from pathlib import Path


def setup_logging() -> None:
    r"""
    Initialize logging configuration.
    
    Creates logs directory if it doesn't exist and configures logging to:
    - Write to \logs\TCControlPanel.log
    - Use UTF-8 encoding
    - Append to existing log file
    - Format: timestamp - level - message
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_file = logs_dir / "TCControlPanel.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a')
        ]
    )
    
    # Log startup
    logging.info("="*60)
    logging.info("Torchcrawl GM Control Panel - Application Started")
    logging.info("="*60)


def log_debug(message: str) -> None:
    """
    Log debug message.
    
    Args:
        message: Message to log
    """
    logging.debug(message)


def log_info(message: str) -> None:
    """
    Log info message.
    
    Args:
        message: Message to log
    """
    logging.info(message)


def log_warning(message: str) -> None:
    """
    Log warning message.
    
    Args:
        message: Message to log
    """
    logging.warning(message)


def log_error(message: str) -> None:
    """
    Log error message.
    
    Args:
        message: Message to log
    """
    logging.error(message)

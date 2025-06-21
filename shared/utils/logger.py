"""
Logger utilities for Bella's Reef project.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The logger name
        level: Optional logging level (defaults to INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    # Only add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 
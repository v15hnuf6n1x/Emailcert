import logging
import os
from typing import Optional

from .constants import DEFAULT_LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger for the certgen module.

    Args:
        name: Logger name (typically __name__).
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
               If None, reads from CERT_LOG_LEVEL env var, defaults to INFO.

    Returns:
        Configured logger instance.
    """
    if level is None:
        # Try to load env var, fallback to constant
        level = os.getenv("CERT_LOG_LEVEL", DEFAULT_LOG_LEVEL)

    # Normalize level
    level = level.upper() if isinstance(level, str) else DEFAULT_LOG_LEVEL
    numeric_level = getattr(logging, level, logging.INFO)

    logger = logging.getLogger(name)

    # Avoid duplicate handlers on re-invocation
    if logger.handlers:
        logger.setLevel(numeric_level)
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(numeric_level)
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    return logger


# Default module logger
logger = setup_logger("emailcert.certgen")

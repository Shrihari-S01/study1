"""
Application logging configuration.
"""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import get_settings


# ==========================================================
# Settings
# ==========================================================

settings = get_settings()

LOG_DIR = settings.log_dir

LOG_FILE = LOG_DIR / "auction_ai.log"


# ==========================================================
# Logger Configuration
# ==========================================================

def configure_logging() -> None:
    """
    Configure application logging.
    """

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(settings.log_level)

    formatter = logging.Formatter(

        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),

        datefmt="%Y-%m-%d %H:%M:%S",

    )

    # ======================================================
    # Console Handler
    # ======================================================

    console_handler = logging.StreamHandler()

    console_handler.setLevel(settings.log_level)

    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # ======================================================
    # File Handler
    # ======================================================

    file_handler = TimedRotatingFileHandler(

        filename=LOG_FILE,

        when="midnight",

        interval=1,

        backupCount=30,

        encoding="utf-8",

    )

    file_handler.setLevel(settings.log_level)

    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)


# ==========================================================
# Logger Factory
# ==========================================================

def get_logger(
    name: str,
) -> logging.Logger:
    """
    Return configured logger.

    Parameters
    ----------
    name : str
        Module name.

    Returns
    -------
    logging.Logger
    """

    configure_logging()

    return logging.getLogger(name)
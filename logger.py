"""Logging to stdout only (the hosting platform collects it). No log files are
written, and transcripts are never logged."""

import logging
import os

logging.basicConfig(
    level=os.getenv("MINBAR_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("minbar")


def log_error(message: str):
    logger.error(message)


def log_info(message: str):
    logger.info(message)

"""Logging configuration for complete execution traces."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def configure_logging(logs_directory: Path) -> tuple[logging.Logger, Path]:
    """Create a unique timestamped log and configure the application logger."""
    logs_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S_%f")
    log_path = logs_directory / f"markdown_merge_{timestamp}.log"

    logger = logging.getLogger("markdown_merge")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(file_handler)

    logger.debug("Logging initialized: %s", log_path)
    return logger, log_path

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(
    *,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    app_name: str = "app",
    logs_dir: Optional[Path] = None,
) -> None:
    """Configure Loguru sinks for console and file logging."""

    logger.remove()

    logger.add(
        sys.stderr,
        level=console_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    logs_directory = logs_dir or Path("logs")
    logs_directory.mkdir(parents=True, exist_ok=True)

    logger.add(
        logs_directory / f"{app_name}_{{time:YYYYMMDD}}.log",
        level=file_level,
        rotation="12:00",
        retention="10 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - "
            "{message}"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

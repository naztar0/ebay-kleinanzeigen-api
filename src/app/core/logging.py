from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(
    *,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    app_name: str = "kleinanzeigen-api",
    logs_dir: Path | None = None,
) -> None:
    """Configure Loguru sinks for console and rotating file logging."""
    logger.remove()
    logger.configure(extra={"request_id": "-"})

    logger.add(
        sys.stderr,
        level=console_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<magenta>{extra[request_id]}</magenta> | "
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
        rotation="100 MB",
        retention="10 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} - {message}"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

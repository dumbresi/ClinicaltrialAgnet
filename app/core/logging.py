"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.core.config import Settings, get_settings


def setup_logging(settings: Settings | None = None) -> None:
    """Configure root logging for the application."""
    resolved = settings or get_settings()
    level = getattr(logging, resolved.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)


def log_context(
    logger: logging.Logger,
    message: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Log a message with optional structured key=value context."""
    if not fields:
        logger.log(level, message)
        return

    context = " ".join(f"{key}={value!r}" for key, value in fields.items())
    logger.log(level, "%s | %s", message, context)

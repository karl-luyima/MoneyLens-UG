
"""Structured logging configuration for MoneyLens UG."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging() -> None:
    """Configure application-wide structured logging."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

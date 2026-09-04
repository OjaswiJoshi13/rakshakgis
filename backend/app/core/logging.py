"""Application logging configuration."""

import logging
import sys
from app.core.middleware import get_request_id


class RequestIDFilter(logging.Filter):
    """Logging filter that injects the current request correlation ID into LogRecords."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure minimal application logging for startup and request diagnostics."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIDFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    logger = logging.getLogger("rakshakgis")
    logger.setLevel(level)
    return logger

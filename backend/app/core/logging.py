"""Application logging configuration."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure minimal application logging for startup and request diagnostics."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logger = logging.getLogger("rakshakgis")
    logger.setLevel(level)
    return logger

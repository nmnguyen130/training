import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured console logging for the application."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if re-called
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Helper to obtain a named logger."""
    return logging.getLogger(name)

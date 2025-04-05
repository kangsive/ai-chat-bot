import logging
from logging.config import dictConfig

def configure_logging():
    """Configure logging for the entire application."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": "INFO",
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
                "formatter": "default",
            },
            "fastapi": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    dictConfig(log_config) 
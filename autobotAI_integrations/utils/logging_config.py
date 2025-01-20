import logging
import logging.config
import os
import sys

DEBUG = os.getenv("DEBUG", None)


def setup_logging():
    # Remove existing handlers to avoid duplicate or ignored handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure logging based on environment
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging


# Call setup_logging when this module is imported
logger = setup_logging()

import logging
import logging.config
import os

DEBUG = os.getenv("DEBUG", None)


def setup_logging():
    if DEBUG:
        # Configure logging for development
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )
    else:
        # Configure logging for production
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )
    return logging


# Call setup_logging when this module is imported
logger = setup_logging()

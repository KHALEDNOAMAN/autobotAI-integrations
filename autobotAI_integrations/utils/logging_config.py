import logging
import os
from sys import stdout
from typing import Optional

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG" if os.getenv("DEBUG", None) else "INFO")
logger = logging.getLogger("AutobotAI-Integrations")
logger.propagate = False

class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'req_id'):
            record.req_id = "System"
        if not hasattr(record, 'bot_exc_id'):
            record.bot_exc_id = "AutobotAI"
        super().format(record)
        prefix = self.formatMessage(record).split(record.getMessage())[0]
        response = "\n".join(prefix + line for line in record.getMessage().splitlines())

        # append traceback with custom prefix if exc_info is present
        if getattr(record, "exc_info"):
            exc_text = self.formatException(record.exc_info)
            prefix = f"[{self.formatTime(record, self.datefmt)}] {record.levelname} for " \
                     f"[{getattr(record, 'req_id', '-')}] [{getattr(record, 'bot_exc_id', '-')}]"
            response += "\n" + prefix + "\n" + exc_text
        return response

def set_log_format(unformatted_logger):
    FORMAT = "[%(asctime)s] %(levelname)s in %(module)s/%(filename)s:%(funcName)s:%(lineno)d for [%(req_id)s] [%(bot_exc_id)s]-- %(message)s"
    unformatted_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(MultiLineFormatter(FORMAT))
    for old_handler in unformatted_logger.handlers:
        unformatted_logger.removeHandler(old_handler)
    unformatted_logger.addHandler(handler)
    set_unset_log_ids(unformatted_logger, None, None)

def set_unset_log_ids(unformatted_logger, req_id: Optional[str] = "Preserve", bot_exc_id: Optional[str] = "Preserve" ):
    """
    set_unset_log_ids: Used to set the logging requestIds and BotExecIds
    Use set_unset_log_ids(logger, None, None) to reset the logger
    """
    class LogFilter(logging.Filter):
        def filter(self, record):
            if not req_id and not bot_exc_id:
                record.req_id = "System"
                record.bot_exc_id = "AutobotAI"
            else:
                if req_id and req_id != "Preserve":
                    if req_id:
                        record.req_id = str(req_id)
                    else:
                        record.req_id = "System"
                if bot_exc_id and bot_exc_id != "Preserve":
                    if bot_exc_id:
                        record.bot_exc_id = str(bot_exc_id)
                    else:
                        record.bot_exc_id = "AutobotAI"
            return True
    if not req_id and not bot_exc_id:
        unformatted_logger.filters = []
    unformatted_logger.addFilter(LogFilter())

set_log_format(logger)
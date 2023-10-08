from datetime import datetime
import logging
import sys
import os

from common import alert
from config import config
from keys import keys


class ExitOnError(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            if config.ALERT_ENABLE:
                alert.send_message(config.ALERT_ENABLE, keys.TELEGRAM_KEY, config.ALERT_TELEGRAM_ID, f'ERROR: {record.message}')
            sys.exit(1)


def init_logging():

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a formatter with a custom log record format
    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(filename)-24s:%(lineno)-4d - %(message)s')

    # Create a StreamHandler to display logs on the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create log folder
    if not os.path.exists(config.LOG_FOLDER):
        try:
            os.makedirs(config.LOG_FOLDER)
        except:
            raise Exception(f'Unable to create folder: {config.LOG_FOLDER}')

    # Create a FileHandler to write logs to a file
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)

    # Create an ExitOnError handler
    exit_on_error_handler = ExitOnError()

    # Add the handler to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(exit_on_error_handler)

    # Create a function to get the UTC timestamp
    def get_utc_timestamp():
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create a function to get the local timestamp
    def get_local_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add the UTC and local timestamps to the log record format
    formatter.formatTime = lambda record, datefmt=None: f'{get_local_timestamp()}'

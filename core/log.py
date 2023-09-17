import logging
from datetime import datetime

class ExitOnError(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            exit(1)

def init_logging():

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a formatter with a custom log record format
    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(filename)-20s:%(lineno)-4d - %(message)s')

    # Create a StreamHandler to display logs on the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create an ExitOnError handler
    exit_on_error_handler = ExitOnError()

    # Add the handler to the logger
    logger.addHandler(console_handler)
    logger.addHandler(exit_on_error_handler)

    # Create a function to get the UTC timestamp
    def get_utc_timestamp():
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create a function to get the local timestamp
    def get_local_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add the UTC and local timestamps to the log record format
    formatter.formatTime = lambda record, datefmt=None: f'{get_utc_timestamp()} | {get_local_timestamp()}'

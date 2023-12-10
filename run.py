from datetime import datetime, timezone
import traceback
import argparse
import logging
import pytz
import yaml
import sys
import os

from common.pydantic.status import Status
from common import alert
from _keys import keys

import time


def log_info_alert(message):
    logging.info(message)
    alert.send_message(config.ALERT_ENABLE, keys.ALERT_TELEGRAM_SENDER_KEY, config.ALERT_TELEGRAM_RECEIVER_ID, message)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """This function handles uncaught exceptions."""
    # Do not print traceback for SystemExit and KeyboardInterrupt
    if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception here
    log_info_alert(f'Unhandled exception: {exc_type} {exc_value}')
    log_info_alert("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def has_duplicates(lst):
    seen = set()
    ret = False
    for item in lst:
        if item in seen:
            logging.warning(f'Duplicated input: {item}')
            ret = True
        seen.add(item)
    return ret


if __name__ == '__main__':

    # Parse arguments

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--active_date', '-d', type=str, required=True, help='Current date in yyyy')

    args = parser.parse_args()

    # Set paths

    code_path = os.path.dirname(os.path.abspath(__file__))
    os.environ['CODEPATH'] = code_path
    os.environ['PYTHONPATH'] = code_path

    # Set current date

    active_date = datetime.strptime(args.active_date, '%Y%m%d')
    active_datetime_str = active_date.strftime('%Y%m%d')
    os.environ['ACTIVE_DATE'] = active_datetime_str

    # Set current datetime

    os.environ['CURRENT_DATETIME'] = datetime.now().strftime("%y%m%d_%H%M%S")

    # Perform imports

    from common import log
    from config import config

    from stack.a_download_news.download_news import run as run_download_news
    from stack.b_news_to_vectordb.news_to_vectordb import run as run_news_to_vectordb
    from stack.c_get_main_topic.get_main_topic import run as run_get_main_topic
    from stack.d_construct_digest.construct_digest import run as run_construct_digest
    from stack.e_curate_digest.curate_digest import run as run_curate_digest
    from stack.f_review_digest.review_digest import run as run_review_digest
    from stack.g_download_media.download_media import run as run_download_media
    from stack.h_generate_clip.generate_clip import run as run_generate_clip
    from stack.i_generate_title.generate_title import run as run_generate_title
    from stack.j_upload_clip.upload_clip import run as run_upload_clip
    from stack.k_upload_thumbnail.upload_thumbnail import run as run_upload_thumbnail

    # Init logging

    log.init_logging()

    # Init exception handling

    sys.excepthook = global_exception_handler

    # Print datetime information

    log_info_alert(f'##########################################################################################')
    log_info_alert(f'curr datetime   :  {config.CURR_DATETIME}')
    log_info_alert(f'user date       :  {config.ACTIVE_DATE_STR}')
    log_info_alert(f'active datetime :  {config.ACTIVE_DATETIME_STR}')
    log_info_alert(f'active date     :  {config.ACTIVE_DATE_STR}')
    log_info_alert(f'publish datetime:  {config.PUBLISH_DATETIME_STR}')
    log_info_alert(f'publish date    :  {config.PUBLISH_DATE_STR}')

    # Create vardata folder

    if not os.path.exists(config.VARDATA_DATE_FOLDER):
        try:
            os.makedirs(config.VARDATA_DATE_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.VARDATA_DATE_FOLDER}')

    # Create log folder

    if not os.path.exists(config.LOG_FOLDER):
        try:
            os.makedirs(config.LOG_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.LOG_FOLDER}')

    # Create vectordb folder

    if not os.path.exists(config.VECTORDB_FOLDER):
        try:
            os.makedirs(config.VECTORDB_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.VECTORDB_FOLDER}')

    # Load status file

    if os.path.exists(config.STATUS_FILE):

        file_path = f'{config.STATUS_FILE}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        status = Status(**yaml_data)

        logging.info("Loaded existing status file")

    else:
        status = Status(**config.STATUS_DEFAULT_VALUE)

        with open(config.STATUS_FILE, 'w') as file:
            yaml.dump(status.model_dump(), file, sort_keys=False)

        logging.info("Created new status file")

    # Construct stack information

    stack_info = (
        ('download_news',     True, run_download_news,    status.download_news),
        ('news_to_vector_db', True, run_news_to_vectordb, status.news_to_vectordb),
        ('get_main_topic',    True, run_get_main_topic,   status.get_main_topic),
        ('construct_digest',  True, run_construct_digest, status.construct_digest),
        ('curate_digest',     True, run_curate_digest,    status.curate_digest),
        ('review_digest',     True, run_review_digest,    status.review_digest),
        ('download_media',    True, run_download_media,   status.download_media),
        ('generate_clip',     True, run_generate_clip,    status.generate_clip),
        ('generate_title',    True, run_generate_title,   status.generate_title),
        ('upload_clip',       True, run_upload_clip,      status.upload_clip),
        ('upload_thumbnail',  True, run_upload_thumbnail, status.upload_thumbnail),
    )

    # Run stack

    day = config.ACTIVE_DATETIME.weekday()
    idx = -1

    for idx, (name, debug_enable, func, st) in enumerate(stack_info):

        logging.info(f'##########################################################################################')
        log_info_alert(f'# Running stack: {name}')
        logging.info(f'##########################################################################################')

        if debug_enable == False:
            log_info_alert(f'# Internally disabled.')
            continue

        if st.enable == False:
            log_info_alert(f'# Config Disabled')
            continue

        start_time = time.time()

        input_list = list(st.input)

        if has_duplicates(input_list) == True:
            logging.error("Input list has duplicates")

        clean = False
        if st.append_output == False:
            clean = True

        output_list = func(clean, input_list)

        if idx < (len(stack_info) - 1):
            next_st = stack_info[idx + 1][3]
            if st.append_output == True:
                next_st.input += output_list
            else:
                next_st.input = output_list

        st.enable = False

        with open(config.STATUS_FILE, 'w') as file:
            yaml.dump(status.model_dump(), file, sort_keys=False)

        logging.info(f'##########################################################################################')
        end_time = time.time()
        elapsed_min = int((end_time - start_time) / 60)
        elapsed_sec = int((end_time - start_time) % 60)
        log_info_alert(f'# Stack ended: {name}, {elapsed_min}m {elapsed_sec}s')

    log_info_alert('crypto_news ended')


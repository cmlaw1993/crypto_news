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
from keys import keys

import time


def log_info_alert(message):
    logging.info(message)
    alert.send_message(config.ALERT_ENABLE, keys.TELEGRAM_KEY, config.ALERT_TELEGRAM_ID, message)


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
    for item in lst:
        if item in seen:
            return True
        seen.add(item)
    return False


if __name__ == '__main__':

    # Parse arguments

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--current_datetime', '-c', type=str, help='Current datetime in yyyymmdd_hhmmss')

    args = parser.parse_args()

    # Set paths

    code_path = os.path.dirname(os.path.abspath(__file__))
    os.environ['CODEPATH'] = code_path
    os.environ['PYTHONPATH'] = code_path

    # Set current datetime

    if args.current_datetime:
        current_datetime = datetime.strptime(args.current_datetime, '%Y%m%d_%H%M%S')
        current_datetime = current_datetime.replace(tzinfo=pytz.utc)
    else:
        current_datetime = datetime.now(timezone.utc)

    current_datetime_str = current_datetime.strftime('%Y%m%d_%H%M%S_%z')
    os.environ['CURRENT_DATETIME'] = current_datetime_str

    # Perform imports

    from common import log
    from config import config

    from stack.a_download_news.download_news import run as run_download_news
    from stack.b_news_to_vectordb.news_to_vectordb import run as run_news_to_vectordb
    from stack.c_get_main_topics.get_main_topics import run as run_get_main_topics
    from stack.d_construct_digest.construct_digest import run as run_construct_digest
    from stack.e_rank_digest.rank_digest import run as run_rank_digest
    from stack.f_select_digest.select_digest import run as run_select_digest
    from stack.g_download_media.download_media import run as run_download_media
    from stack.h_create_thumbnail.create_thumbnail import run as run_create_thumbnail
    from stack.i_generate_clip.generate_clip import run as run_generate_clip
    from stack.j_combine_clips.combine_clips import run as run_combine_clips
    from stack.k_upload_clip.upload_clip import run as run_upload_clip
    from stack.l_upload_thumbnail.upload_thumbnail import run as run_upload_thumbnail

    # Init logging

    log.init_logging()

    log_info_alert(f'crypto_news started: {config.ACTIVE_DATETIME_STR}')

    # Init exception handling

    sys.excepthook = global_exception_handler

    # Print datetime information

    logging.info(f'current datetime: {config.CURRENT_DATETIME_STR}')
    logging.info(f'active datetime:  {config.ACTIVE_DATETIME_STR}')
    logging.info(f'active date:      {config.ACTIVE_DATE_STR}')

    # Create vardata folder

    if not os.path.exists(config.VARDATA_DATE_FOLDER):
        try:
            os.makedirs(config.VARDATA_DATE_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.VARDATA_DATE_FOLDER}')

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

    stack_info = {
        'download_news':     (True, run_download_news,    status.download_news,    ['news_to_vector_db', 'get_main_topics']),
        'news_to_vector_db': (True, run_news_to_vectordb, status.news_to_vectordb, []),
        'get_main_topics':   (True, run_get_main_topics,  status.get_main_topics,  ['construct_digest']),
        'construct_digest':  (True, run_construct_digest, status.construct_digest, ['rank_digest']),
        'rank_digest':       (True, run_rank_digest,      status.rank_digest,      ['select_digest']),
        'select_digest':     (True, run_select_digest,    status.select_digest,    ['download_media', 'create_thumbnail']),
        'download_media':    (True, run_download_media,   status.download_media,   ['generate_clip']),
        'create_thumbnail':  (True, run_create_thumbnail, status.create_thumbnail, ['upload_thumbnail']),
        'generate_clip':     (True, run_generate_clip,    status.generate_clip,    ['combine_clips']),
        'combine_clips':     (True, run_combine_clips,    status.combine_clips,    ['upload_clip']),
        'upload_clip':       (True, run_upload_clip,      status.upload_clip,     ['upload_thumbnail']),
        'upload_thumbnail':  (False, run_upload_thumbnail, status.upload_thumbnail, []),
    }

    # Run stack

    day = config.ACTIVE_DATETIME.weekday()

    for name, (debug_enable, func, st, output_keys) in stack_info.items():

        logging.info(f'##########################################################################################')
        log_info_alert(f'# Running stack: {name}')
        logging.info(f'##########################################################################################')

        if debug_enable == False:
            log_info_alert(f'#### Internally disabled.')
            continue

        if st.enable == False:
            log_info_alert(f'#### Config Disabled')
            continue

        if day in [5, 6] and st.weekend == False:
            log_info_alert(f'#### Disabled for weekend')
            continue

        start_time = time.time()

        input_list = list(st.input)

        if has_duplicates(input_list) == True:
            logging.error("Input list has duplicates")

        clean = False
        if st.append_output == False:
            clean = True

        output = func(clean, input_list)

        if len(output) != len(output_keys):
            logging.error("Incorrect output length")

        for idx, ret_output_list in enumerate(output):

            if st.append_output == True:
                ret_output_list += stack_info[output_keys[idx]][2].input

            ret_output_list = list(set(ret_output_list))
            ret_output_list = sorted(ret_output_list)
            stack_info[output_keys[idx]][2].input = ret_output_list

        st.enable = False
        st.append_output = False

        with open(config.STATUS_FILE, 'w') as file:
            yaml.dump(status.model_dump(), file, sort_keys=False)

        logging.info(f'##########################################################################################')
        end_time = time.time()
        elapsed_min = int((end_time - start_time) / 60)
        elapsed_sec = int((end_time - start_time) % 60)
        log_info_alert(f'#### Stack ended: {name}, {elapsed_min}m {elapsed_sec}s')

    log_info_alert('crypto_news ended')


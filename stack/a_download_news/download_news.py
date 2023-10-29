from datetime import timedelta
import logging
import os

from stack.a_download_news.cyrptonewsapi.dlnews_alltickernews import run as run_dlnews_cryptonewsapi_alltickernews
from stack.a_download_news.cyrptonewsapi.dlnews_generalcryptonews import run as run_dlnews_cryptonewsapi_generalcryptonews
from stack.a_download_news.cyrptonewsapi.dlnews_sundowndigest import run as run_dlnews_cryptonewsapi_sundowndigest
from stack.a_download_news.cyrptonewsapi.dlnews_trendingheadlines import run as run_dlnews_cryptonewsapi_trendingheadlines

from stack.a_download_news.newsdata.dlnews_newsdata_all import run as run_dlnews_newsdata_all

from common import utils
from config import config


def run(clean, input_list):

    logging.info(f'a_download_news/download_news started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.DOWNLOADNEWS_FOLDER):
        try:
            os.makedirs(config.DOWNLOADNEWS_FOLDER)
            logging.info(f'Created folder: {config.DOWNLOADNEWS_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.DOWNLOADNEWS_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.DOWNLOADNEWS_FOLDER}/*')
        logging.info(f'Cleaned: {config.DOWNLOADNEWS_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate start and end datetime')

    start_dt = config.ACTIVE_DATETIME - timedelta(days=1)
    end_dt = config.ACTIVE_DATETIME

    logging.info(f'active_datetime: {utils.to_datetime_str(config.ACTIVE_DATETIME)}')
    logging.info(f'start_datetime : {utils.to_datetime_str(start_dt)}')
    logging.info(f'end_datetime   : {utils.to_datetime_str(end_dt)}')

    logging.info(f'[END  ] Calculate start_datetime and end_datetime')

    logging.info(f'------------------------------------------------------------------------------------------')

    output_list_all = list()
    output_list_sundowndigest = list()

    for module in config.DOWNLOADNEWS_MODULES:

        if module == 'cryptonewsapi_alltickernews':
            output_list_all += run_dlnews_cryptonewsapi_alltickernews(start_dt, end_dt)

        elif module == 'cryptonewsapi_generalcryptonews':
            output_list_all += run_dlnews_cryptonewsapi_generalcryptonews(start_dt, end_dt)

        elif module == 'cryptonewsapi_sundowndigest':
            output_list_sundowndigest += run_dlnews_cryptonewsapi_sundowndigest(start_dt, end_dt)
            output_list_all += output_list_sundowndigest

        elif module == 'cryptonewsapi_trendingheadlines':
            output_list_all += run_dlnews_cryptonewsapi_trendingheadlines(start_dt, end_dt)

        elif module == 'newsdata_all':
            output_list_all += run_dlnews_newsdata_all(start_dt, end_dt)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'a_download_news/download_news ended')

    return [output_list_all, output_list_sundowndigest]

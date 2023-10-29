import logging
import os

from stack.c_get_main_topics.cryptonewsapi.maintopic_sundowndigest import run as run_maintp_cryptonewsapi_sundowndigest

from config import config


def run(clean, input_list):

    logging.info(f'c_get_main_topics/get_main_topics started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.GETMAINTOPICS_FOLDER):
        try:
            os.makedirs(config.GETMAINTOPICS_FOLDER)
            logging.info(f'Created folder: {config.GETMAINTOPICS_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.GETMAINTOPICS_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.GETMAINTOPICS_FOLDER}/*')
        logging.info(f'Cleaned: {config.GETMAINTOPICS_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')

    output_list = list()

    for module in config.GETMAINTOPICS_MODULES:

        if module == 'cryptonewsapi_sundowndigest':
            output_list += run_maintp_cryptonewsapi_sundowndigest(input_list)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'c_get_main_topics/get_main_topics ended')

    return [output_list]

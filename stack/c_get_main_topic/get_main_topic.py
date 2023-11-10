import logging
import os

from stack.c_get_main_topic.cryptonewsapi.maintopic_sundowndigest import run as run_maintp_cryptonewsapi_sundowndigest

from config import config


def run(clean, input_list):

    logging.info(f'c_get_main_topics/get_main_topics started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.GETMAINTOPIC_FOLDER):
        try:
            os.makedirs(config.GETMAINTOPIC_FOLDER)
            logging.info(f'Created folder: {config.GETMAINTOPIC_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.GETMAINTOPIC_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.GETMAINTOPIC_FOLDER}/*')
        logging.info(f'Cleaned: {config.GETMAINTOPIC_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')

    output_list = list()

    for module in config.GETMAINTOPIC_MODULES:

        if module == 'cryptonewsapi_sundowndigest':
            output_list += run_maintp_cryptonewsapi_sundowndigest(input_list)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'c_get_main_topics/get_main_topics ended')

    return output_list

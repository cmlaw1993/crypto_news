import logging
import os

from stack.h_create_thumbnail.dummy.thumbnail_dummy import run as run_thumbnail_dummy
from stack.h_create_thumbnail.semiauto.thumbnail_semiauto import run as run_thumbnail_semiauto

from config import config


def run(clean, input_list):

    logging.info(f'h_create_thumbnail/create_thumbnail started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.CREATETHUMBNAIL_FOLDER):
        try:
            os.makedirs(config.CREATETHUMBNAIL_FOLDER)
            logging.info(f'Created folder: {config.CREATETHUMBNAIL_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.CREATETHUMBNAIL_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.CREATETHUMBNAIL_FOLDER}/*')
        logging.info(f'Cleaned: {config.CREATETHUMBNAIL_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')

    for module in config.CREATETHUMBNAIL_MODULES:

        if module == 'dummy':
            run_thumbnail_dummy(input_list)

        elif module == 'semiauto':
            run_thumbnail_semiauto(input_list)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'h_create_thumbnail/create_thumbnail ended')

    return []

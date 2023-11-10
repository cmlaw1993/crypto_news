import logging
import os

from stack.f_download_media.dummy.media_dummy import run as run_media_dummy
from stack.f_download_media.semiauto.media_semiauto import run as run_media_semiauto

from config import config


def run(clean, input_list):

    logging.info(f'f_download_media/f_download_media')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.DOWNLOADMEDIA_FOLDER):
        try:
            os.makedirs(config.DOWNLOADMEDIA_FOLDER)
            logging.info(f'Created folder: {config.DOWNLOADMEDIA_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.DOWNLOADMEDIA_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')

    output_list = list()

    for module in config.DOWNLOADMEDIA_MODULES:

        if module == 'dummy':
            output_list += run_media_dummy(input_list)

        elif module == 'semiauto':
            output_list += run_media_semiauto(input_list)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'f_download_media/f_download_media ended')

    return output_list

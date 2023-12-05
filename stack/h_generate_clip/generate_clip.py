import logging
import os

from stack.h_generate_clip.v1.clip_v1 import run as run_clip_v1

from config import config


def run(clean, input_list):
    logging.info(f'{config.GENERATECLIP_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.GENERATECLIP_FOLDER):
        try:
            os.makedirs(config.GENERATECLIP_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.GENERATECLIP_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.GENERATECLIP_FOLDER}/*')
        logging.info(f'Cleaned: {config.GENERATECLIP_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')

    output_list_all = list()

    for module in config.GENERATECLIP_MODULES:

        if module == "v1":
            output_list_all += run_clip_v1(input_list)

        else:
            logging.error(f'Unknown module: {module}')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.GENERATECLIP_NAME} ended')

    return output_list_all

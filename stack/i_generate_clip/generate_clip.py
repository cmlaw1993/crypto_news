import logging
import os

from stack.i_generate_clip.primary.clip_primary import run as run_clips_primary
from stack.i_generate_clip.secondary.clip_secondary import run as run_clips_secondary

from config import config


def run(clean, input_list):
    logging.info(f'i_generate_clip/generate_clip started')

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

        if module == "primary":
            output_list_all += run_clips_primary(input_list)

        elif module == "secondary":
            output_list_all += run_clips_secondary(input_list)

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'i_generate_clip/generate_clip ended')

    return [output_list_all]

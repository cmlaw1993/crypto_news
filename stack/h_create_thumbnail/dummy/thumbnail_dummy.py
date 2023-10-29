import logging

from config import config


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load dummy thumbnail')

    output = [config.CREATETHUMBNAIL_DUMMY_IMAGE,]

    logging.info(f'[END  ] Load dummy thumbnail')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output

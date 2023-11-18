import logging
import random
import yaml
import os

from common.pydantic.digest import Digest
from config import config


def content_to_list(content: str) -> list:

    content_list = list()

    for line in content.replace('\r', '').split('\n'):
        if len(line) > 10:
            content_list.append(line)

    return content_list


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for digest_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

        logging.info(f'Loaded: {file_path}')

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Assign images')

    for digest in digests:

        num_lines = 1 + len(digest.content)

        digest.media = dict()

        for idx in range(num_lines):
            media = dict()
            image_idx = idx % len(config.DOWNLOADMEDIA_DUMMY_IMAGE)
            media['id'] = config.DOWNLOADMEDIA_DUMMY_IMAGE[image_idx]
            media['keyword'] = ''
            media['source'] = ''
            media['author'] = ''
            media['credit'] = ''
            media['license'] = ''
            media['effects'] = 'ZoomOutCenter'
            digest.media[idx] = media

    output_list = list()

    for digest in digests:
        output_list.append(f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {file_path}')

    logging.info(f'[END  ] Assign images')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

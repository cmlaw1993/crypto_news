import logging
import yaml
import os

from common import utils
from common.pydantic.digest import Digest
from common.pydantic.vidinfo import VidInfo, Chapter
from config import config


def run(clean, input_list):

    logging.info(f'f_review_digest/review_digest started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.REVIEWDIGEST_FOLDER):
        try:
            os.makedirs(config.REVIEWDIGEST_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.REVIEWDIGEST_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.REVIEWDIGEST_FOLDER}/*')
        logging.info(f'Cleaned: {config.REVIEWDIGEST_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for digest_file in input_list:

        file_path = os.path.join(config.DATA_FOLDER, digest_file)
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Review digests')

    logging.info(f'Please review the curated digests for the day.  Then press ENTER.')
    input()

    logging.info(f'[END  ] Review digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digest')

    outputs = list()

    for digest in digests:

        outputs.append(f'{config.REVIEWDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.REVIEWDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {digest.id}')

    logging.info(f'[END  ] Save digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'f_review_digest/review_digest ended')

    return outputs

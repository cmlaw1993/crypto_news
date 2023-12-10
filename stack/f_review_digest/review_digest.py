import logging
import yaml
import os

from common.pydantic.digest import Digest
from config import config


def run(clean, input_list):

    logging.info(f'{config.REVIEWDIGEST_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.REVIEWDIGEST_FOLDER):
        try:
            os.makedirs(config.REVIEWDIGEST_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.REVIEWDIGEST_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load and save digests')

    # Only load and save digests if they do not already exists

    files = os.listdir(config.REVIEWDIGEST_FOLDER)
    if len(files) == 0:

        for digest_file in input_list:

            input_file_path = os.path.join(config.DATA_FOLDER, digest_file)
            with open(input_file_path, 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            digest = Digest(**yaml_data)

            output_file_path = f'{config.REVIEWDIGEST_FOLDER}/{digest.id}'
            with open(output_file_path, 'w') as yaml_file:
                yaml.dump(digest.model_dump(), yaml_file, sort_keys=False)

    logging.info(f'[END  ] Load and save digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Review digests')

    outputs = None
    matched = True

    while True:

        logging.info(f'Please review the curated digests for the day.  Then press ENTER.')
        input()

        outputs = list()

        for f in os.listdir(config.REVIEWDIGEST_FOLDER):

            file_path = os.path.join(config.REVIEWDIGEST_FOLDER, f)

            with open(file_path, 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)

            digest = Digest(**yaml_data)

            if digest.id != f:
                logging.warning(f'File name does not match digest id: {digest.id}')
                matched = False

            if 'primary' in digest.id or 'secondary' in digest.id:
                outputs.append(os.path.join(config.REVIEWDIGEST_RELATIVE_FOLDER, f))

        if matched:
            break

        matched = True
        continue

    logging.info(f'[END  ] Review digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.REVIEWDIGEST_NAME} ended')

    return outputs

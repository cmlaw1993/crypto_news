import logging
import yaml
import os

from common.pydantic.digest import Digest
from common import utils
from config import config

def run(clean, input_list):

    logging.info(f'f_select_digest/select_digest started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.SELECTDIGEST_FOLDER):
        try:
            os.makedirs(config.SELECTDIGEST_FOLDER)
            logging.info(f'Created folder: {config.SELECTDIGEST_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.SELECTDIGEST_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.SELECTDIGEST_FOLDER}/*')
        logging.info(f'Cleaned: {config.SELECTDIGEST_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sort input')

    def sort_by_rank(item):
        return item.split(".")[1]

    input_list = sorted(input_list, key=sort_by_rank)

    logging.info(f'[END  ] Sort input')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for digest_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Select digests')

    pri_start_idx = 0
    pri_end_idx   = config.SELECTDIGEST_NUM_PRIMARY
    sec_start_idx = pri_end_idx
    sec_end_idx   = sec_start_idx + config.SELECTDIGEST_NUM_SECONDARY
    uns_start_idx = sec_end_idx

    primary_digests   = digests[pri_start_idx:pri_end_idx]
    secondary_digests = digests[sec_start_idx:sec_end_idx]
    unused_digests    = digests[uns_start_idx:]

    logging.info(f'[END  ] Select digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digests')

    output_list = list()

    def save_digest(digest, type):

        rank = int(digest.id.split(".")[1])
        score = int(digest.id.split(".")[2])
        name = digest.id.split(".")[3]

        digest.id = f'digest.{type}.{rank:02}.{score:03}.{name}.yaml'

        if type != "unused":
            output_list.append(f'{config.SELECTDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.SELECTDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {digest.id}')

    for digest in primary_digests:
        save_digest(digest, "primary")

    for digest in secondary_digests:
        save_digest(digest, "secondary")

    for digest in unused_digests:
        save_digest(digest, "unused")

    logging.info(f'[END  ] Save digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'f_select_digest/select_digest ended')

    return [output_list, [output_list[0]]]

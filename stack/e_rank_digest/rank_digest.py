import logging
import yaml
import os

from common.pydantic.digest import Digest
from common import utils
from config import config


def run(clean, input_list):

    logging.info(f'e_rank_digest/rank_digest started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.RANKDIGEST_FOLDER):
        try:
            os.makedirs(config.RANKDIGEST_FOLDER)
            logging.info(f'Created folder: {config.RANKDIGEST_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.RANKDIGEST_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.RANKDIGEST_FOLDER}/*')
        logging.info(f'Cleaned: {config.RANKDIGEST_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

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
    logging.info(f'[BEGIN] Rank digest')

    vector_db = config.VECTORDB_GET_INST()

    digest_scores = list()

    for digest in digests:

        date_0_days_ago_str = utils.to_date_str(config.ACTIVE_DATETIME)
        docs_0_days_ago = vector_db.similarity_search_with_relevance_scores(query=f'{digest.title}', k=256, filter={'active_date': date_0_days_ago_str})

        unique_source = set()

        for doc in docs_0_days_ago:
            doc_file = doc[0].metadata['file']
            source = doc_file.split('.')[3]
            if source not in unique_source:
                unique_source.add(source)

        score = 0

        for source in unique_source:
            if source in config.RANKDIGEST_SOURCE_RANK:
                score += config.RANKDIGEST_SOURCE_RANK[source]
            else:
                score += 1

        digest_scores.append((score, digest))

    digest_scores = sorted(digest_scores, reverse=True, key=lambda x: x[0])

    for digest_score in digest_scores:
        logging.info(digest_score)

    logging.info(f'[END  ] Rank digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[START] Save digest')

    output_list = list()
    rank = 0

    for score, digest in digest_scores:

        digest.id = f'digest.{rank:02}.{score:03}.{digest.id.split(".")[2]}.yaml'
        rank += 1

        output_list.append(f'{config.RANKDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.RANKDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {digest.id}')

    logging.info(f'[END  ] Save digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'e_rank_digest/rank_digest ended')

    return [output_list]

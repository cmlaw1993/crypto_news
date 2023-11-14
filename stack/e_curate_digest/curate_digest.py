from datetime import timedelta
import logging
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common.pydantic.digest import Digest
from common import utils
from config import config
from keys import keys


def run(clean, input_list):

    logging.info(f'e_curate_digest/curate_digest started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.CURATEDIGEST_FOLDER):
        try:
            os.makedirs(config.CURATEDIGEST_FOLDER)
            logging.info(f'Created folder: {config.CURATEDIGEST_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.CURATEDIGEST_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.CURATEDIGEST_FOLDER}/*')
        logging.info(f'Cleaned: {config.CURATEDIGEST_FOLDER}')
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
    logging.info(f'[BEGIN] Curate digest')

    verdicts = list()

    curated = list()

    for digest in digests:

        system_template = f'You are a top editor for a cryptocurrency news agency.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        accepted_str = ''
        for idx, crt in enumerate(curated):

            contents = ''
            for content in crt.content:
                contents += f'{content}'
                if contents[-1] != '.':
                    contents += "."
                contents += ' '

            accepted_str += f'Article {idx+1}'
            accepted_str += f'    Title: {crt.title}\n'
            accepted_str += f'    Content: {contents}\n'
            accepted_str += f'\n'

        if accepted_str == '':
            accepted_str += '    <List is currently empty>'

        new_str = ''
        contents = ''
        for content in digest.content:
            contents += f'{content}'
            if contents[-1] != '.':
                contents += "."
            contents += ' '

        new_str += f'New Article:'
        new_str += f'    Title: {digest.title}\n'
        new_str += f'    Content: {contents}\n'
        new_str += f'\n'

        human_template = f'The following is the list of cryptocurrency news articles that are to be published for the day:\n' \
                         f'\n' \
                         f'{accepted_str}\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'A journalist has brought in an additional article as follows:\n' \
                         f'\n' \
                         f'{new_str}\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'Your task is to determine if the article is to be accepted for the day\'s publication.\n' \
                         f'You can only accept the article if it meets the following criteria:\n' \
                         f'1. The subject matter in the new article has not already appeared in the existing list.\n' \
                         f'2. The article is not about price prediction of a token.\n' \
                         f'\n' \
                         f'Return your answer in this format:\n' \
                         f'\n' \
                         f'<yes/no>:<reason for accepting/rejecting>\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                          model_name=config.CURATEDIGEST_OPENAI_MODEL,
                          temperature=config.CURATEDIGEST_OPENAI_TEMPERATURE,
                          request_timeout=config.CURATEDIGEST_OPENAI_TIMEOUT)
        res = chat(prompt)

        answer = res.content
        yn = answer.split(':')[0]
        reason = answer.split(':')[1]

        if yn.strip().lower() == 'yes':
            verdicts.append(f'Accepted : {digest.title} : {reason}')
            curated.append(digest)
        else:
            verdicts.append(f'Rejected : {digest.title} : {reason}')

    for verdict in verdicts:
        logging.info(verdict)

    digests = curated

    logging.info(f'[END  ] Curate digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Compare to recent digests')

    prev_digests = list()

    for i in range(config.CURATEDIGEST_DAYS_AGO):

        day = i + 1

        prev_date = utils.to_date_str(config.ACTIVE_DATE - timedelta(days=day))
        folder = os.path.join(config.VARDATA_FOLDER, prev_date, config.CURATEDIGEST_NAME)
        if not os.path.exists(folder):
            continue

        files = [os.path.join(folder, f) for f in os.listdir(folder)]
        for file_path in files:
            with open(file_path, 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            prev_digest = Digest(**yaml_data)
            prev_digests.append(prev_digest)

    deduplicated = list()
    verdicts = list()

    if len(prev_digests) > 0:

        for digest in digests:

            system_template = f'You are a top editor for a cryptocurrency news agency.'
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

            prev_str = ''
            for idx, prev in enumerate(prev_digests):

                contents = ''
                for content in prev.content:
                    contents += f'{content}'
                    if contents[-1] != '.':
                        contents += "."
                    contents += ' '

                prev_str += f'Article {idx + 1}'
                prev_str += f'    Title: {prev.title}\n'
                prev_str += f'    Content: {contents}\n'
                prev_str += f'\n'

            new_str = ''
            contents = ''
            for content in digest.content:
                contents += f'{content}'
                if contents[-1] != '.':
                    contents += "."
                contents += ' '

            new_str += f'New Article:'
            new_str += f'    Title: {digest.title}\n'
            new_str += f'    Content: {contents}\n'
            new_str += f'\n'

            human_template = f'The following is the list of cryptocurrency news articles that are to be published for the day:\n' \
                             f'\n' \
                             f'{prev_str}\n' \
                             f'\n' \
                             f'\n' \
                             f'\n' \
                             f'A journalist has brought in an additional article as follows:\n' \
                             f'\n' \
                             f'{new_str}\n' \
                             f'\n' \
                             f'\n' \
                             f'\n' \
                             f'Your task is to determine if the article is to be accepted for the day\'s publication.\n' \
                             f'You can only accept the article if it meets the following criteria:\n' \
                             f'1. The subject matter in the new article has not already appeared in the existing list.\n' \
                             f'2. The article is not about price prediction of a token.\n' \
                             f'\n' \
                             f'Return your answer in this format:\n' \
                             f'\n' \
                             f'<yes/no>:<reason for accepting/rejecting>\n' \
                             f'\n'

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

            chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
            prompt = chat_prompt.format_prompt().to_messages()

            chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                              model_name=config.CURATEDIGEST_OPENAI_MODEL,
                              temperature=config.CURATEDIGEST_OPENAI_TEMPERATURE,
                              request_timeout=config.CURATEDIGEST_OPENAI_TIMEOUT)
            res = chat(prompt)

            answer = res.content
            yn = answer.split(':')[0]
            reason = answer.split(':')[1]

            if yn.strip().lower() == 'yes':
                verdicts.append(f'Accepted : {digest.title} : {reason}')
                deduplicated.append(digest)
            else:
                verdicts.append(f'Rejected : {digest.title} : {reason}')

    for verdict in verdicts:
        logging.info(verdict)

        digests = deduplicated

    logging.info(f'[END  ] Compare to recent digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Rank digest')

    vector_db = config.VECTORDB_GET_INST()

    digest_scores = list()

    for digest in digests:

        date_0_days_ago_str = utils.to_date_str(config.ACTIVE_DATETIME)
        docs_0_days_ago = vector_db.similarity_search_with_relevance_scores(query=f'{digest.oneliner}', k=256, filter={'active_date': date_0_days_ago_str})

        unique_source = set()

        for doc in docs_0_days_ago:
            doc_file = doc[0].metadata['file']
            source = doc_file.split('.')[3]
            if source not in unique_source:
                unique_source.add(source)

        score = 0

        for source in unique_source:
            if source in config.CURATEDIGEST_SOURCE_RANK:
                score += config.CURATEDIGEST_SOURCE_RANK[source]

        digest_scores.append((score, digest))

    digest_scores = sorted(digest_scores, reverse=True, key=lambda x: x[0])

    for digest_score in digest_scores:
        logging.info(digest_score)

    logging.info(f'[END  ] Rank digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Specialize digests')

    pri_start_idx = 0
    pri_end_idx   = config.CURATEDIGEST_NUM_PRIMARY
    sec_start_idx = pri_end_idx
    sec_end_idx   = sec_start_idx + config.CURATEDIGEST_NUM_SECONDARY
    uns_start_idx = sec_end_idx

    primary_digest_scores   = digest_scores[pri_start_idx:pri_end_idx]
    secondary_digest_scores = digest_scores[sec_start_idx:sec_end_idx]
    unused_digest_scores    = digest_scores[uns_start_idx:]

    logging.info(f'[END  ] Specialize digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digests')

    output_list = list()

    def save_digest(rank, score, digest, type):

        name = digest.id.split(".")[2]

        digest.id = f'digest.{type}.{rank:02}.{score:03}.{name}.yaml'

        if type != "unused":
            output_list.append(f'{config.CURATEDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.CURATEDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {digest.id}')

    for idx, (score, digest) in enumerate(primary_digest_scores):
        save_digest(idx, score, digest, "primary")

    for idx, (score, digest) in enumerate(secondary_digest_scores):
        save_digest(idx, score, digest, "secondary")

    for idx, (score, digest) in enumerate(unused_digest_scores):
        save_digest(idx, score, digest, "unused")

    logging.info(f'[END  ] Save digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'e_curate_digest/curate_digest ended')

    return output_list

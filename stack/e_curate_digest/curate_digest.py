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

def digest_to_text(article, idx=None):
    contents = ''
    for content in article.content:
        contents += f'{content}'
        if contents[-1] != '.':
            contents += "."
        contents += ' '

    ret = ''
    if idx == None:
        ret += f'Article:\n'
    else:
        ret += f'Article {idx}:\n'
    ret += f'    Title: {article.title}\n'
    ret += f'    Content: {contents}\n'
    ret += f'\n'
    
    return ret


def run(clean, input_list):

    logging.info(f'{config.CURATEDIGEST_NAME} started')

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
    logging.info(f'[BEGIN] Sort digests')

    digests = sorted(digests, key=lambda x: x.priority)

    logging.info(f'[END  ] Sort digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Curate digest')

    chats = [
        ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                   model_name=config.CONSTRUCTDIGEST_OPENAI_MODEL,
                   temperature=config.CONSTRUCTDIGEST_OPENAI_TEMPERATURE,
                   request_timeout=config.CONSTRUCTDIGEST_OPENAI_TIMEOUT),
        ChatOpenAI(openai_api_key=keys.OPENAI_KEY_1,
                   model_name=config.CONSTRUCTDIGEST_OPENAI_MODEL,
                   temperature=config.CONSTRUCTDIGEST_OPENAI_TEMPERATURE,
                   request_timeout=config.CONSTRUCTDIGEST_OPENAI_TIMEOUT)
    ]

    accepted_digests = list()
    rejected_digests = list()
    
    verdicts = list()

    for idx, digest in enumerate(digests):

        system_template = f'You are a top editor for a cryptocurrency and AI news agency.' \
                          f' Your target audience ranges from enthusiasts to top cryptocurrency traders, fund managers, and AI investors,' \
                          f' who trusts in the objectiveness and fairness of your publication' \
                          f' to keep up to date with the latest happenings in the crypto and AI world.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        accepted_str = ''
        for idx, accepted in enumerate(accepted_digests):
            accepted_str += digest_to_text(accepted, idx)
        if accepted_str == '':
            accepted_str += '    <List is currently empty>'

        new_str = ''
        new_str += digest_to_text(digest)

        human_template = f'The following is the list of news articles that are to be published for the day:\n' \
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
                         f'1. The subject matter in the new article has not already appeared in the existing list. Ignore this criteria if the list of articles is empty.\n' \
                         f'2. The article is not about price prediction or analysis of a token. If you could not make a proper determination, accept the article anyways.\n' \
                         f'3. The article is not about a promotion. If you could not make a proper determination, accept the article anyways.\n' \
                         f'4. The article is not about a tutorial.  If you could not make a proper determination, accept the article anyways.\n' \
                         f'5. The headline is not written in the form of a question.\n' \
                         f'\n' \
                         f'Return your answer in this format:\n' \
                         f'\n' \
                         f'<yes/no>:<reason for accepting/rejecting>\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = chats[idx % len(chats)]
        res = chat(prompt)

        answer = res.content
        yn = answer.split(':')[0].strip().lower()
        reason = answer.split(':')[1]

        if yn == 'yes' or yn == '<yes>':
            digest.reason = f'{yn} : {reason}'
            accepted_digests.append(digest)
            verdicts.append(f'Accepted : {digest.title} : {reason}')
        else:
            digest.reason = reason
            rejected_digests.append(digest)
            verdicts.append(f'Rejected : {digest.title} : {reason}')

    for verdict in verdicts:
        logging.info(verdict)

    digests = list(accepted_digests)

    logging.info(f'[END  ] Curate digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Compare to previous day\'s digests')

    accepted_digests = list(digests)
    repeated_digests = list()
    verdicts = list()

    for i in range(config.CURATEDIGEST_DAYS_AGO):

        day = i + 1

        prev_digests = list()

        prev_date = utils.to_date_str(config.ACTIVE_DATE - timedelta(days=day))
        folder = os.path.join(config.VARDATA_FOLDER, prev_date, config.CURATEDIGEST_NAME)
        if not os.path.exists(folder):
            continue

        files = [os.path.join(folder, f) for f in os.listdir(folder)]
        for file_path in files:
            if 'digest.unused' in file_path:
                continue
            if 'digest.z_rejected' in file_path:
                continue
            if 'digest.z_repeated' in file_path:
                continue
            with open(file_path, 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            prev_digest = Digest(**yaml_data)
            prev_digests.append(prev_digest)

        if len(prev_digests) > 0:

            tmp_digests = list(accepted_digests)
            accepted_digests = list()

            prev_digests = sorted(prev_digests, key=lambda x: x.priority)
            accepted_digests = sorted(accepted_digests, key=lambda x: x.priority)

            for idx, digest in enumerate(tmp_digests):

                # A simple system template seems to work better to tone done the aggression
                # of the AI in filtering out digests.
                system_template = f'You are a top editor for a cryptocurrency and AI news agency.'
                system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

                prev_str = ''
                for idx, prev in enumerate(prev_digests):
                    prev_str += digest_to_text(prev, idx)

                new_str = ''
                new_str += digest_to_text(digest)

                human_template = f'The following is the list of news articles that have been published {day} day(s) ago:\n' \
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
                                 f'You can only accept the article if it does not repeat an article that have been previously published.\n' \
                                 f'You should accept an article if it provides a new angle or new information on an article that have been previously published.\n' \
                                 f'\n' \
                                 f'Return your answer in this format:\n' \
                                 f'\n' \
                                 f'<accepted/rejected>:<reason for accepting/rejecting>:<article title from previous day that collides with current day>\n' \
                                 f'\n'

                human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

                chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
                prompt = chat_prompt.format_prompt().to_messages()

                chat = chats[idx % len(chats)]
                res = chat(prompt)

                answers = res.content.split(':')

                ret = answers[0].strip().lower()
                reason = answers[1]
                article = ''
                if len(answers) > 2:
                    article = answers[2]

                if ret == 'accepted' or ret == '<accepted>':
                    accepted_digests.append(digest)
                    verdicts.append(f'Accepted : {digest.title} : {reason}')
                else:
                    digest.reason = f'{prev_date}:{res.content}'
                    repeated_digests.append(digest)
                    verdicts.append(f'Rejected : {digest.title} : {prev_date} : {article} : {reason}')

    for verdict in verdicts:
        logging.info(verdict)

    digests = accepted_digests

    logging.info(f'[END  ] Compare to previous day\'s digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Specialize digests')

    digests = sorted(digests, key=lambda x: x.priority)

    pri_start_idx = 0
    pri_end_idx   = config.CURATEDIGEST_NUM_PRIMARY
    sec_start_idx = pri_end_idx
    sec_end_idx   = sec_start_idx + config.CURATEDIGEST_NUM_SECONDARY
    uns_start_idx = sec_end_idx

    primary_digests   = digests[pri_start_idx:pri_end_idx]
    secondary_digests = digests[sec_start_idx:sec_end_idx]
    unused_digests    = digests[uns_start_idx:]

    logging.info(f'[END  ] Specialize digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digests')

    output_list = list()

    def save_digest(digest, type):

        name = utils.sanitize_file_name(digest.title)
        priority = digest.priority
        priority_score = digest.priority_score

        digest.id = f'digest.{type}.{priority:02}.{priority_score:03}.{name}.yaml'

        if type == "primary" or type == 'secondary':
            output_list.append(f'{config.CURATEDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.CURATEDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {digest.id}')

    for digest in primary_digests:
        save_digest(digest, "primary")

    for digest in secondary_digests:
        save_digest(digest, "secondary")

    for digest in unused_digests:
        save_digest(digest, "unused")

    for digest in rejected_digests:
        save_digest(digest, "z_rejected")

    for digest in repeated_digests:
        save_digest(digest, "z_repeated")

    logging.info(f'[END  ] Save digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.CURATEDIGEST_NAME} ended')

    return output_list

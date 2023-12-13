import logging
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from config import config
from common.pydantic.digest import Digest
from common.pydantic.clipdata import ClipData
from _keys import keys


def format_time(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def run(clean, input_list):

    logging.info(f'{config.GENERATETITLE_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.GENERATETITLE_FOLDER):
        try:
            os.makedirs(config.GENERATETITLE_FOLDER)
            logging.info(f'Created folder: {config.GENERATETITLE_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.GENERATETITLE_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.GENERATETITLE_FOLDER}/*')
        logging.info(f'Cleaned: {config.GENERATETITLE_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load clipdata')

    if len(input_list) != 1:
        logging.error('Received multiple clipdata as input although only one expected')

    file_path = os.path.join(config.DATA_FOLDER, input_list[0])
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    clipdata = ClipData(**yaml_data)

    logging.info(f'[END  ] Load clipdata')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    sorted_chapters = sorted(clipdata.chapters, key=lambda x: x.ts)

    digests = list()

    for idx, chapter in enumerate(sorted_chapters):

        digest_path = os.path.join(config.DATA_FOLDER, chapter.digest)
        with open(digest_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate short titles')

    short_titles = list()

    for digest in digests:

        if '.primary.' not in digest.id:
            continue

        subtitle = config.GENERATETITLE_TITLE_SUBTITLE
        max_len = config.GENERATETITLE_TITLE_NUM_CHARACTERS - len(subtitle)

        retries = config.GENERATETITLE_TITLE_NUM_RETRIES

        article_str = ''
        for line in digest.content:
            article_str += line
            if article_str[-1] != '.':
                article_str += '.'
            article_str += ' '

        short_title = None

        while retries > 0:

            system_template = f'You are a top editor for a cryptocurrency news agency.'
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

            human_template = f'The following is an article\n'\
                             f'\n' \
                             f'{article_str}\n' \
                             f'\n' \
                             f'\n' \
                             f'\n' \
                             f'\n' \
                             f'Your task is to reword the title for a Youtube video, such that the title would attract views.\n' \
                             f'The reworded title must be in an active voice.\n'\
                             f'The reworded title must be within {max_len} characters.\n' \
                             f'Simply state your answer without forming a sentence.\n' \
                             f'\n'

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

            chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
            prompt = chat_prompt.format_prompt().to_messages()

            chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                              model_name=config.GENERATETITLE_OPENAI_MODEL,
                              temperature=config.GENERATETITLE_OPENAI_TEMPERATURE,
                              request_timeout=config.GENERATETITLE_OPENAI_TIMEOUT)
            res = chat(prompt)

            short_title = res.content

            if short_title[0] == '"' or short_title[0] == '\'':
                short_title = short_title[1:]

            if short_title[-1] == '"' or short_title[-1] == '\'':
                short_title = short_title[:-1]

            short_title_subtitle = subtitle + short_title

            if len(short_title_subtitle) <= config.GENERATETITLE_TITLE_NUM_CHARACTERS:
                break

            retries -= 1

        if retries == 0:
            logging.warning(f'Unable to generate title.  Retry limit reached.  Will proceed with what is given.')

        short_titles.append(short_title)

        logging.info(f'Original title : {digest.title}')
        logging.info(f'Generated title: {short_title}')

    clipdata.title = subtitle + short_titles[0]

    logging.info(f'Video title: {clipdata.title}')

    logging.info(f'[END  ] Generate title')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate description')

    # Add introduction

    description = 'Welcome to The New Satellite, your quick and reliable source for the latest happenings in the world of cryptocurrencies.\n'
    description += '\n'
    description += 'In today\'s edition:\n'
    description += '\n'

    # Add timestamps

    description += '0:00 Intro\n'
    for idx, chapter in enumerate(sorted_chapters):
        if '.primary.' in chapter.digest:
            description += f'{format_time(chapter.ts)} [Top Story {idx + 1}] - {short_titles[idx]}\n'
        else:
            description += f'{format_time(chapter.ts)} [Quick Highlights]\n'
            break
    description += f'\n'

    # Add tags

    for tag in config.GENERATETITLE_TAGS:
        description += f'#{tag} '
    description += '\n'

    clipdata.description = description

    logging.info(f'[END  ] Generate description')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save clipdata')

    file_path = os.path.join(config.GENERATETITLE_FOLDER, clipdata.id)
    with open(file_path, 'w') as file:
        yaml.dump(clipdata.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Save clipdata')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.GENERATETITLE_NAME} ended')

    return [os.path.join(config.GENERATETITLE_RELATIVE_FOLDER, clipdata.id)]

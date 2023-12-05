import logging
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from config import config
from common.pydantic.digest import Digest
from common.pydantic.clipinfo import VidInfo
from keys import keys


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
    logging.info(f'[BEGIN] Load vidinfo')

    if len(input_list) != 1:
        logging.error('Received multiple vidinfo as input although only one expected')

    file_path = os.path.join(config.DATA_FOLDER, input_list[0])
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    vidinfo = VidInfo(**yaml_data)

    logging.info(f'[END  ] Load vidinfo')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate title')

    sorted_chapters = sorted(vidinfo.chapters, key=lambda x: x.ts)

    system_template = f'You are a top editor for a cryptocurrency news agency.'
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    chapters = ''
    chapters += f'Chapter 0: {sorted_chapters[1].title}\n'
    chapters += f'Chapter 1: {sorted_chapters[2].title}\n'
    chapters += f'Chapter 2: {sorted_chapters[3].title}\n'

    human_template = f'The following is a list of chapters that are in a video\n'\
                     f'\n' \
                     f'{chapters}\n' \
                     f'\n' \
                     f'\n' \
                     f'\n' \
                     f'\n' \
                     f'Your task is generate a title for the video.\n' \
                     f'The video title must be strictly within {config.GENERATETITLE_NUM_TITLE_CHARACTERS} characters.\n' \
                     f'To generate the title, follow the following instructions:\n' \
                     f'1. Summarize each chapter and rewrite in an active voice.\n'\
                     f'2. Fit all three summarized chapters together in the form of "<Chapter 0> | <Chapter 1> | <Chapter 2>".\n' \
                     f'3. If the title is above {config.GENERATETITLE_NUM_TITLE_CHARACTERS} characters, remove <Chapter 2>.\n' \
                     f'4. If the title is above {config.GENERATETITLE_NUM_TITLE_CHARACTERS} characters, remove <Chapter 1> and <Chapter 2>.\n' \
                     f'5. In all cases, the title must be written in an active voice.\n' \
                     f'6. Simply state your answer without forming a sentence.' \
                     f'\n'

    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                      model_name=config.GENERATETITLE_OPENAI_MODEL,
                      temperature=config.GENERATETITLE_OPENAI_TEMPERATURE,
                      request_timeout=config.GENERATETITLE_OPENAI_TIMEOUT)
    res = chat(prompt)

    vid_title = res.content

    # if len(vid_title) > config.GENERATETITLE_NUM_TITLE_CHARACTERS:
    #     chs = vid_title.split(' | ')
    #     vid_title = f'{chs[0]} | {chs[1]}'
    #
    # if len(vid_title) > config.GENERATETITLE_NUM_TITLE_CHARACTERS:
    #     chs = vid_title.split(' | ')
    #     vid_title = f'{chs[0]}'

    vidinfo.title = vid_title

    logging.info(len(vidinfo.title))

    logging.info(f'[END  ] Generate title')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for idx, chapter in enumerate(vidinfo.chapters):
        if idx == 0:
            continue

        digest_path = os.path.join(config.DATA_FOLDER, chapter.digest)
        with open(digest_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Deduce main actor')

    main_actors = list()

    for digest in digests:

        system_template = f'You are a top editor for a cryptocurrency news agency.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = f'{digest.title}\n' \
                         f'\n' \
                         f'Deduce the single main actor of the news title.\n' \
                         f'Simply return the name without forming a sentence\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                          model_name=config.GENERATETITLE_OPENAI_MODEL,
                          temperature=config.GENERATETITLE_OPENAI_TEMPERATURE,
                          request_timeout=config.GENERATETITLE_OPENAI_TIMEOUT)
        res = chat(prompt)

        main_actors.append(res.content)

    logging.info(f'[END  ] Deduce main actor')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate description')

    description = ''

    # Add first primary article contents

    for line in digests[0].content:
        description += f'{line}\n'
    description += f'\n'

    # Add tags

    tags = set()

    description += '#News #Crypto #Bitcoin #Ethereum '
    tags.add('News')
    tags.add('Crypto')
    tags.add('Bitcoin')
    tags.add('Ethereum')

    for actor in main_actors:
        tmp = actor.replace(' ', '')
        if tmp not in tags:
            description += f'#{tmp} '
    description += '\n'

    # Add timestamps

    for idx, chapter in enumerate(sorted_chapters):
        description += f'{format_time(chapter.ts)} {chapter.title}\n'
    description += f'\n'

    # Add disclaimer

    description += 'Disclaimer:'
    description += 'The information provided in this video is for educational purposes and shall not be misconstrued' \
                   ' as financial advice. The New Satellite assumes no liability for any actions taken based on'\
                   ' the presented content.'
    description += f'\n'


    vidinfo.description = description

    logging.info(f'[END  ] Generate description')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save vidinfo')

    file_path = os.path.join(config.GENERATETITLE_FOLDER, vidinfo.id)
    with open(file_path, 'w') as file:
        yaml.dump(vidinfo.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Save vidinfo')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.GENERATETITLE_NAME} ended')

    return [os.path.join(config.GENERATETITLE_RELATIVE_FOLDER, vidinfo.id)]

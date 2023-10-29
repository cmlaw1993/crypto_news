import logging
import yaml

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.article import Article
from common.pydantic.topic import Topic
from config import config
from keys import keys


def content_to_list(content: str) -> list:

    content_list = list()

    for line in content.replace('\r', '').split('\n'):
        if len(line) > 10:
            content_list.append(line)

    return content_list


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load cryptonewsapi sundowndigest article')

    # Note: Sometimes, there are two sundowndigests uploaded in a single day.
    #       Under such circumstances, use the latest one.
    input_list = sorted(input_list)
    file_name = input_list[-1]
    file_path = f'{config.DATA_FOLDER}/{file_name}'
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    article = Article(**yaml_data)

    logging.info(f'Loaded: {file_path}')

    logging.info(f'[END  ] Load cryptonewsapi sundowndigest article')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sanitize content')

    system_template = 'You are a top news editor.'
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    human_template = f'The following is a news article titled Sundown Digest.'\
                     f' Please remove the introduction and the closing statement from the article:\n'\
                     f'{article.content}'
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt,human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY,
                      model_name=config.GETMAINTOPICS_SUNDOWNDIGEST_OPENAI_MODEL,
                      temperature=config.GETMAINTOPICS_SUNDOWNDIGEST_OPENAI_TEMPERATURE)
    results = chat(prompt)
    sanitized_content = results.content

    original_formatted = content_to_list(article.content)
    sanitized_formatted = content_to_list(sanitized_content)

    for i, line in enumerate(original_formatted):
        logging.info(f'original : {i}: {line}')

    for i, line in enumerate(sanitized_formatted):
        logging.info(f'sanitized: {i}: {line}')

    logging.info(f'[END  ] Sanitize content')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Get main topics')

    main_topics = list()

    system_template = f'You are a top editor for a cryptocurrency news agency.'\
                      f' Your target audience include top cryptocurrency traders and fund managers who makes important decisions based on your articles.'
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    # human_template = f'{sanitized_content}\n'\
    #                  f'\n'\
    #                  f'\n'\
    #                  f'\n'\
    #                  f'\n'\
    #                  f'\n'\
    #                  f'The above is a news snippet.'\
    #                  f' Identify all the key points of this news snippet.'\
    #                  f' Simply state your answer without forming a sentence.'\
    #                  f' Separate each key point with a newline.'\
    #                  f' Return each key point in the sequence they appear.'\
    #                  f' Group key points with the same main actor together.'

    human_template = f'{sanitized_content}\n'\
                     f'\n'\
                     f'\n'\
                     f'\n'\
                     f'\n'\
                     f'\n'\
                     f'The above is a news snippet.'\
                     f' Identify all the key points of this news snippet and the originating sentence they belong to.'\
                     f' Simply state your answer without forming a sentence.' \
                     f' Return each key point in the sequence they appear.' \
                     f' Group key points with the same main actor together.' \
                     f' Format your answer as follows:\n'\
                     f' \n' \
                     f' Keypoint:<First keypoint><newline>\n' \
                     f' Sentence:<Originating sentence for first keypoint>\n' \
                     f' <newline>\n' \
                     f' Keypoint:<Second keypoint><newline>\n' \
                     f' Sentence:<Originating sentence for second keypoint>\n'\
                     f' <newline>\n'

    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt,human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY,
                      model_name=config.GETMAINTOPICS_SUNDOWNDIGEST_OPENAI_MODEL,
                      temperature=config.GETMAINTOPICS_SUNDOWNDIGEST_OPENAI_TEMPERATURE)
    results = chat(prompt)

    def next_line(idx, lines):
        while True:
            if idx >= len(lines):
                return -1

            if len(lines[idx].strip()) == 0:
                idx += 1
                continue
            return idx

    lines = results.content.split('\n')
    idx = 0

    priority = 0

    while True:

        idx = next_line(idx, lines)
        if idx < 0:
            break

        keypoint = lines[idx].split(':')[-1].strip()
        idx += 1

        idx = next_line(idx, lines)
        if idx < 0:
            logging.error(f'Unable to parse keypoints from openai: {results.content}')
            break

        sentence = lines[idx].split(':')[-1].strip()
        idx += 1

        maintopic_data = {
            'id': f'main_topic.cryptonewsapi_sundowndigest.{priority:02}.{utils.sanitize_file_name(keypoint)}.yaml',
            'content': keypoint,
            'source': file_name,
            'source_content': sentence,
            'datetime': config.ACTIVE_DATETIME_STR,
            'date': config.ACTIVE_TIME_STR,
            'time': config.ACTIVE_TIME_STR
        }

        main_topic = Topic(**maintopic_data)
        main_topics.append(main_topic)

        priority += 1

    if len(main_topics) == 0:
        logging.error(f'Main topics is 0. Parsing keypoints from openai unsuccessful: {results.content}')

    output_list = list()

    for main_topic in main_topics:

        output_list.append(f'{config.GETMAINTOPICS_RELATIVE_FOLDER}/{main_topic.id}')

        file_path = f'{config.GETMAINTOPICS_FOLDER}/{main_topic.id}'
        with open(file_path, 'w') as file:
            yaml.dump(main_topic.model_dump(), file, sort_keys=False)

        logging.info(f'saved  : {file_path}')
        logging.info(f'content: {main_topic.content}')

    logging.info(f'[END  ] Get main topics')

    return output_list

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
        if len(line) > 5:
            content_list.append(line)

    return content_list


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load ranked articles')

    articles = list()
    source_title = set()

    for article_file in input_list:
        file_path = f'{config.DATA_FOLDER}/{article_file}'

        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        article = Article(**yaml_data)

        if article.source.lower() in config.GETMAINTOPIC_RANK_SOURCE_RANK.keys():

            s_t = article.source.lower() + "." + article.title.lower()

            if s_t not in source_title:
                source_title.add(s_t)
                articles.append(article)

    logging.info(f'[END  ] Load ranked articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Get main topics')

    system_template = f'You are a top editor for a cryptocurrency news agency.'
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    source_rank = ''
    for source, rank in config.GETMAINTOPIC_RANK_SOURCE_RANK.items():
        source_rank += f'{source.lower()}: {rank}\n'

    source_title = ''
    for article in articles:
        source_title += f'{article.source.lower()}: {article.title}\n'

    human_template = f'The following is a list of cryptocurrency news sources and their rank:\n'\
                     f'\n' \
                     f'{source_rank}\n' \
                     f'\n' \
                     f'\n' \
                     f'\n' \
                     f'The following is a list of headlines produces by the cryptocurrency news sources:\n' \
                     f'\n' \
                     f'{source_title}\n' \
                     f'\n' \
                     f'\n' \
                     f'\n' \
                     f'Your task is to summarize all they keypoints from the headlines and sort them by points.\n' \
                     f'Please note, since some headlines might discuss similar topics.\n' \
                     f'If the essence of those topics are the same, group them under a single keypoint.\n' \
                     f'Keypoints should be short and sweet, as in the headline of an article.\n'\
                     f'Do not generalize infromation in keypoints.\n' \
                     f'Remove any keypoints that cointain speculations.\n' \
                     f'Strictly, keep the keypoints within {config.MAINTOPIC_RANK_MAX_WORDS} words.\n' \
                     f'The points of a keypoint is calculated by summing all the cryptocurrency news source ranking number that they appear in.\n' \
                     f'Return your answer in this format:\n' \
                     f'\n' \
                     f'<points>:<keypoint>:<comma-separated list of sources>\n' \
                     f'<points>:<keypoint>:<comma-separated list of sources>\n' \
                     f'<points>:<keypoint>:<comma-separated list of sources>\n' \
                     f'\n'

    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                      model_name=config.MAINTOPIC_RANK_OPENAI_MODEL,
                      temperature=config.MAINTOPIC_RANK_OPENAI_TEMPERATURE,
                      request_timeout=config.MAINTOPIC_RANK_OPENAI_TIMEOUT)
    res = chat(prompt)

    lines = content_to_list(res.content)

    main_topics = list()

    for priority, line in enumerate(lines):

        if priority >= config.MAINTOPIC_RANK_MAX_TOPICS:
            break

        score = line.split(':')[0]
        keypoint = line.split(':')[1]
        sources = line.split(':')[2]

        maintopic_data = {
            'id': f'main_topic.rank.{priority:02}.{utils.sanitize_file_name(keypoint)}.yaml',
            'content': keypoint,
            'source': sources,
            'source_content': '',
            'datetime': config.ACTIVE_DATETIME_STR,
            'date': config.ACTIVE_TIME_STR,
            'time': config.ACTIVE_TIME_STR
        }

        main_topic = Topic(**maintopic_data)
        main_topics.append(main_topic)

    output_list = list()

    for main_topic in main_topics:
        output_list.append(f'{config.GETMAINTOPIC_RELATIVE_FOLDER}/{main_topic.id}')

        file_path = f'{config.GETMAINTOPIC_FOLDER}/{main_topic.id}'
        with open(file_path, 'w') as file:
            yaml.dump(main_topic.model_dump(), file, sort_keys=False)

        logging.info(f'saved  : {main_topic.id}')
        logging.info(f'content: {main_topic.content}')

    logging.info(f'[END  ] Get main topics')
    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

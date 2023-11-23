import logging
import yaml
import re

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.article import Article
from common.pydantic.topic import Topic
from config import config
from keys import keys


def extract_int(input_str):

    numbers = re.findall(r'\d+', input_str)

    if numbers:
        return int(numbers[0])
    else:
        logging.error(f'Unable to extract int from input_str: {input_str}')


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load ranked articles')

    articles = list()
    source_title = set()

    for article_file in sorted(input_list):
        file_path = f'{config.DATA_FOLDER}/{article_file}'

        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        article = Article(**yaml_data)

        if article.source.lower() in config.GETMAINTOPIC_RANK_SOURCE_RANK.keys():

            s_t = article.source.lower() + "." + utils.sanitize_file_name(article.title)

            if s_t not in source_title:
                source_title.add(s_t)
                articles.append(article)

    logging.info(f'[END  ] Load ranked articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Get main topics')

    main_topics = list()
    messages = list()

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

    for idx, article in enumerate(articles):

        system_template = f'You are a top editor for a cryptocurrency and AI news agency.' \
                          f' Your target audience ranges from enthusiasts to top cryptocurrency traders, fund managers, and AI investors,' \
                          f' who trusts in the objectiveness and fairness of your publication' \
                          f' to keep up to date with the latest happenings in the crypto and AI world.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        headline_str = ''
        for idx, main_topic in enumerate(main_topics):
            headline_str += f'Headline {idx}: {main_topic.content}\n'
        if headline_str == '':
            headline_str += '    <List is currently empty>'

        new_str = ''
        new_str = article.title

        human_template = f'The following is a list of cryptocurrency news articles that are to be published for the day:\n'\
                         f'\n' \
                         f'{headline_str}\n' \
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
                         f'<accepted/repeated/rejected>:<reason for accepting/index of headline repeated/reason for rejection>\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = chats[idx % len(chats)]
        res = chat(prompt)

        answer = res.content
        ret = answer.split(':')[0].strip().lower()
        i = answer.split(':')[1].strip()

        if ret == 'accepted' or ret == '<accepted>':

            maintopic_data = {
                # id is set as article.title temporarily. We will change it later
                'id': article.title,
                'content': article.title,
                'priority': 0,
                'priority_score': 0,
                'source': article.source,
                'source_content': '',
                'datetime': config.ACTIVE_DATETIME_STR,
                'date': config.ACTIVE_TIME_STR,
                'time': config.ACTIVE_TIME_STR
            }

            main_topic = Topic(**maintopic_data)
            main_topics.append(main_topic)

        elif ret == 'repeated' or ret == '<repeated>':

            main_topics[extract_int(i)].source += f',{article.source}'

        elif ret == 'rejected' or ret == '<rejected>':

            pass

        else:

            logging.error(f'Unknown response: {answer}')

        messages.append(f'Article:{article.title}')
        messages.append(f'Return :{ret}')
        messages.append(f'Reason :{idx}')
        messages.append(f'\n')

    for message in messages:
        logging.info(message)

    logging.info(f'[END  ] Get main topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Rank main topics')

    for main_topic in main_topics:
        sources = set(main_topic.source.split(','))
        for source in sources:
            main_topic.priority_score += config.GETMAINTOPIC_RANK_SOURCE_RANK[source.lower()]

    main_topics = sorted(main_topics, key=lambda x: x.priority_score, reverse=True)

    for idx, main_topic in enumerate(main_topics):
        main_topic.priority = idx
        main_topic.id = f'main_topic.rank.{idx:02}.{main_topic.priority_score:03}.{utils.sanitize_file_name(main_topic.content)}'

    logging.info(f'[BEGIN] Rank main topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Select first n main topics')

    main_topics = main_topics[:config.MAINTOPIC_RANK_MAX_TOPICS]

    logging.info(f'[BEGIN] Rank main topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save main topics')

    output_list = list()

    for main_topic in main_topics:
        output_list.append(f'{config.GETMAINTOPIC_RELATIVE_FOLDER}/{main_topic.id}')

        file_path = f'{config.GETMAINTOPIC_FOLDER}/{main_topic.id}'
        with open(file_path, 'w') as file:
            yaml.dump(main_topic.model_dump(), file, sort_keys=False)

        logging.info(f'saved  : {main_topic.id}')
        logging.info(f'content: {main_topic.content}')

    logging.info(f'[BEGIN] Save main topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

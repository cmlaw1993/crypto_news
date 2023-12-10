import logging
import yaml
import re

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.article import Article
from common.pydantic.topic import Topic
from config import config
from _keys import keys


def remove_brackets(input_str):
    ret = input_str
    if ret[0] in ['(', '{', '<']:
        ret = ret[1:]
    if ret[-1] in [')', '}', '>']:
        ret = ret[:-1]
    return ret


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

            # Remove the same article from different API provider
            s_t = article.source.lower() + "." + utils.sanitize_file_name(article.title)
            if s_t not in source_title:
                source_title.add(s_t)
                articles.append(article)

    logging.info(f'[END  ] Load ranked articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Convert to topics')

    topics = list()

    for article in articles:

        maintopic_data = {
            # id is set as article.title temporarily. We will change it later
            'id': article.title,
            'content': article.title,
            'priority': 0,
            'priority_score': 0,
            'sources': [article.source],
            'source_content': [],
            'reason': '',
            'datetime': config.ACTIVE_DATETIME_STR,
            'date': config.ACTIVE_DATE_STR,
            'time': config.ACTIVE_TIME_STR
        }

        topic = Topic(**maintopic_data)
        topics.append(topic)

    logging.info(f'[END  ] Convert to topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Screen topics')

    chats = [
        ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                   model_name=config.GETMAINTOPIC_RANK_OPENAI_MODEL,
                   temperature=config.GETMAINTOPIC_RANK_OPENAI_TEMPERATURE,
                   request_timeout=config.GETMAINTOPIC_RANK_OPENAI_TIMEOUT),
        ChatOpenAI(openai_api_key=keys.OPENAI_KEY_1,
                   model_name=config.GETMAINTOPIC_RANK_OPENAI_MODEL,
                   temperature=config.GETMAINTOPIC_RANK_OPENAI_TEMPERATURE,
                   request_timeout=config.GETMAINTOPIC_RANK_OPENAI_TIMEOUT)
    ]

    screened_topics = list()
    descreened_topics = list()

    for i, source in enumerate(config.GETMAINTOPIC_RANK_SOURCE_RANK.keys()):

        logging.info(f'Screening articles from {source}')

        system_template = f'You are an assistant to a top editor for a cryptocurrency and AI news agency.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        active_topic = list()
        topic_str = ''
        idx = 0
        for topic in topics:
            if topic.sources[0].lower() != source.lower():
                continue
            active_topic.append(topic)
            topic_str += f'Article {idx}: {topic.content}\n'
            idx += 1

        human_template = f'The following is a list of cryptocurrency and AI news articles that are to be published for the day:\n' \
                         f'\n' \
                         f'{topic_str}\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'Your task is to perform a screening of each of the articles above and determine if they are to be accepted or rejected for the day\'s publication.\n' \
                         f'You must accept or reject each of the articles given a set of criteria given by the editor.\n' \
                         f'If you do not know, or cannot make a proper determination, accept the articles anyways. The editor will make a second screening.\n' \
                         f'An article can be rejected only and only if it meets any of the the following criteria from the editor:\n' \
                         f'\n' \
                         f'1. The article is about price prediction or analysis of a token.\n' \
                         f'2. The article is a promotion for a token, company or entity.\n' \
                         f'3. The article discusses multiple unrelated topics.\n' \
                         f'4. The article is a tutorial or a how-to.\n' \
                         f'5. The article is a repetition of another article before it.\n' \
                         f'\n' \
                         f'Only return your answer in this format:\n' \
                         f'\n' \
                         f'<idx>::<accepted/rejected>::<reason for accepting/rejecting>\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = chats[i % len(chats)]
        res = chat(prompt)

        answer = res.content
        ans_lines = answer.split('\n')

        last_idx = -1
        for line in ans_lines:

            parts = line.split('::')
            if len(parts) < 2:
                logging.warning(f'Bad openai output: {line}')
                continue

            idx = extract_int(remove_brackets(parts[0].strip()))
            yn = remove_brackets(parts[1].strip())

            if idx != last_idx + 1:
                logging.warning(f'Idx jumped from {last_idx} to {idx}')
            last_idx += 1

            if 'accept' in yn.lower():
                screened_topics.append(active_topic[idx])
            else:
                active_topic[idx].reason = remove_brackets(parts[2].strip())
                descreened_topics.append(active_topic[idx])

    for topic in screened_topics:
        logging.info(f'Screened  : {topic.content}')
    for topic in descreened_topics:
        logging.info(f'Descreened: {topic.content}')
        logging.info(f'          : {topic.reason}')

    topics = list(screened_topics)

    logging.info(f'[END  ] Screen articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Find common topics')

    common_topics = list()
    uncommon_topics = list()

    for i in range(config.GETMAINTOPIC_RANK_COMMONTOPIC_MAXLOOPS):

        logging.info(f'Running loop {i} of {config.GETMAINTOPIC_RANK_COMMONTOPIC_MAXLOOPS}.')

        tmp_common_topics = list()
        tmp_uncommon_topics = list()

        system_template = f'You are an assistant to a top editor for a cryptocurrency and AI news agency.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        topic_str = ''
        idx = 0
        for source in config.GETMAINTOPIC_RANK_SOURCE_RANK.keys():
            topic_str += f'\n\n\n\n'
            topic_str += f'Source: {source.lower()}\n\n'
            for topic in topics:
                if topic.sources[0].lower() != source.lower():
                    continue
                topic_str += f'\tArticle {idx}: {topic.content}\n'
                idx += 1

        human_template = f'The following is a list of cryptocurrency and AI article headlines from various sources:\n' \
                         f'\n' \
                         f'{topic_str}\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'\n' \
                         f'Your task is to find articles that are common across sources and group them\n' \
                         f'If you are unable to determine if an article and another are common, assume that they are different. The editor will make a second screening.\n'\
                         f'\n' \
                         f'Only return your answer in this format:\n' \
                         f'\n' \
                         f'<Group idx>\n' \
                         f'\t<Article idx>::<Article source>::<Article headline>\n' \
                         f'\t<Article idx>::<Article source>::<Article headline>\n' \
                         f'\n'

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        chat = chats[i % len(chats)]
        res = chat(prompt)

        answer = res.content
        ans_lines = answer.split('\n')

        topic = None
        used_idx = list()

        for line in ans_lines:

            if len(line) < 2:
                continue

            if line[0] != '\t':
                if topic is not None:
                    tmp_common_topics.append(topic.copy())

                topic = Topic(
                    id='',
                    content = '',
                    priority = 0,
                    priority_score = 0,
                    sources = [],
                    source_content = [],
                    reason = '',
                    datetime = config.ACTIVE_DATETIME_STR,
                    date = config.ACTIVE_DATE_STR,
                    time = config.ACTIVE_TIME_STR,
                )

            else:
                parts = line.split('::')
                idx = extract_int(remove_brackets(parts[0].strip()))
                source = remove_brackets(parts[1].strip()).lower()
                headline = remove_brackets(parts[2].strip())

                if topic.content == '':
                    topic.content = headline
                topic.sources.append(source)
                topic.source_content.append(f'{source}:{topics[idx].content}')
                topic.priority_score += config.GETMAINTOPIC_RANK_SOURCE_RANK[source]

                used_idx.append(idx)

        if topic is not None and topic.id != '':
            tmp_common_topics.append(topic.copy())

        for idx, topic in enumerate(topics):
            if idx not in used_idx:
                tmp_uncommon_topics.append(topic.copy())

        if len(tmp_common_topics) > len(common_topics):
            common_topics = list(tmp_common_topics)
            uncommon_topics = list(tmp_uncommon_topics)

    for topic in common_topics:
        logging.info(f'Common  : {topic.content}')
    for topic in uncommon_topics:
        logging.info(f'Uncommon: {topic.content}')

    topics = list(common_topics)

    logging.info(f'[END  ] Find common topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Rank topics')

    topics = sorted(topics, key=lambda x: x.priority_score, reverse=True)

    for idx, topic in enumerate(topics):
        topic.priority = idx
        topic.id = f'main_topic.rank.{idx:02}.{topic.priority_score:03}.{utils.sanitize_file_name(topic.content)}'

    logging.info(f'[BEGIN] Rank topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save topics')

    output_list = list()

    for topic in topics:
        output_list.append(f'{config.GETMAINTOPIC_RELATIVE_FOLDER}/{topic.id}')

        file_path = f'{config.GETMAINTOPIC_FOLDER}/{topic.id}'
        with open(file_path, 'w') as file:
            yaml.dump(topic.model_dump(), file, sort_keys=False)

        logging.info(f'saved  : {topic.id}')
        logging.info(f'content: {topic.content}')

    logging.info(f'[BEGIN] Save topics')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

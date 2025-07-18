from datetime import timedelta
import logging
import nltk
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.topic import Topic
from common.pydantic.digest import Digest
from config import config
from _keys import keys


def run(clean, input_list):

    logging.info(f'{config.CONSTRUCTDIGEST_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.CONSTRUCTDIGEST_FOLDER):
        try:
            os.makedirs(config.CONSTRUCTDIGEST_FOLDER)
            logging.info(f'Created folder: {config.CONSTRUCTDIGEST_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.CONSTRUCTDIGEST_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.CONSTRUCTDIGEST_FOLDER}/*')
        logging.info(f'Cleaned: {config.CONSTRUCTDIGEST_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load main topic')

    main_topics = list()

    for main_topic_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{main_topic_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        main_topic = Topic(**yaml_data)
        main_topics.append(main_topic)

    logging.info(f'[END  ] Load main topic')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Construct digest')

    digests = list()

    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize

    vector_db = config.VECTORDB_GET_INST()

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

    for idx, main_topic in enumerate(main_topics):

        logging.info(f'Constructing digest: {main_topic.id}')

        # Get news contents

        docs = vector_db.similarity_search_with_relevance_scores(query=f'{main_topic.content}', k=config.CONSTRUCTDIGEST_NUM_DOCS)

        info = ''
        articles = list()

        for doc in docs:
            info += (doc[0].page_content) + "\n\n"
            articles.append(doc[0].metadata['file'])

        system_template = f'You are a top editor for a cryptocurrency and AI news agency.' \
                          f' Your target audience ranges from enthusiasts to top cryptocurrency traders, fund managers, and AI investors,' \
                          f' who trusts in the objectiveness and fairness of your publication' \
                          f' to keep up to date with the latest happenings in the crypto and AI world.\n' \
                          '\n' \
                          'Use the following information from the last day to answer the question. If you do not know the answer, simply say you do not know.\n' \
                          '\n' \
                          'Information from the last day:\n' \
                          '\n' \
                          '{information}\n' \
                          '\n' \
                          '\n'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        # human_template = 'Topic: {topic}\n' \
        #                  '\n' \
        #                  'Please write a news article for the above topic for today.\n' \
        #                  'The news article must be within {min_num_sentences} to {max_num_sentences} sentences long.\n' \
        #                  'Each sentence must be within {min_num_words} to {max_num_words} words.\n' \
        #                  'Each sentence must be void of price speculation and opinions.\n' \
        #                  'Each sentence must be factual and provide useful information to your target audience.\n' \
        #                  'Prefer information corroborated from multiple lines of information.\n' \
        #                  'Prefer objective facts and figures in each of your sentences.\n' \
        #                  'Do not lift sentences. Paraphrase to avoid plagiarism.\n' \
        #                  'Ensure a logical continuity between sentences.\n' \
        #                  'Assume the article is a one-off.\n' \
        #                  'Write only the contents of the article. Do not write the title.'
        human_template = 'Topic: {topic}\n' \
                         '\n' \
                         'Please write a news article for the above topic for today.\n' \
                         'The news article must be within {min_num_sentences} to {max_num_sentences} sentences long.\n' \
                         'Each sentence must be within {min_num_words} to {max_num_words} words.\n' \
                         'Each sentence must be factual and provide useful information to your target audience.\n' \
                         'Prefer information corroborated from multiple lines of information.\n' \
                         'Prefer objective facts and figures in each of your sentences.\n' \
                         'Do not lift sentences. Paraphrase to avoid plagiarism.\n' \
                         'Ensure a logical continuity between sentences.\n' \
                         'Assume the article is a one-off.\n' \
                         'Write only the contents of the article. Do not write the title.'
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt(
            information=info,
            topic=main_topic.content,
            min_num_sentences=config.CONSTRUCTDIGEST_CONTENT_MIN_NUM_SENTENCES,
            max_num_sentences=config.CONSTRUCTDIGEST_CONTENT_MAX_NUM_SENTENCES,
            min_num_words=config.CONSTRUCTDIGEST_CONTENT_MIN_NUM_WORDS_PER_SENTENCE,
            max_num_words=config.CONSTRUCTDIGEST_CONTENT_MAX_NUM_WORDS_PER_SENTENCE
        ).to_messages()

        chat = chats[idx % len(chats)]
        res = chat(prompt)
        article_content = res.content

        # Infer title from news content

        system_template = f'You are a top editor for a cryptocurrency and AI news agency.' \
                          f' Your target audience ranges from enthusiasts to top cryptocurrency traders, fund managers, and AI investors,' \
                          f' who trusts in the objectiveness and fairness of your publication' \
                          f' to keep up to date with the latest happenings in the crypto and AI world.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = f'Write a short and compelling title within {config.CONSTRUCTDIGEST_TITLE_MIN_NUM_WORDS_PER_SENTENCE} to {config.CONSTRUCTDIGEST_TITLE_MAX_NUM_WORDS_PER_SENTENCE} words, for the news article below:\n'\
                         f'\n'\
                         f'{article_content}'
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        res = chat(prompt)
        title = res.content

        while True:
            if title[0] == "'" and title[-1] == "'":
                title = title[1:-1]
                continue
            if title[0] == '"' and title[-1] == '"':
                title = title[1:-1]
                continue
            break

        # Infer oneliner from news content

        system_template = f'You are a top editor for a cryptocurrency and AI news agency.' \
                          f' Your target audience ranges from enthusiasts to top cryptocurrency traders, fund managers, and AI investors,' \
                          f' who trusts in the objectiveness and fairness of your publication' \
                          f' to keep up to date with the latest happenings in the crypto and AI world.'
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = f'Write a oneline summary {config.CONSTRUCTDIGEST_ONELINER_MIN_NUM_WORDS_PER_SENTENCE} to {config.CONSTRUCTDIGEST_ONELINER_MAX_NUM_WORDS_PER_SENTENCE} words, for the news article below:\n' \
                         f'\n' \
                         f'{title}\n' \
                         f'{article_content}'
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        prompt = chat_prompt.format_prompt().to_messages()

        res = chat(prompt)
        oneliner = res.content

        while True:
            if oneliner[0] == "'" and oneliner[-1] == "'":
                oneliner = oneliner[1:-1]
                continue
            if oneliner[0] == '"' and oneliner[-1] == '"':
                oneliner = oneliner[1:-1]
                continue
            break

        # Construct pydantic object

        priority = main_topic.priority
        priority_score = main_topic.priority_score

        digest_data = {
            'id': f'digest.{priority:02}.{priority_score:03}.{utils.sanitize_file_name(title)}.yaml',
            'main_topic': main_topic.content,
            'main_topic_source_content': main_topic.source_content,
            'title': title,
            'oneliner': oneliner,
            'content': sent_tokenize(article_content),
            'sources': main_topic.sources,
            'source_content': main_topic.source_content,
            'articles': articles,
            'priority': priority,
            'priority_score': priority_score,
            'datetime': config.ACTIVE_DATETIME_STR,
            'date': config.ACTIVE_DATE_STR,
            'time': config.ACTIVE_TIME_STR,
        }

        digest = Digest(**digest_data)
        digests.append(digest)

    logging.info(f'[END  ] Construct digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digest')

    output_list = list()

    for digest in digests:

        output_list.append(f'{config.CONSTRUCTDIGEST_RELATIVE_FOLDER}/{digest.id}')

        file_path = f'{config.CONSTRUCTDIGEST_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {file_path}')

    logging.info(f'[END  ] Save digest')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.CONSTRUCTDIGEST_NAME} ended')

    return output_list

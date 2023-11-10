import logging
import yaml
import os

from langchain.text_splitter import CharacterTextSplitter

from common import utils
from common.pydantic.article import Article
from config import config

def run(clean, input_list):

    logging.info(f'b_news_to_vectordb/news_to_vectordb started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.NEWSTOVECTORDB_FOLDER):
        try:
            os.makedirs(config.NEWSTOVECTORDB_FOLDER)
            logging.info(f'Created folder: {config.NEWSTOVECTORDB_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.NEWSTOVECTORDB_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.NEWSTOVECTORDB_FOLDER}/*')
        logging.info(f'Cleaned: {config.NEWSTOVECTORDB_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load articles')

    articles = dict()
    used_file_path = dict()
    unused_file_path = set()

    for article_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{article_file}'

        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        article = Article(**yaml_data)
        title = utils.sanitize_file_name(article.title)

        # Replace existing article if the current one has more data

        replace = False

        if title not in articles.keys():
            replace = True

        else:
            curr_content_len = 0
            if article.content is not None:
                curr_content_len = len(article.content)

            curr_description_len = 0
            if article.description is not None:
                curr_description_len = len(article.description)

            existing_content_len = 0
            if articles[title].content is not None:
                existing_content_len = len(articles[title].content)

            existing_description_len = 0
            if articles[title].description is not None:
                existing_description_len = len(articles[title].description)

            if curr_content_len > existing_content_len:
                replace = True
            elif curr_content_len == existing_content_len:
                if curr_description_len > existing_description_len:
                    replace = True

        if replace == True:
            articles[title] = article

            if title in used_file_path.keys():
                unused_file_path.add(used_file_path[title])

            used_file_path[title] = file_path

    articles = dict(sorted(articles.items()))
    used_file_path = dict(sorted(used_file_path.items()))
    unused_file_path = sorted(unused_file_path)

    for file_path in used_file_path.values():
        logging.info(f'Used  : {file_path}')

    for file_path in unused_file_path:
        logging.info(f'Unused: {file_path}')

    logging.info(f'[END  ] Load articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Construct save data')

    article_data = dict()

    for title, article in articles.items():

        data_string = ''

        data_raw = [
            article.title,
            article.description,
            article.content
        ]

        for raw in data_raw:
            if raw is not None:
                data_string += raw
                if data_string[-1] != '.':
                    data_string += '. '
                else:
                    data_string += ' '

        text_splitter = CharacterTextSplitter(chunk_size=config.NEWSTOVECTORDB_CHUNK_SIZE,
                                              chunk_overlap=config.NEWSTOVECTORDB_CHUNK_OVERLAP,
                                              separator=' ')
        texts = text_splitter.split_text(data_string)
        ids = list()
        metadatas = list()

        for i in range(len(texts)):
            id = f'{article.id}_{i}'
            metadata = {
                'published_datetime': article.datetime,
                'published_date': article.date,
                'published_time': article.time,
                'active_date': config.ACTIVE_DATE_STR,
                'file': article.id,
                'id': id
            }
            ids.append(id)
            metadatas.append(metadata)

        data = dict()
        data['texts'] = texts
        data['ids'] = ids
        data['metadatas'] = metadatas

        article_data[title] = data

    logging.info(f'[END  ] Construct data')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate tokens and costs')

    total_tokens = 0

    for title, data in article_data.items():

        file = used_file_path[title]
        texts = data['texts']

        tokens = 0
        for text in texts:
            tokens += utils.count_tokens(config.VECTORDB_EMBEDDINGS_MODEL, text)
        total_tokens += tokens

        logging.info(f'Tokens: {tokens:>6}, {file}')

    total_cost = total_tokens * config.VECTORDB_EMBEDDINGS_COST

    logging.info(f'total_articles: {len(article_data)}')
    logging.info(f'total_tokens  : {total_tokens}')
    logging.info(f'total_cost    : {total_cost}')

    if total_cost > config.NEWSTOVECTORDB_MAX_COST:
        logging.error(f'Total cost is above ${config.NEWSTOVECTORDB_MAX_COST}')

    logging.info(f'[END  ] Calculate tokens and costs')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Initialize vector_db')

    vector_db = config.VECTORDB_GET_INST()

    logging.info(f'[END  ] Initialize vector_db')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Delete current datetime documents')

    num_deleted = 0

    while True:
        documents = vector_db.similarity_search(query='', k=4, filter={'active_date': config.ACTIVE_DATE_STR})
        if len(documents) == 0:
            break

        ids = list()
        for document in documents:
            ids.append(document.metadata['id'])
        vector_db.delete(ids)
        vector_db.persist()

        num_deleted += len(documents)
        logging.info(f'Deleted: {num_deleted}')

    logging.info(f'[END  ] Delete current datetime documents')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save articles to vector db')

    count = 0
    texts = list()
    metadatas = list()
    ids = list()

    for title, data in article_data.items():

        file = used_file_path[title]
        texts += data['texts']
        metadatas += data['metadatas']
        ids += data['ids']

        count += 1

        if count % 100 == 0 or count == len(article_data):

            vector_db.add_texts(texts, metadatas, ids)
            vector_db.persist()

            texts = list()
            metadatas = list()
            ids = list()

            logging.info(f'Saved: {count:>4}/{len(article_data)} {file}')

    logging.info(f'[END  ] Save articles to vector db')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'b_news_to_vectordb/news_to_vectordb ended')

    return input_list

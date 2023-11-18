from datetime import datetime
import logging
import pytz
import yaml

from newsdataapi import NewsDataApiClient

from common import utils
from common.pydantic.article import Article
from config import config
from keys import keys


def run(start_dt, end_dt):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Download news for newsdata_all')

    articles = list()
    page = None
    response = list()

    news_data = NewsDataApiClient(apikey=keys.NEWSDATA_KEY)

    while True:

        utc_dt = None

        try:
            response = news_data.crypto_api(language='en',
                                            excludedomain=config.DOWNLOADNEWS_NEWSDATA_EXCLUDEDOMAIN,
                                            size=50,
                                            page=page)
        except:
            logging.error('Downloading articles from NewsData.io failed')

        for result in response['results']:

            utc_dt = datetime.strptime(result['pubDate'], '%Y-%m-%d %H:%M:%S')
            utc_dt = utc_dt.astimezone(pytz.timezone('UTC'))

            if not (start_dt < utc_dt <= end_dt):
                continue

            date_str = utc_dt.strftime('%Y%m%d')
            time_str = utc_dt.strftime('%H%M%S')
            datetime_str = utc_dt.strftime('%Y%m%d_%H%M%S')

            sanitized_headline = utils.sanitize_file_name(result['title'])

            id = f'article.newsdata.all.{result["source_id"].replace(" ", "")}.{date_str}.{time_str}.{sanitized_headline}.yaml'

            content = None
            if result['content'] is not None:
                content = result['content']

            author = result['source_id']
            if result['creator'] is not None:
                author = result['creator'][0]

            image_link = None
            if result['image_url'] is not None:
                image_link = result['image_url']

            video_link = None
            if result['video_url'] is not None:
                video_link = result['video_url']

            article_data = {
                'id': id,
                'title': result['title'],
                'content': content,
                'api': 'newsdata',
                'api_type': 'all',
                'source': result['source_id'],
                'author': author,
                'description': result['description'],
                'category': result['category'],
                'keywords': result['keywords'],
                'country': result['country'],
                'language': result['language'],
                'news_link': result['link'],
                'image_link': image_link,
                'video_link': video_link,
                'datetime': datetime_str,
                'date': date_str,
                'time': time_str,
            }

            article = Article(**article_data)
            articles.insert(0, article)

        if utc_dt < start_dt:
            break

        page = str(response.get('nextPage', None))
        if page == 'None':
            break

    output_list = set()

    for article in articles:

        output = f'{config.DOWNLOADNEWS_RELATIVE_FOLDER}/{article.id}'
        if output in output_list:
            continue

        output_list.add(output)

        file_path = f'{config.DOWNLOADNEWS_FOLDER}/{article.id}'
        with open(file_path, 'w') as file:
            yaml.dump(article.model_dump(), file, sort_keys=False)

        logging.info(f'Downloaded: {article.id}')

    logging.info(f'[END  ] Download news for newsdata_all')

    return list(output_list)

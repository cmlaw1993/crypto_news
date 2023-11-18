from datetime import datetime
import requests
import logging
import pytz
import yaml

from common import utils
from common.pydantic.article import Article
from config import config
from keys import keys


def run(start_dt, end_dt):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Download news for cyrptonewsapi_alltickernews')

    articles = list()

    page = 0

    while True:

        page += 1
        if page > config.DOWNLOADNEWS_CRYPTONEWSAPI_MAXPAGES:
            logging.error(f'Attempted to query past {config.DOWNLOADNEWS_CRYPTONEWSAPI_MAXPAGES} pages')

        url = f'https://cryptonews-api.com/api/v1/category?section=alltickers&type=article&items=100&page={page}&token={keys.CRYPTONEWSAPI_KEY}'
        response = None
        utc_dt = None

        try:
            response = requests.get(url)
        except:
            logging.error(f'Http request error, url:{url}')

        if response.status_code != 200:
            logging.error(f'Http request returned error, url:{url}, status_code:{response.status_code}, text:{response.text}')

        response_json = response.json()
        response_data = response_json['data']

        for data in response_data:

            tz_dt = datetime.strptime(data['date'], '%a, %d %b %Y %H:%M:%S %z')
            utc_dt = tz_dt.astimezone(pytz.timezone('UTC'))

            if not (start_dt < utc_dt <= end_dt):
                continue

            datetime_str = utc_dt.strftime('%Y%m%d_%H%M%S')
            date_str = utc_dt.strftime('%Y%m%d')
            time_str = utc_dt.strftime('%H%M%S')

            sanitized_headline = utils.sanitize_file_name(data['title'])

            id = f'article.cryptonewsapi.alltickernews.{data["source_name"].replace(" ", "")}.{date_str}.{time_str}.{sanitized_headline}.yaml'

            article_data = {
                'id': id,
                'title': data['title'],
                'content': data['text'],
                'api': 'cryptonewsapi',
                'api_type': 'alltickernews',
                'source': data['source_name'],
                'author': data['source_name'],
                'keywords': data['topics'],
                'news_url': data['news_url'],
                'image_url': data['image_url'],
                'datetime': datetime_str,
                'date': date_str,
                'time': time_str,
            }

            article = Article(**article_data)
            articles.insert(0, article)

        if utc_dt < start_dt:
            break

    if len(articles) == 0:
        logging.error('There are 0 articles for current datetime')

    output_list = list()

    for article in articles:

        output = f'{config.DOWNLOADNEWS_RELATIVE_FOLDER}/{article.id}'
        if output in output_list:
            continue

        output_list.append(output)

        file_path = f'{config.DOWNLOADNEWS_FOLDER}/{article.id}'
        with open(file_path, 'w') as file:
            yaml.dump(article.model_dump(), file, sort_keys=False)

        logging.info(f'Downloaded: {article.id}')

    logging.info(f'[END  ] Download news for cyrptonewsapi_alltickernews')

    return output_list

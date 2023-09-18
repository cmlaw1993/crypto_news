from datetime import datetime, timedelta
import logging
import shutil
import json
import os

from newsdataapi import NewsDataApiClient

from core import log, utils
from config import config
from keys import keys


if __name__ == "__main__":

    log.init_logging()
    logging.info(f"News scraper started")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Loading config")

    logging.info(f"active_datetime: {config.ACTIVE_DATETIME}")
    logging.info(f"vardata_folder: {config.VARDATA_FOLDER}")
    logging.info(f"raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Loading config")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Check vardata_folder")

    if os.path.exists(config.VARDATA_FOLDER):
        logging.info("vardata_folder exists")
    else:
        logging.info("vardata_folder does not exists")
        try:
            os.mkdir(config.VARDATA_FOLDER)
        except:
            logging.error(f"Unable to create vardata_folder: {config.VARDATA_FOLDER}")

        logging.info(f"Created vardata_folder: {config.VARDATA_FOLDER}")

    logging.info(f"[END  ] Check vardata_folder")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Check raw_articles_folder")

    if os.path.exists(config.RAW_ARTICLES_FOLDER):
        logging.info("raw_articles_folder exists")
    else:
        logging.info("raw_articles_folder does not exists")
        try:
            os.mkdir(config.RAW_ARTICLES_FOLDER)
        except:
            logging.error(f"Unable to create raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")

        logging.info(f"Created raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Check raw_articles_folder")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Calculated start and end datetime")

    start_datetime = config.ACTIVE_DATETIME
    end_datetime = config.ACTIVE_DATETIME + timedelta(days=1)

    logging.info(f"start_datetime: {start_datetime.strftime('%Y%m%d_%H%M%S')}")
    logging.info(f"end_datetime:   {end_datetime.strftime('%Y%m%d_%H%M%S')}")

    logging.info(f"[END  ] Calculated start and end datetime")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Scraping news")

    articles = list()
    page = None
    response = list()
    published_datetime = 0

    news_data = NewsDataApiClient(apikey=keys.NEWSDATA_KEY)

    while True:

        try:
            response = news_data.crypto_api(language="en",
                                            full_content=True,
                                            prioritydomain="top",
                                            excludedomain="youtube.com",
                                            page=page)
        except:
            logging.error("Downloading articles from NewsData.io failed")

        for result in response["results"]:

            published_datetime = datetime.strptime(result["pubDate"], "%Y-%m-%d %H:%M:%S")

            if not (start_datetime < published_datetime <= end_datetime):
                continue

            group_datetime = published_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            group_datetime = group_datetime.strftime('%Y%m%d')

            articles.insert(0, result)

        if published_datetime < start_datetime:
            break

        page = str(response.get("nextPage", None))
        if page == "None":
            break

    for article in articles:

        source = article["source_id"]
        dt = datetime.strptime(article["pubDate"], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d_%H%M%S')
        title = utils.sanitize_file_name(article["title"])
        title = title.replace(".", "")

        file_name = f"{config.RAW_ARTICLES_FOLDER}/{source}.{dt}.{title}.json"
        out_file = open(file_name, "w")
        json.dump(article, out_file, indent=4)
        out_file.close()

        logging.info(f"Dumped raw article: {file_name}")

    logging.info(f"[END  ] Scraping news")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"News scraper ended")

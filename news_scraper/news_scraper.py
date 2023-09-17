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

    logging.info(f"raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Loading config")

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

    logging.info(f"[BEGIN] Get last_datetime")

    datetime_files = os.listdir(config.RAW_ARTICLES_FOLDER)

    for dt_file in datetime_files:
        if ".tmp" in dt_file:
            shutil.rmtree(f"{config.RAW_ARTICLES_FOLDER}/{dt_file}")
            datetime_files.remove(dt_file)

    if len(datetime_files) == 0:
        datetime_files.append("19700101")

    datetime_files.sort()

    last_datetime = datetime.strptime(datetime_files[-1], '%Y%m%d')
    last_datetime += timedelta(days=1)

    logging.info(f"last_datetime: {last_datetime.strftime('%Y%m%d_%H%M%S')}")

    logging.info(f"[END  ] Get last_datetime")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Get curr_datetime")

    curr_datetime = current_utc_time = datetime.now()
    curr_datetime = curr_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

    logging.info(f"curr_datetime: {curr_datetime.strftime('%Y%m%d_%H%M%S')}")

    logging.info(f"[END  ] Get curr_datetime")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Verifying last_datetime to curr_datetime delta")

    delta = curr_datetime - last_datetime

    logging.info(f"delta: {delta}")

    if delta < timedelta(days=1):
        logging.info(f"delta < 1 day, program shall terminate")
        exit(0)

    logging.info(f"delta >= 1 day, program shall continue")

    logging.info(f"[END  ] Verifying last_datetime to curr_datetime delta")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Scraping news")

    article_dict = dict()
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

            if not (last_datetime < published_datetime <= curr_datetime):
                continue

            group_datetime = published_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            group_datetime = group_datetime.strftime('%Y%m%d')

            if group_datetime not in article_dict:
                article_dict[group_datetime] = list()

            article_dict[group_datetime].insert(0, result)

        if published_datetime < last_datetime:
            break

        page = str(response.get("nextPage", None))
        if page == "None":
            break

    for group_datetime, articles in article_dict.items():

        folder = f"{config.RAW_ARTICLES_FOLDER}/{group_datetime}"
        folder_tmp = f"{folder}.tmp"

        if not os.path.exists(folder_tmp):
            try:
                os.makedirs(folder_tmp)
                logging.info(f"Created folder: {folder_tmp}")
            except:
                logging.error(f"Unable to create folder: {folder_tmp}")

        for article in articles:

            source = article["source_id"]
            dt = datetime.strptime(article["pubDate"], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d_%H%M%S')
            title = utils.sanitize_file_name(article["title"])
            title = title.replace(".", "")

            file_name = f"{folder_tmp}/{source}.{dt}.{title}.json"
            out_file = open(file_name, "w")
            json.dump(article, out_file, indent=4)
            out_file.close()

            logging.info(f"Dumped raw article: {file_name}")

        os.rename(folder_tmp, folder)
        logging.info(f"Renamed {folder_tmp} to {folder}")

    logging.info(f"[END  ] Scraping news")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"News scraper ended")

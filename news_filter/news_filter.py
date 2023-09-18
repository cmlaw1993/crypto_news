from datetime import datetime, timedelta
import logging
import shutil
import json
import os

from core import log, utils
from config import config

if __name__ == "__main__":

    log.init_logging()
    logging.info(f"News filter started")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Get active_datetime")

    active_datetime = datetime.strptime(os.getenv('ACTIVE_DATETIME'), '%Y%m%d')

    logging.info(f"active_datetime: {active_datetime.strftime('%Y%m%d_%H%M%S')}")

    logging.info(f"[END  ] Get active_datetime")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Loading config")

    raw_articles_dt_folder = f"{config.RAW_ARTICLES_FOLDER}/{active_datetime.strftime('%Y%m%d')}"
    accepted_articles_dt_folder = f"{config.ACCEPTED_ARTICLES_FOLDER}/{active_datetime.strftime('%Y%m%d')}"
    rejected_articles_dt_folder = f"{config.REJECTED_ARTICLES_FOLDER}/{active_datetime.strftime('%Y%m%d')}"

    logging.info(f"raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")
    logging.info(f"raw_articles_dt_folder: {raw_articles_dt_folder}")
    logging.info(f"accepted_articles_folder: {config.ACCEPTED_ARTICLES_FOLDER}")
    logging.info(f"accepted_articles_dt_folder: {accepted_articles_dt_folder}")
    logging.info(f"rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")
    logging.info(f"rejected_articles_dt_folder: {rejected_articles_dt_folder}")

    logging.info(f"[END  ] Loading config")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Check accepted_articles_folder")

    if os.path.exists(config.ACCEPTED_ARTICLES_FOLDER):
        logging.info("accepted_articles_folder exists")
    else:
        logging.info("accepted_articles_folder does not exists")

        try:
            os.mkdir(config.ACCEPTED_ARTICLES_FOLDER)
        except:
            logging.error(f"Unable to create accepted_articles_folder: {config.ACCEPTED_ARTICLES_FOLDER}")

        logging.info(f"Created accepted_articles_folder: {config.ACCEPTED_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Check accepted_articles_folder")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Check rejected_articles_folder")

    if os.path.exists(config.REJECTED_ARTICLES_FOLDER):
        logging.info("rejected_articles_folder exists")
    else:
        logging.info("rejected_articles_folder does not exists")

        try:
            os.mkdir(config.REJECTED_ARTICLES_FOLDER)
        except:
            logging.error(f"Unable to create rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")

        logging.info(f"Created rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Check rejected_articles_folder")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Recreate accepted_articles_dt_folder")

    if os.path.exists(accepted_articles_dt_folder):
        shutil.rmtree(f"{accepted_articles_dt_folder}")
        logging.info(f"Deleted accepted_articles_dt_folder: {accepted_articles_dt_folder}")

    os.mkdir(accepted_articles_dt_folder)
    logging.info(f"Created accepted_articles_dt_folder: {accepted_articles_dt_folder}")

    logging.info(f"[END  ] Recreate accepted_articles_dt_folder")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Recreate rejected_articles_dt_folder")

    if os.path.exists(rejected_articles_dt_folder):
        shutil.rmtree(f"{rejected_articles_dt_folder}")
        logging.info(f"Deleted rejected_articles_dt_folder: {rejected_articles_dt_folder}")

    os.mkdir(rejected_articles_dt_folder)
    logging.info(f"Created rejected_articles_dt_folder: {rejected_articles_dt_folder}")

    logging.info(f"[END  ] Recreate rejected_articles_dt_folder")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Load raw_articles")

    if not os.path.exists(raw_articles_dt_folder):
        logging.error(f"raw_articles_dt_folder does not exists: {raw_articles_dt_folder}")

    files = os.listdir(raw_articles_dt_folder)

    raw_articles = dict()

    for f in files:

        file_name = f"{raw_articles_dt_folder}/{f}"

        with open(file_name, "r") as file:
            raw_articles[f] = json.load(file)

        logging.info(f"Loaded raw_article: {f}")

    logging.info(f"[END  ] Load raw_articles")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Filter select_by_source_id")

    accepted_articles = dict()

    for f, raw_article in raw_articles.items():
        if raw_article["source_id"] in config.FILTER_SELECT_BY_SOURCE_ID:
            accepted_articles[f] = raw_article
            logging.info(f"Selected: {f}")

    if len(accepted_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter select_by_source_id")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Filter remove_by_keywords")

    removed_articles = set()

    for f, article in accepted_articles.items():
        for article_keyword in article["keywords"]:
            for filter_keyword in config.FILTER_REMOVE_BY_KEYWORDS:
                if filter_keyword.lower() in article_keyword.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        accepted_articles.pop(f)
        logging.info(f"Removed: {f}")

    if len(accepted_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter remove_by_keywords")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Filter remove_by_title")

    removed_articles = set()

    for f, article in accepted_articles.items():
        for article_title in article["title"]:
            for filter_title in config.FILTER_REMOVE_BY_TITLE:
                if filter_title.lower() in article_title.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        accepted_articles.pop(f)
        logging.info(f"Removed: {f}")

    if len(accepted_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter remove_by_title")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Filter remove_by_content")

    removed_articles = set()

    for f, article in accepted_articles.items():
        for article_content in article["content"]:
            for filter_content in config.FILTER_REMOVE_BY_CONTENT:
                if filter_content.lower() in article_content.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        accepted_articles.pop(f)
        logging.info(f"Removed: {f}")

    if len(accepted_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter remove_by_content")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Filter remove_by_link")

    removed_articles = set()

    for f, article in accepted_articles.items():
        for article_link in article["link"]:
            for filter_link in config.FILTER_REMOVE_BY_LINK:
                if filter_link.lower() in article_link.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        accepted_articles.pop(f)
        logging.info(f"Removed: {f}")

    if len(accepted_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter remove_by_link")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Link accepted_articles")

    for f in accepted_articles.keys():
        src = f"{raw_articles_dt_folder}/{f}"
        dest = f"{accepted_articles_dt_folder}/{f}"
        os.symlink(src, dest)
        logging.info(f"Accepted: {f}")

    logging.info(f"[END  ] Link accepted_articles")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"[BEGIN] Link rejected_articles")

    for f in raw_articles.keys():
        if f not in accepted_articles:
            src = f"{raw_articles_dt_folder}/{f}"
            dest = f"{rejected_articles_dt_folder}/{f}"
            os.symlink(src, dest)
            logging.info(f"Rejected: {f}")

    logging.info(f"[END  ] Link unused_articles")

    logging.info(f"------------------------------------------------------------------------------------------")

    logging.info(f"News filter ended")

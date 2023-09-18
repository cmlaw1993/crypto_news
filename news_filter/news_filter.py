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
    logging.info(f"[BEGIN] Loading config")

    logging.info(f"active_datetime: {config.ACTIVE_DATETIME}")
    logging.info(f"raw_articles_folder: {config.RAW_ARTICLES_FOLDER}")
    logging.info(f"rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")
    logging.info(f"selected_articles_folder: {config.SELECTED_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Loading config")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Recreate rejected_articles_folder")

    if os.path.exists(config.REJECTED_ARTICLES_FOLDER):
        shutil.rmtree(f"{config.REJECTED_ARTICLES_FOLDER}")
        logging.info(f"Deleted accepted_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")

    try:
        os.mkdir(config.REJECTED_ARTICLES_FOLDER)
        logging.info(f"Created rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")
    except:
        logging.error(f"Unable to create rejected_articles_folder: {config.REJECTED_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Recreate rejected_articles_folder")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Recreate selected_articles_folder")

    if os.path.exists(config.SELECTED_ARTICLES_FOLDER):
        shutil.rmtree(f"{config.SELECTED_ARTICLES_FOLDER}")
        logging.info(f"Deleted selected_articles_folder: {config.SELECTED_ARTICLES_FOLDER}")

    try:
        os.mkdir(config.SELECTED_ARTICLES_FOLDER)
        logging.info(f"Created selected_articles_folder: {config.SELECTED_ARTICLES_FOLDER}")
    except:
        logging.error(f"Unable to create selected_articles_folder: {config.SELECTED_ARTICLES_FOLDER}")

    logging.info(f"[END  ] Recreate selected_articles_folder")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Load raw_articles")

    if not os.path.exists(config.RAW_ARTICLES_FOLDER):
        logging.error(f"raw_articles_dt_folder does not exists: {config.RAW_ARTICLES_FOLDER}")

    files = os.listdir(config.RAW_ARTICLES_FOLDER)

    raw_articles = dict()

    for f in files:
        file_name = f"{config.RAW_ARTICLES_FOLDER}/{f}"

        with open(file_name, "r") as file:
            raw_articles[f] = json.load(file)

        logging.info(f"Loaded raw_article: {f}")

    logging.info(f"[END  ] Load raw_articles")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Filter select_by_source_id")

    selected_articles = dict()

    for f, raw_article in raw_articles.items():
        if raw_article["source_id"] in config.FILTER_SELECT_BY_SOURCE_ID:
            selected_articles[f] = raw_article
            logging.info(f"Selected: {f}")

    if len(selected_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter select_by_source_id")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Filter reject_by_keywords")

    removed_articles = set()

    for f, article in selected_articles.items():
        for article_keyword in article["keywords"]:
            for filter_keyword in config.FILTER_REJECT_BY_KEYWORDS:
                if filter_keyword.lower() in article_keyword.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        selected_articles.pop(f)
        logging.info(f"Rejected: {f}")

    if len(selected_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter reject_by_keywords")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Filter reject_by_title")

    removed_articles = set()

    for f, article in selected_articles.items():
        for article_title in article["title"]:
            for filter_title in config.FILTER_REJECT_BY_TITLE:
                if filter_title.lower() in article_title.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        selected_articles.pop(f)
        logging.info(f"Rejected: {f}")

    if len(selected_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter reject_by_title")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Filter reject_by_content")

    removed_articles = set()

    for f, article in selected_articles.items():
        for article_content in article["content"]:
            for filter_content in config.FILTER_REJECT_BY_CONTENT:
                if filter_content.lower() in article_content.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        selected_articles.pop(f)
        logging.info(f"Rejected: {f}")

    if len(selected_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter reject_by_content")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Filter reject_by_link")

    removed_articles = set()

    for f, article in selected_articles.items():
        for article_link in article["link"]:
            for filter_link in config.FILTER_REJECT_BY_LINK:
                if filter_link.lower() in article_link.lower():
                    removed_articles.add(f)

    for f in removed_articles:
        selected_articles.pop(f)
        logging.info(f"Rejected: {f}")

    if len(selected_articles) == 0:
        logging.error("There are no articles after performing filter")

    logging.info(f"[END  ] Filter reject_by_link")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Link selected_articles")

    for f in selected_articles.keys():
        src = f"{config.RAW_ARTICLES_FOLDER}/{f}"
        dest = f"{config.SELECTED_ARTICLES_FOLDER}/{f}"
        os.symlink(src, dest)
        logging.info(f"Accepted: {f}")

    logging.info(f"[END  ] Link selected_articles")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"[BEGIN] Link rejected_articles")

    for f in raw_articles.keys():
        if f not in selected_articles:
            src = f"{config.RAW_ARTICLES_FOLDER}/{f}"
            dest = f"{config.REJECTED_ARTICLES_FOLDER}/{f}"
            os.symlink(src, dest)
            logging.info(f"Rejected: {f}")

    logging.info(f"[END  ] Link rejected_articles")

    logging.info(f"------------------------------------------------------------------------------------------")
    logging.info(f"News filter ended")

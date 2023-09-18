from datetime import datetime
import os

ACTIVE_DATETIME = datetime.strptime(os.getenv('ACTIVE_DATETIME'), '%Y%m%d')

VARDATA_FOLDER = f"{os.getcwd()}/vardata/{ACTIVE_DATETIME.strftime('%Y%m%d')}"
RAW_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/0_raw_articles"
REJECTED_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/1_rejected_articles"
SELECTED_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/2_selected_articles"

FILTER_SELECT_BY_SOURCE_ID = (
    "beincrypto",
    "bitcoinwarrior",
    "bitdegree",
    "blockchain",
    "coinedition",
    "coindesk",
    "coinpaper",
    "coinpedia",
    "cointelegraph",
    "cryptoeconomy",
    "cryptomode",
    "cryptonews",
    "cryptoslate",
    "cryptotimes",
    "einvesting",
    "globalcoinreport",
    "invezz",
    "theblock",
    "usethebitcoin",
    "utoday",
    "watcherguru",
)

FILTER_REJECT_BY_KEYWORDS = (
    "analysis",
    "prediction",
    "sponsored",
    "learn",
    "how to",
    "industry talk",
)

FILTER_REJECT_BY_TITLE = (
    "?",
)

FILTER_REJECT_BY_CONTENT = (
    "The Airdrop",
)

FILTER_REJECT_BY_LINK = (
    "cointelegraph.com/magazine",
)


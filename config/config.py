from datetime import timezone, timedelta
import os


VARDATA_FOLDER = f"{os.getcwd()}/vardata"
RAW_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/0_raw_articles"
ACCEPTED_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/1_accepted_articles"
REJECTED_ARTICLES_FOLDER = f"{VARDATA_FOLDER}/2_rejected_articles"

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

FILTER_REMOVE_BY_KEYWORDS = (
    "analysis",
    "prediction",
    "sponsored",
    "learn",
    "how to",
    "industry talk",
)

FILTER_REMOVE_BY_TITLE = (
    "?",
)

FILTER_REMOVE_BY_CONTENT = (
    "The Airdrop",
)

FILTER_REMOVE_BY_LINK = (
    "cointelegraph.com/magazine",
)


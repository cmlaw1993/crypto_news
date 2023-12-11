from datetime import datetime, timedelta
import pytz
import os

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from common import utils
from _keys import keys


# ####################################################################################################
# alert

ALERT_ENABLE = True

ALERT_TELEGRAM_RECEIVER_ID = "6895080174"

# ####################################################################################################
# active datetime

ACTIVE_DATE = datetime.strptime(os.getenv('ACTIVE_DATE'), '%Y%m%d')

ACTIVE_TZ = 'Asia/Kuala_Lumpur'
ACTIVE_HOUR = 5

PUBLISH_TZ = 'US/Eastern'
PUBLISH_HOUR = 20


def calculate_active_datetime():
    tz = pytz.timezone(ACTIVE_TZ)
    tz_time = tz.localize(ACTIVE_DATE)
    ret = tz_time.replace(hour=ACTIVE_HOUR, minute=0, second=0, microsecond=0)
    current_time = datetime.now(tz)
    if current_time < ret:
        raise Exception('Current time is before active datetime')
    return ret


ACTIVE_DATETIME = calculate_active_datetime()
ACTIVE_DATETIME_STR = utils.to_datetime_str(ACTIVE_DATETIME)
ACTIVE_DATE_STR = utils.to_date_str(ACTIVE_DATETIME)
ACTIVE_TIME_STR = utils.to_time_str(ACTIVE_DATETIME)


def calculate_utc_datetime():
    return ACTIVE_DATETIME.astimezone(pytz.timezone('UTC'))


UTC_DATETIME = calculate_utc_datetime()
UTC_DATETIME_STR = utils.to_datetime_str(ACTIVE_DATETIME)
UTC_DATE_STR = utils.to_date_str(ACTIVE_DATETIME)
UTC_TIME_STR = utils.to_time_str(ACTIVE_DATETIME)


def calculate_publish_datetime():
    tz = pytz.timezone(PUBLISH_TZ)
    tz_time = ACTIVE_DATETIME.astimezone(tz)
    ret = tz_time.replace(hour=PUBLISH_HOUR, minute=0, second=0, microsecond=0)
    if tz_time > ret:
        ret += timedelta(days=1)
    return ret


PUBLISH_DATETIME = calculate_publish_datetime()
PUBLISH_DATETIME_STR = utils.to_datetime_str(PUBLISH_DATETIME)
PUBLISH_DATE_STR = utils.to_date_str(PUBLISH_DATETIME)
PUBLISH_TIME_STR = utils.to_time_str(PUBLISH_DATETIME)


# ####################################################################################################
# current datetime

CURR_DATETIME = os.getenv('CURRENT_DATETIME')

# ####################################################################################################
# codepath

CODEPATH_FOLDER = f'{os.getenv("CODEPATH")}'

# ####################################################################################################
# data

DATA_FOLDER = os.path.join(os.getenv("CODEPATH"), '_data')

# ####################################################################################################
# vardata

VARDATA_FOLDER = os.path.join(DATA_FOLDER, 'vardata')
VARDATA_DATE_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR)

# ####################################################################################################
# staticdata

STATICDATA_FOLDER = os.path.join(DATA_FOLDER, 'staticdata')

TEMPLATES_FOLDER = os.path.join(STATICDATA_FOLDER, 'templates')

# ####################################################################################################
# video

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 60
VIDEO_BITRATE = '50000k'
VIDEO_PIXEL_FORMAT = 'yuv420p'
VIDEO_COLOR_RANGE = 'tv'
VIDEO_CODEC = 'h264_nvenc'
VIDEO_CODEC_PRESET = 'fast'

AUDIO_CODEC = 'aac'
AUDIO_BITRATE = '384k'

# ####################################################################################################
# status

STATUS_FILE = f'{VARDATA_DATE_FOLDER}/status.yaml'

STATUS_DEFAULT_VALUE = {
    'download_news':    {'enable': True, 'append_output': False, 'input': []},
    'news_to_vectordb': {'enable': True, 'append_output': False, 'input': []},
    'get_main_topic':   {'enable': True, 'append_output': False, 'input': []},
    'construct_digest': {'enable': True, 'append_output': False, 'input': []},
    'curate_digest':    {'enable': True, 'append_output': False, 'input': []},
    'review_digest':    {'enable': True, 'append_output': False, 'input': []},
    'download_media':   {'enable': True, 'append_output': False, 'input': []},
    'generate_clip':    {'enable': True, 'append_output': False, 'input': []},
    'generate_title':   {'enable': True, 'append_output': False, 'input': []},
    'upload_clip':      {'enable': True, 'append_output': False, 'input': []},
    'upload_thumbnail': {'enable': True, 'append_output': False, 'input': []},
}

# ####################################################################################################
# log

LOG_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, '0_log')
LOG_FILE = os.path.join(LOG_FOLDER, f'log_{CURR_DATETIME}.txt')

# ####################################################################################################
# vectordb

VECTORDB_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, '1_vectordb')

VECTORDB_COLLECTION_NAME = 'collection'
VECTORDB_EMBEDDINGS_MODEL = 'text-embedding-ada-002'
VECTORDB_EMBEDDINGS_COST = 0.0001/1000

def VECTORDB_GET_INST():
    embeddings = OpenAIEmbeddings(
        openai_api_key=keys.OPENAI_KEY_0,
        model=VECTORDB_EMBEDDINGS_MODEL
    )

    return Chroma(
        collection_name=VECTORDB_COLLECTION_NAME,
        persist_directory=VECTORDB_FOLDER,
        embedding_function=embeddings
    )

# ----------------------------------------------------------------------------------------------------
# a_download_news

DOWNLOADNEWS_NAME = 'a_download_news'
DOWNLOADNEWS_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, DOWNLOADNEWS_NAME)
DOWNLOADNEWS_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, DOWNLOADNEWS_NAME)

DOWNLOADNEWS_DAYS_AGO = 2

DOWNLOADNEWS_MODULES = [
    'cryptonewsapi_alltickernews',
    'cryptonewsapi_generalcryptonews',
    'cryptonewsapi_sundowndigest',
    'cryptonewsapi_trendingheadlines',
    'newsdata_all',
]

DOWNLOADNEWS_CRYPTONEWSAPI_MAXPAGES = 25

DOWNLOADNEWS_NEWSDATA_EXCLUDEDOMAIN = 'youtube.com'

# ----------------------------------------------------------------------------------------------------
# b_news_to_vectordb

NEWSTOVECTORDB_NAME = 'b_news_to_vectordb'
NEWSTOVECTORDB_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, NEWSTOVECTORDB_NAME)
NEWSTOVECTORDB_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, NEWSTOVECTORDB_NAME)

NEWSTOVECTORDB_MAX_COST = 1

NEWSTOVECTORDB_CHUNK_SIZE = 512
NEWSTOVECTORDB_CHUNK_OVERLAP = 100

# ----------------------------------------------------------------------------------------------------
# c_get_main_topic

GETMAINTOPIC_NAME = 'c_get_main_topic'
GETMAINTOPIC_FOLDER = os.path.join(VARDATA_DATE_FOLDER, GETMAINTOPIC_NAME)
GETMAINTOPIC_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, GETMAINTOPIC_NAME)

GETMAINTOPIC_MODULES = [
    'rank',
    # 'cryptonewsapi_sundowndigest',
]

GETMAINTOPIC_RANK_SOURCE_RANK = {
    'reuters': 1,
    'cointelegraph': 1,
    'coindesk': 1,
    'utoday': 1,
    'coingape': 1,
    'beincrypto': 1,
    'decrypt': 1,
    'coinpedia': 1,
    'coinedition': 1,
    'theblock': 1,
}

GETMAINTOPIC_RANK_OPENAI_MODEL = 'gpt-4-1106-preview'
GETMAINTOPIC_RANK_OPENAI_TEMPERATURE = 0
GETMAINTOPIC_RANK_OPENAI_TIMEOUT = 300

GETMAINTOPIC_RANK_COMMONTOPIC_MAXLOOPS = 3

MAINTOPIC_RANK_MAX_TOPICS = 20

GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_MODEL = 'gpt-4-1106-preview'
GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_TEMPERATURE = 0
GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_TIMEOUT = 60

# ----------------------------------------------------------------------------------------------------
# d_construct_digest

CONSTRUCTDIGEST_NAME = 'd_construct_digest'
CONSTRUCTDIGEST_FOLDER = os.path.join(VARDATA_DATE_FOLDER, CONSTRUCTDIGEST_NAME)
CONSTRUCTDIGEST_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, CONSTRUCTDIGEST_NAME)

CONSTRUCTDIGEST_OPENAI_MODEL = 'gpt-4-1106-preview'
CONSTRUCTDIGEST_OPENAI_TEMPERATURE = 0
CONSTRUCTDIGEST_OPENAI_TIMEOUT = 60

CONSTRUCTDIGEST_NUM_DOCS = 40

CONSTRUCTDIGEST_CONTENT_MIN_NUM_SENTENCES = 3
CONSTRUCTDIGEST_CONTENT_MAX_NUM_SENTENCES = 4
CONSTRUCTDIGEST_CONTENT_MIN_NUM_WORDS_PER_SENTENCE = 5
CONSTRUCTDIGEST_CONTENT_MAX_NUM_WORDS_PER_SENTENCE = 16

CONSTRUCTDIGEST_TITLE_MIN_NUM_WORDS_PER_SENTENCE = 5
CONSTRUCTDIGEST_TITLE_MAX_NUM_WORDS_PER_SENTENCE = 10

CONSTRUCTDIGEST_ONELINER_MIN_NUM_WORDS_PER_SENTENCE = 12
CONSTRUCTDIGEST_ONELINER_MAX_NUM_WORDS_PER_SENTENCE = 20

# ----------------------------------------------------------------------------------------------------
# e_curate_digest

CURATEDIGEST_NAME = 'e_curate_digest'
CURATEDIGEST_FOLDER = os.path.join(VARDATA_DATE_FOLDER, CURATEDIGEST_NAME)
CURATEDIGEST_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, CURATEDIGEST_NAME)

CURATEDIGEST_DAYS_AGO = 3

CURATEDIGEST_OPENAI_MODEL = 'gpt-4-1106-preview'
CURATEDIGEST_OPENAI_TEMPERATURE = 0
CURATEDIGEST_OPENAI_TIMEOUT = 60

CURATEDIGEST_NUM_PRIMARY = 3
CURATEDIGEST_NUM_SECONDARY = 10

# ----------------------------------------------------------------------------------------------------
# f_review_digest

REVIEWDIGEST_NAME = 'f_review_digest'
REVIEWDIGEST_FOLDER = os.path.join(VARDATA_DATE_FOLDER, REVIEWDIGEST_NAME)
REVIEWDIGEST_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, REVIEWDIGEST_NAME)

# ----------------------------------------------------------------------------------------------------
# g_download_media

DOWNLOADMEDIA_NAME = 'g_download_media'
DOWNLOADMEDIA_FOLDER = os.path.join(VARDATA_DATE_FOLDER, DOWNLOADMEDIA_NAME)
DOWNLOADMEDIA_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, DOWNLOADMEDIA_NAME)

DOWNLOADMEDIA_MODULES = [
    # 'dummy',
    'semiauto'
]

DOWNLOADMEDIA_DUMMY_IMAGE = [
    'staticdata/media/dummy/dummyImage0.jpg',
    'staticdata/media/dummy/dummyVideo0.mov',
    'staticdata/media/dummy/dummyImage1.jpg',
    'staticdata/media/dummy/dummyVideo1.mp4',
    'staticdata/media/dummy/dummyImage2.jpg',
    'staticdata/media/dummy/dummyVideo2.mp4',
]

DOWNLOADMEDIA_SEMIAUTO_OPENAI_MODEL = 'gpt-4-1106-preview'
DOWNLOADMEDIA_SEMIAUTO_OPENAI_TEMPERATURE = 0
DOWNLOADMEDIA_SEMIAUTO_OPENAI_TIMEOUT = 60

# ----------------------------------------------------------------------------------------------------
# h_generate_clip

GENERATECLIP_NAME = 'h_generate_clip'
GENERATECLIP_FOLDER = os.path.join(VARDATA_DATE_FOLDER, GENERATECLIP_NAME)
GENERATECLIP_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, GENERATECLIP_NAME)

GENERATECLIP_MODULES = [
    'v1',
]

GENERATECLIP_V1_CLEAN_TMP_FILES = True

GENERATECLIP_V1_SEC_PER_WORD = 0.5

GENERATECLIP_V1_AUDIO = [
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'CyberpunkFuture_A.wav'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'CyberpunkFuture_B.wav'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'CyberpunkFuture_C.wav'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'CyberpunkFuture_D.wav')
]

GENERATECLIP_V1_INTRO = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'Intro.mp4')

GENERATECLIP_V1_OUTRO = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'Outro.mov')
GENERATECLIP_V1_OUTRO_OVERLAP_DURATION = 0.5

GENERATECLIP_V1_LOGO = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'Logo.png')

GENERATECLIP_V1_INTRO_TRANSITION_AUDIO = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'IntroTransition.wav')

GENERATECLIP_V1_PRIMARY_MEDIA_TRANSITION = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'PrimaryMediaTransition.mov')
GENERATECLIP_V1_PRIMARY_BACKGROUND = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'PrimaryBackground.mp4')
GENERATECLIP_V1_PRIMARY_TRANSITION = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'PrimaryTransition.mov')

GENERATECLIP_V1_PRIMARY_ENTRY_DELAY = 0.15
GENERATECLIP_V1_PRIMARY_ENTRY_DURATION = 0.883

GENERATECLIP_V1_PRIMARY_TEXTBOX_WIDTH = 0.8979 * VIDEO_WIDTH
GENERATECLIP_V1_PRIMARY_TEXTBOX_HEIGHT = 0.3019 * VIDEO_HEIGHT

GENERATECLIP_V1_PRIMARY_TITLE_FONT = 'Roboto-Black'
GENERATECLIP_V1_PRIMARY_TITLE_SIZE = 44
GENERATECLIP_V1_PRIMARY_TITLE_COLOR = 'white'
GENERATECLIP_V1_PRIMARY_TITLE_GRAVITY = 'NorthWest'
GENERATECLIP_V1_PRIMARY_TITLE_BORDER_WIDTH = 20
GENERATECLIP_V1_PRIMARY_TITLE_BORDER_HEIGHT = 20
GENERATECLIP_V1_PRIMARY_TITLE_TEXTBOX_QUOTA = 0.27

GENERATECLIP_V1_PRIMARY_CONTENT_FONT = 'Roboto-Thin'
GENERATECLIP_V1_PRIMARY_CONTENT_SIZE = 52
GENERATECLIP_V1_PRIMARY_CONTENT_COLOR = 'white'
GENERATECLIP_V1_PRIMARY_CONTENT_GRAVITY = 'West'
GENERATECLIP_V1_PRIMARY_CONTENT_BORDER_WIDTH = 23
GENERATECLIP_V1_PRIMARY_CONTENT_BORDER_HEIGHT = 0
GENERATECLIP_V1_PRIMARY_CONTENT_TEXTBOX_QUOTA = 0.6

GENERATECLIP_V1_SECONDARY_BACKGROUND = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryBackground.mp4')

GENERATECLIP_V1_SECONDARY_TRANSITION_DURATION = 1.2
GENERATECLIP_V1_SECONDARY_TRANSITION_AUDIO = os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'audio', 'SecondaryTransition.wav')

GENERATECLIP_V1_SECONDARY_ENTRY_DURATION = 1.2

GENERATECLIP_V1_SECONDARY_TEXTBOX_ENTER = (
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox2LEnter.mov'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox3LEnter.mov'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox4LEnter.mov')
)

GENERATECLIP_V1_SECONDARY_TEXTBOX_STATIC = (
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox2LStatic.png'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox3LStatic.png'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox4LStatic.png')
)

GENERATECLIP_V1_SECONDARY_TEXTBOX_EXIT = (
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox2LExit.mov'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox3LExit.mov'),
    os.path.join(f'{TEMPLATES_FOLDER}', 'v1', 'video', 'SecondaryTBox4LExit.mov')
)

GENERATECLIP_V1_SECONDARY_TEXTBOX_WIDTH = (
    0.6411 * VIDEO_WIDTH,
    0.6411 * VIDEO_WIDTH,
    0.6411 * VIDEO_WIDTH
)

GENERATECLIP_V1_SECONDARY_TEXTBOX_HEIGHT = (
    0.2306 * VIDEO_HEIGHT,
    0.2926 * VIDEO_HEIGHT,
    0.3444 * VIDEO_HEIGHT,
)

GENERATECLIP_V1_SECONDARY_ONELINE_FONT = 'Roboto-Medium'
GENERATECLIP_V1_SECONDARY_ONELINE_SIZE = 52
GENERATECLIP_V1_SECONDARY_ONELINE_COLOR = 'white'
GENERATECLIP_V1_SECONDARY_ONELINE_GRAVITY = 'Center'
GENERATECLIP_V1_SECONDARY_ONELINE_BORDER_WIDTH = 20
GENERATECLIP_V1_SECONDARY_ONELINE_BORDER_HEIGHT = 40
GENERATECLIP_V1_SECONDARY_ONELINE_TEXTBOX_QUOTA = 0.2

# ----------------------------------------------------------------------------------------------------
# i_generate_title

GENERATETITLE_NAME = 'i_generate_title'
GENERATETITLE_FOLDER = os.path.join(VARDATA_DATE_FOLDER, GENERATETITLE_NAME)
GENERATETITLE_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, GENERATETITLE_NAME)

GENERATETITLE_OPENAI_MODEL = 'gpt-4-1106-preview'
GENERATETITLE_OPENAI_TEMPERATURE = 0
GENERATETITLE_OPENAI_TIMEOUT = 60

GENERATETITLE_TITLE_NUM_CHARACTERS = 60
GENERATETITLE_TITLE_NUM_RETRIES = 5
GENERATETITLE_TITLE_SUBTITLE = ' | TNS Daily'

GENERATETITLE_TAGS = [
    'News',
    'Cryptonews',
    'Crypto',
    'Bitcoin',
    'Ethereum',
    'ETF'
]

# ----------------------------------------------------------------------------------------------------
# j_upload_clip

UPLOADCLIP_NAME = 'j_upload_clip'
UPLOADCLIP_FOLDER = os.path.join(VARDATA_DATE_FOLDER, UPLOADCLIP_NAME)
UPLOADCLIP_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, UPLOADCLIP_NAME)

UPLOADCLIP_TAGS = [
    'News',
    'Cryptonews',
    'Crypto',
    'Bitcoin',
    'Ethereum',
    'ETF'
]

# ----------------------------------------------------------------------------------------------------
# k_upload_thumbnail

UPLOADTHUMBNAIL_NAME = 'k_upload_thumbnail'
UPLOADTHUMBNAIL_FOLDER = os.path.join(VARDATA_DATE_FOLDER, UPLOADTHUMBNAIL_NAME)
UPLOADTHUMBNAIL_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, UPLOADTHUMBNAIL_NAME)

UPLOADTHUMBNAIL_USE_DUMMY = False
UPLOADTHUMBNAIL_DUMMY_IMAGE = os.path.join('staticdata', 'dummy', 'dummyThumbnail.jpg')

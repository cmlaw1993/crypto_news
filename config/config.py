from datetime import datetime, timedelta
import pytz
import os

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from common import utils
from keys import keys


# ####################################################################################################
# alert

ALERT_ENABLE = False

ALERT_TELEGRAM_ID = "6895080174"
ALERT_TELEGRAM_KEY = "6895080174"

# ####################################################################################################
# active datetime

ACTIVE_DATE = datetime.strptime(os.getenv('ACTIVE_DATE'), '%Y%m%d')
ACTIVE_DATE_STR = utils.to_datetime_str(ACTIVE_DATE)

ACTIVE_TZ = 'US/Eastern'
ACTIVE_HOUR = 19


def calculate_active_datetime():
    tz_time = ACTIVE_DATE.replace(tzinfo=pytz.timezone(ACTIVE_TZ))
    ret = tz_time.replace(hour=ACTIVE_HOUR, minute=0, second=0, microsecond=0)
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
# vectordb

VECTORDB_FOLDER = os.path.join(DATA_FOLDER, 'vectordb')
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

# ####################################################################################################
# video

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_BITRATE = '12000k'
VIDEO_FPS = 30
VIDEO_CODEC = 'h264_nvenc'
VIDEO_CODEC_PRESET = 'fast'
AUDIO_CODEC = 'libmp3lame'

# ####################################################################################################
# youtube data api

YOUTUBEDATAAPI_SECRET = "/home/dennis/Workspace/crypto_news/keys/googleapi/test_secret.json"
YOUTUBEDATAAPI_OAUTH = "/home/dennis/Workspace/crypto_news/keys/googleapi/test_oauth.json"

# ####################################################################################################
# status

STATUS_FILE = f'{VARDATA_DATE_FOLDER}/status.yaml'

STATUS_DEFAULT_VALUE = {
    'download_news':    {'enable': True, 'weekend': True,  'append_output': False, 'input': []},
    'news_to_vectordb': {'enable': True, 'weekend': True,  'append_output': False, 'input': []},
    'get_main_topic':   {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'construct_digest': {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'curate_digest':    {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'download_media':   {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'generate_clip':    {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'combine_clips':    {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'upload_clip':      {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
    'upload_thumbnail': {'enable': True, 'weekend': False, 'append_output': False, 'input': []},
}

# ----------------------------------------------------------------------------------------------------
# a_download_news

DOWNLOADNEWS_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, 'a_download_news')
DOWNLOADNEWS_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'a_download_news')

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

NEWSTOVECTORDB_FOLDER = os.path.join(VARDATA_FOLDER, ACTIVE_DATE_STR, 'b_news_to_vectordb')
NEWSTOVECTORDB_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'b_news_to_vectordb')

NEWSTOVECTORDB_MAX_COST = 1

NEWSTOVECTORDB_CHUNK_SIZE = 512
NEWSTOVECTORDB_CHUNK_OVERLAP = 100

# ----------------------------------------------------------------------------------------------------
# c_get_main_topic

GETMAINTOPIC_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'c_get_main_topics')
GETMAINTOPIC_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'c_get_main_topics')

GETMAINTOPIC_MODULES = [
    'rank',
    # 'cryptonewsapi_sundowndigest',
]

GETMAINTOPIC_RANK_SOURCE_RANK = {
    'cointelegraph': 10,
    'coindesk': 9,
    'beincrypto': 8,
    'decrypt': 7,
    'utoday': 6,
    'bitcoin': 5,
    'blockworks': 4,
    'cryptonews': 3,
    'coincodex': 2,
    'theblock': 1,
}

MAINTOPIC_RANK_OPENAI_MODEL = 'gpt-4-1106-preview'
MAINTOPIC_RANK_OPENAI_TEMPERATURE = 0
MAINTOPIC_RANK_OPENAI_TIMEOUT = 30

MAINTOPIC_RANK_MAX_WORDS = 12
MAINTOPIC_RANK_MAX_TOPICS = 20

GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_MODEL = 'gpt-4-1106-preview'
GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_TEMPERATURE = 0
GETMAINTOPIC_SUNDOWNDIGEST_OPENAI_TIMEOUT = 30

# ----------------------------------------------------------------------------------------------------
# d_construct_digest

CONSTRUCTDIGEST_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'd_construct_digest')
CONSTRUCTDIGEST_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'd_construct_digest')

CONSTRUCTDIGEST_OPENAI_MODEL = 'gpt-4-1106-preview'
CONSTRUCTDIGEST_OPENAI_TEMPERATURE = 0
CONSTRUCTDIGEST_OPENAI_TIMEOUT = 30

CONSTRUCTDIGEST_NUMARTICLES_0_DAYS_AGO = 10
CONSTRUCTDIGEST_NUMARTICLES_1_DAYS_AGO = 10
CONSTRUCTDIGEST_NUMARTICLES_2_DAYS_AGO = 10

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

CURATEDIGEST_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'e_curate_digest')
CURATEDIGEST_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'e_curate_digest')

CURATEDIGEST_SOURCE_RANK = {
    'cointelegraph': 10,
    'coindesk': 9,
    'beincrypto': 8,
    'decrypt': 7,
    'utoday': 6,
    'bitcoin': 5,
    'blockworks': 4,
    'cryptonews': 3,
    'coincodex': 2,
    'theblock': 1,
}

CURATEDIGEST_NUM_PRIMARY = 3
CURATEDIGEST_NUM_SECONDARY = 20

# ----------------------------------------------------------------------------------------------------
# f_download_media

DOWNLOADMEDIA_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'f_download_media')
DOWNLOADMEDIA_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'f_download_media')

DOWNLOADMEDIA_MODULES = [
    # 'dummy',
    'semiauto'
]

DOWNLOADMEDIA_DUMMY_IMAGE = [
    'staticdata/dummy/dummyImage0.jpg',
    'staticdata/dummy/dummyVideo0.mov',
    'staticdata/dummy/dummyImage1.jpg',
    'staticdata/dummy/dummyVideo1.mp4',
    'staticdata/dummy/dummyImage2.jpg',
    'staticdata/dummy/dummyVideo2.mp4',
]

DOWNLOADMEDIA_SEMIAUTO_OPENAI_MODEL = 'gpt-4-1106-preview'
DOWNLOADMEDIA_SEMIAUTO_OPENAI_TEMPERATURE = 0
DOWNLOADMEDIA_SEMIAUTO_OPENAI_TIMEOUT = 30

# ----------------------------------------------------------------------------------------------------
# g_generate_clip/generate_clip

GENERATECLIP_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'g_generate_clip')
GENERATECLIP_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'g_generate_clip')

GENERATECLIP_MODULES = [
    'primary',
    'secondary',
]

GENERATECLIP_PRIMARY_SLIDE_WAIT_DURATION = 0.50
GENERATECLIP_PRIMARY_SLIDE_DURATION = 0.35
GENERATECLIP_PRIMARY_SEC_PER_WORD = 0.5

GENERATECLIP_PRIMARY_TITLE_FONT = 'Archivo-Black'
GENERATECLIP_PRIMARY_TITLE_SIZE = 75
GENERATECLIP_PRIMARY_TITLE_COLOR = 'yellow'
GENERATECLIP_PRIMARY_TITLE_BORDER_WIDTH = 150
GENERATECLIP_PRIMARY_TITLE_BORDER_HEIGHT = 150
GENERATECLIP_PRIMARY_TITLE_GRAVITY = 'Center'
GENERATECLIP_PRIMARY_TITLE_BACKDROP = os.path.join(f'{TEMPLATES_FOLDER}', 'TitleBackdrop.png')

GENERATECLIP_PRIMARY_CONTENT_FONT = 'Archivo-Black'
GENERATECLIP_PRIMARY_CONTENT_SIZE = 60
GENERATECLIP_PRIMARY_CONTENT_OVERSIZED_FONT_SIZE = 50
GENERATECLIP_PRIMARY_CONTENT_OVERSIZED_CHAR_LIMIT = 150
GENERATECLIP_PRIMARY_CONTENT_COLOR = 'white'
GENERATECLIP_PRIMARY_CONTENT_BORDER_WIDTH = 50
GENERATECLIP_PRIMARY_CONTENT_BORDER_HEIGHT = 30
GENERATECLIP_PRIMARY_CONTENT_GRAVITY = 'South'
GENERATECLIP_PRIMARY_CONTENT_BACKDROP = (
    (729, os.path.join(f'{TEMPLATES_FOLDER}', 'ContentBackdrop4Lines.png')),
    (815, os.path.join(f'{TEMPLATES_FOLDER}', 'ContentBackdrop3Lines.png')),
    (901, os.path.join(f'{TEMPLATES_FOLDER}', 'ContentBackdrop2Lines.png')),
)

GENERATECLIP_SECONDARY_SLIDE_DURATION = 0.35
GENERATECLIP_SECONDARY_SEC_PER_WORD = 0.5

GENERATECLIP_SECONDARY_TITLE_FONT = 'Archivo-Black'
GENERATECLIP_SECONDARY_TITLE_SIZE = 75
GENERATECLIP_SECONDARY_TITLE_COLOR = 'red'
GENERATECLIP_SECONDARY_TITLE_BORDER_WIDTH = 150
GENERATECLIP_SECONDARY_TITLE_BORDER_HEIGHT = 150
GENERATECLIP_SECONDARY_TITLE_GRAVITY = 'Center'
GENERATECLIP_SECONDARY_TITLE_BACKGROUND = os.path.join(f'{TEMPLATES_FOLDER}', 'TitleBackground.png')
GENERATECLIP_SECONDARY_TITLE_BACKDROP = os.path.join(f'{TEMPLATES_FOLDER}', 'TitleBackdrop.png')

# ----------------------------------------------------------------------------------------------------
# h_combine_clips/combine_clips

COMBINECLIPS_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'h_combine_clips')
COMBINECLIPS_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'h_combine_clips')

COMBINECLIPS_INTRO = os.path.join('staticdata', 'templates', 'TestIntro.mp4')
COMBINECLIPS_OUTRO = os.path.join('staticdata', 'templates', 'TestOutro.mp4')

COMBINECLIPS_AUDIO = os.path.join('staticdata', 'templates', 'SyntheticDeception.mp3')

COMBINECLIPS_AUDIO_FADE_DURATION = 5

# ----------------------------------------------------------------------------------------------------
# i_upload_clip/upload_video

UPLOADCLIP_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'i_upload_clip')
UPLOADCLIP_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'i_upload_clip')

# ----------------------------------------------------------------------------------------------------
# j_upload_thumbnail/upload_thumbnail

UPLOADTHUMBNAIL_FOLDER = os.path.join(VARDATA_DATE_FOLDER, 'j_upload_thumbnail')
UPLOADTHUMBNAIL_RELATIVE_FOLDER = os.path.join('vardata', ACTIVE_DATE_STR, 'j_upload_thumbnail')

UPLOADTHUMBNAIL_USE_DUMMY = False
UPLOADTHUMBNAIL_DUMMY_IMAGE = os.path.join('staticdata', 'dummy', 'dummyThumbnail.jpg')
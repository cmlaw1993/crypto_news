import logging
import yaml
import os

from common.pydantic.clipdata import ClipData
from common.googleapi.youtubedataapi import get_authenticated_service, upload_thumbnail
from config import config
from _keys import keys

def run(clean, input_list):

    logging.info(f'{config.UPLOADTHUMBNAIL_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.UPLOADTHUMBNAIL_FOLDER):
        try:
            os.makedirs(config.UPLOADTHUMBNAIL_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.UPLOADTHUMBNAIL_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.UPLOADTHUMBNAIL_FOLDER}/*')
        logging.info(f'Cleaned: {config.UPLOADTHUMBNAIL_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load upload file')

    clipdata = None

    for input_item in input_list:
        file_path = f'{config.DATA_FOLDER}/{input_item}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        clipdata = ClipData(**yaml_data)

    logging.info(f'[END  ] Load upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Prompt thumbnail from user')

    if config.UPLOADTHUMBNAIL_USE_DUMMY:

        clipdata.thumbnail = config.UPLOADTHUMBNAIL_DUMMY_IMAGE

    else:
        while True:
            thumbnail_name = f'thumbnail.{config.ACTIVE_DATE_STR}.png'
            thumbnail_path = os.path.join(config.UPLOADTHUMBNAIL_FOLDER, thumbnail_name)

            logging.info(f'Please create and save thumbnail as {thumbnail_path} and press enter.')
            input()

            if os.path.exists(thumbnail_path):
                break

            logging.warning('Thumbnail does not exists')

        clipdata.thumbnail = os.path.join(config.UPLOADTHUMBNAIL_RELATIVE_FOLDER, thumbnail_name)

    logging.info(f'[END  ] Prompt thumbnail from user')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload thumbnail')

    thumbnail_path = os.path.join(config.DATA_FOLDER, clipdata.thumbnail)

    youtube = get_authenticated_service(keys.YOUTUBEDATAAPI_CLIENT_SECRET)

    upload_thumbnail(youtube, thumbnail_path, clipdata.youtube_id)

    logging.info(f'[END  ] Upload thumbnail')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save upload file')

    file_path = f'{config.UPLOADCLIP_FOLDER}/{clipdata.id}'
    with open(file_path, 'w') as file:
        yaml.dump(clipdata.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Save upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.UPLOADTHUMBNAIL_NAME} ended')

    return []

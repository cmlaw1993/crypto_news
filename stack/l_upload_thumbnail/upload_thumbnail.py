import logging
import yaml
import os

from common.pydantic.upload import Upload
from common.googleapi.youtubedataapi import get_authenticated_service, upload_thumbnail
from config import config
from keys import keys

def run(clean, input_list):

    logging.info(f'j_upload_thumbnails/upload_thumbnails started')

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

    upload = None

    for input in input_list:
        file_path = f'{config.DATA_FOLDER}/{input}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        upload = Upload(**yaml_data)

    logging.info(f'[END  ] Load upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Prompt thumbnail from user')

    thumbnail_name = f'thumbnail.{config.ACTIVE_DATE_STR}.png'
    thumbnail_path = os.path.join(config.UPLOADTHUMBNAIL_FOLDER, thumbnail_name)

    logging.info(f'Please save thumbnail as {thumbnail_path} and press enter:')
    input()

    logging.info(f'[END  ] Prompt thumbnail from user')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check if thumbnail exists')

    if not os.path.exists(thumbnail_path):
        logging.error('Thumbnail does not exists')

    upload.thumbnail = thumbnail_path

    logging.info(f'[END  ] Check if thumbnail exists')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload thumbnail')

    youtube = get_authenticated_service(config.YOUTUBEDATAAPI_SECRET,
                                        config.YOUTUBEDATAAPI_OAUTH)

    upload_thumbnail(youtube, upload.thumbnail, upload.youtube_id)

    logging.info(f'[END  ] Upload thumbnail')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save upload file')

    file_path = f'{config.UPLOADCLIP_FOLDER}/{upload.id}'
    with open(file_path, 'w') as file:
        yaml.dump(upload.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Save upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'j_upload_thumbnails/upload_thumbnails ended')

    return []

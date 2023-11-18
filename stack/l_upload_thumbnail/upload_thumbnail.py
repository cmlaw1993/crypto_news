import logging
import yaml
import os

from common.pydantic.vidinfo import VidInfo
from common.googleapi.youtubedataapi import get_authenticated_service, upload_thumbnail
from config import config
from keys import keys

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

    vidinfo = None

    for input_item in input_list:
        file_path = f'{config.DATA_FOLDER}/{input_item}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        vidinfo = VidInfo(**yaml_data)

    logging.info(f'[END  ] Load upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Prompt thumbnail from user')

    if config.UPLOADTHUMBNAIL_USE_DUMMY:

        vidinfo.thumbnail = config.UPLOADTHUMBNAIL_DUMMY_IMAGE

    else:
        thumbnail_name = f'thumbnail.{config.ACTIVE_DATE_STR}.png'
        thumbnail_path = os.path.join(config.UPLOADTHUMBNAIL_FOLDER, thumbnail_name)

        logging.info(f'Please create and save thumbnail as {thumbnail_path} and press enter.')
        input()

        if not os.path.exists(thumbnail_path):
            logging.error('Thumbnail does not exists')

        vidinfo.thumbnail = os.path.join(config.UPLOADTHUMBNAIL_RELATIVE_FOLDER, thumbnail_name)

    logging.info(f'[END  ] Prompt thumbnail from user')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload thumbnail')

    thumbnail_path = os.path.join(config.DATA_FOLDER, vidinfo.thumbnail)

    youtube = get_authenticated_service(config.YOUTUBEDATAAPI_SECRET,
                                        config.YOUTUBEDATAAPI_OAUTH)

    upload_thumbnail(youtube, thumbnail_path, vidinfo.youtube_id)

    logging.info(f'[END  ] Upload thumbnail')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save upload file')

    file_path = f'{config.UPLOADCLIP_FOLDER}/{vidinfo.id}'
    with open(file_path, 'w') as file:
        yaml.dump(vidinfo.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Save upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.UPLOADTHUMBNAIL_NAME} ended')

    return []

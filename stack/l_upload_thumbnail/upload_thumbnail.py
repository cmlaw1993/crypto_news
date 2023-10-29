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

    if len(input_list) != 1:
        logging.error('Expected only a single input')

    file_path = f'{config.DATA_FOLDER}/{input_list[0]}'
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    upload = Upload(**yaml_data)

    logging.info(f'[END  ] Load upload file')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload thumbnail')

    file_path = os.path.join(config.DATA_FOLDER, input_list[0])

    youtube = get_authenticated_service(config.YOUTUBEDATAAPI_SECRET,
                                        config.YOUTUBEDATAAPI_OAUTH)

    upload_thumbnail(youtube, file_path, upload.youtube_id)

    logging.info(f'[END  ] Upload thumbnail')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'j_upload_thumbnails/upload_thumbnails ended')

    return []

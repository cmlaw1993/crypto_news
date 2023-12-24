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
    logging.info(f'[BEGIN] Create symlink')

    src = config.UPLOADTHUMBNAIL_FOLDER
    dst = os.path.join(os.path.expanduser("~"), 'Downloads', config.UPLOADTHUMBNAIL_NAME)

    if os.path.islink(dst):
        try:
            os.unlink(dst)
        except:
            raise Exception(f"Error removing existing symlink: {dst}")
    try:
        os.symlink(src, dst)
        logging.info(f'Created symlink: {dst}')
    except:
        raise Exception(f"Error creating symlink: {dst}")

    logging.info(f'[END  ] Create symlink')

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

    thumbnail_path = None

    while True:
        thumbnail_name = f'Daily-Crypto-News.png'
        thumbnail_path = os.path.join(config.UPLOADTHUMBNAIL_FOLDER, thumbnail_name)

        logging.info(f'Please create and save thumbnail as {thumbnail_path} and press enter.')
        input()

        if os.path.exists(thumbnail_path):
            break

        logging.warning('Thumbnail does not exists')

    clipdata.thumbnail = os.path.join(config.UPLOADTHUMBNAIL_RELATIVE_FOLDER, thumbnail_name)

    logging.info(f'[END  ] Prompt thumbnail from user')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Set thumbnail metadata')

    write_tool_path = os.path.join('tools', 'png_metadata_writer.py')

    ret = os.system(f'python {write_tool_path} {thumbnail_path}')
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Unable to set thumbnail metadata')

    read_tool_path = os.path.join('tools', 'png_metadata_reader.py')

    ret = os.system(f'python {read_tool_path} {thumbnail_path}')
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Unable to read thumbnail metadata')

    logging.info(f'[END  ] Set thumbnail metadata')

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

import logging
import yaml
import os

from common.googleapi.youtubedataapi import get_authenticated_service, upload_video

from config import config
from common.pydantic.clipdata import VidInfo


def run(clean, input_list):

    logging.info(f'{config.UPLOADCLIP_NAME} started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.UPLOADCLIP_FOLDER):
        try:
            os.makedirs(config.UPLOADCLIP_FOLDER)
            logging.info(f'Created folder: {config.UPLOADCLIP_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.UPLOADCLIP_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.UPLOADCLIP_FOLDER}/*')
        logging.info(f'Cleaned: {config.UPLOADCLIP_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load vidinfo')

    if len(input_list) != 1:
        logging.error('Received multiple vidinfo as input although only one expected')

    file_path = os.path.join(config.DATA_FOLDER, input_list[0])
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    vidinfo = VidInfo(**yaml_data)

    logging.info(f'[END  ] Load vidinfo')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check clip existance')

    clip_path = os.path.join(config.DATA_FOLDER, vidinfo.clip)

    if not os.path.exists(clip_path):
        logging.error(f'Clip does not exists: {clip_path}')

    logging.info(f'[END  ] Check clip existance')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload clip')

    youtube = get_authenticated_service(config.YOUTUBEDATAAPI_SECRET,
                                        config.YOUTUBEDATAAPI_OAUTH)

    clip_file = clip_path
    title = vidinfo.title
    description = vidinfo.description
    tags = ['crypto', 'bitcoin', 'ethereum', 'news']
    category = '25' # News and politics
    privacy_status = 'private'
    public_stats_viewable = 'false'
    made_for_kids = 'false'
    self_declared_made_for_kids = 'false'

    youtube_id = upload_video(youtube, clip_file, title, description, tags, category, privacy_status,
                              public_stats_viewable, made_for_kids, self_declared_made_for_kids)

    vidinfo.youtube_id = youtube_id

    file_path = f'{config.UPLOADCLIP_FOLDER}/{vidinfo.id}'
    with open(file_path, 'w') as file:
        yaml.dump(vidinfo.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Upload clip')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'{config.UPLOADCLIP_NAME} ended')

    return [f'{config.UPLOADCLIP_RELATIVE_FOLDER}/{vidinfo.id}']

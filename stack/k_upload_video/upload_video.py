import logging
import yaml
import os

from common.googleapi.youtubedataapi import get_authenticated_service, upload_video

from config import config
from common.pydantic.upload import Upload
from keys import keys

def run(clean, input_list):

    logging.info(f'i_upload_video/upload_video started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.UPLOADVIDEO_FOLDER):
        try:
            os.makedirs(config.UPLOADVIDEO_FOLDER)
            logging.info(f'Created folder: {config.UPLOADVIDEO_FOLDER}')
        except:
            logging.error(f'Unable to create folder: {config.UPLOADVIDEO_FOLDER}')
    else:
        logging.info('Folder exists')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.UPLOADVIDEO_FOLDER}/*')
        logging.info(f'Cleaned: {config.UPLOADVIDEO_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check video existance')

    if len(input_list) != 1:
        logging.error(f'Number of inputs is not 1, num_inputs:{len(input_list)}')

    file_path = f'{config.DATA_FOLDER}/{input_list[0]}'
    if not os.path.exists(file_path):
        logging.error(f'Video does not exists: {file_path}')

    logging.info(f'[END  ] Check video existance')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Upload video')

    youtube = get_authenticated_service(config.YOUTUBEDATAAPI_SECRET,
                                        config.YOUTUBEDATAAPI_OAUTH)

    video_file = file_path
    title = f'{input_list[0].split("/")[-1]}'
    description = 'test description'
    tags = ['crypto', 'news']
    category = '25' # News and politics
    privacy_status = 'private'
    public_stats_viewable = 'false'
    made_for_kids = 'false'
    self_declared_made_for_kids = 'false'

    youtube_id = upload_video(youtube, video_file, title, description, tags, category, privacy_status,
                              public_stats_viewable, made_for_kids, self_declared_made_for_kids)

    upload_data = {
        'id': f'upload.{config.ACTIVE_DATE_STR}.yaml',
        'youtube_id': youtube_id,
    }
    upload = Upload(**upload_data)

    file_path = f'{config.UPLOADVIDEO_FOLDER}/{upload.id}'
    with open(file_path, 'w') as file:
        yaml.dump(upload.model_dump(), file, sort_keys=False)

    logging.info(f'[END  ] Upload video')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'i_upload_video/upload_video ended')

    return [[f'{config.UPLOADVIDEO_RELATIVE_FOLDER}/{upload.id}']]

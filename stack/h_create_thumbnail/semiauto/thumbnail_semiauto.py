import subprocess
import logging
import time
import os

from config import config


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create symlink')

    src = config.CREATETHUMBNAIL_FOLDER
    dst = os.path.join(f'{os.path.expanduser("~")}', 'Downloads', 'h_create_thumbnail')

    if os.path.islink(dst):
        try:
            os.unlink(dst)
        except:
            raise Exception(f"Error removing existing symlink: {dst}")
    try:
        os.symlink(src, dst)
        print(f'Created symlink: {dst}')
    except:
        raise Exception(f"Error creating symlink: {dst}")

    logging.info(f'[END  ] Create symlink')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Open canva')

    os.system('pkill -f firefox')
    os.system(f'nohup firefox https://www.canva.com/create/youtube-thumbnails/ &')
    time.sleep(2)

    logging.info(f'[END  ] Open canva')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Open digest in kate')

    os.system('pkill -f kate')
    subprocess.Popen(['kate', f'{config.DATA_FOLDER}/{input_list[0]}'])

    logging.info(f'[END  ] Open digest in kate')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Prompt')

    file_name = f'thumbnail.{config.ACTIVE_DATE_STR}.png'
    output_list = [os.path.join(config.CREATETHUMBNAIL_RELATIVE_FOLDER, file_name)]
    file_path = os.path.join(dst, file_name)

    logging.info(f'Please save thumbnail as {file_path}')
    logging.info(f'Press enter after thumbnail is saved.')
    input()

    logging.info(f'[END  ] Prompt')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check if thumbnail exists')

    if not os.path.exists(file_path):
        logging.error('Thumbnail does not exists')

    logging.info(f'[END  ] Check if thumbnail exists')

    logging.info(f'------------------------------------------------------------------------------------------')

    return output_list

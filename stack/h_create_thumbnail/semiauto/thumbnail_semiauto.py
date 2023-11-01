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

    return

import subprocess
import logging
import glob
import time
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.digest import Digest, Media
from config import config
from keys import keys


def generate_keywords(digest):

    # lines = [digest.title]
    lines = list()
    lines += digest.content

    content = ""
    for idx, line in enumerate(lines):
        content += f'Line {idx}: {line}\n'

    system_template = f'You are a top editor for a cryptocurrency news agency.' \
                      f' Your target audience include top cryptocurrency traders and fund managers who makes important decisions based on your articles.'
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    human_template = f'{content}\n' \
                     f'\n' \
                     f'\n' \
                     f'The above are the list of sentences of an article that is to be converted into a video format.' \
                     f' Each sentence is indexed with its own line number.' \
                     f' We will need one image per each line to illustrate the article in the video.' \
                     f' Images are searched from stock photo databases using words.' \
                     f' The words are usually simple and not complicated.' \
                     f'\n' \
                     f'Your task is to determine the best images to use as well as the line where the image would begin.' \
                     f' You need to produce at least one image per line which best tells the story of the article.'\
                     f' The words describing the image should be simple.' \
                     f' You may use specific names or entities from the article as the words.' \
                     f' In your reply, simply state the line number followed by a colon and then the words.' \
                     f' Separate each entry with a newline.' \
                     f' An example is as follows:' \
                     f'\n' \
                     f'0:<words>' \
                     f'1:<words>' \
                     f'2:<words>' \
                     f'3:<words>' \
                     f'4:<words>'


# f' You should return the keywords which corresponds to the image you would like to use.' \
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY_0,
                      model_name=config.DOWNLOADMEDIA_SEMIAUTO_OPENAI_MODEL,
                      temperature=config.DOWNLOADMEDIA_SEMIAUTO_OPENAI_TEMPERATURE,
                      request_timeout=config.DOWNLOADMEDIA_SEMIAUTO_OPENAI_TIMEOUT)

    res = chat(prompt)

    line_results = res.content.split('\n')

    media = dict()

    # Add a dummy entry for the title

    digest_type = digest.id.split('.')[1]
    priority = digest.id.split('.')[2]
    id = f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}/media.{digest_type}.{priority:02}.Title'

    media_data = {
        'id': id,
        'keyword': '',
        'source': '',
        'author': '',
        'credit': '',
        'license': '',
        'effects': 'ZoomOutCenter'
    }

    media[0] = Media(**media_data)

    # Add entries returned from openai

    for results in line_results:

        line_result = results.split(':')

        line_idx = int(line_result[0]) + 1


        keyword = line_result[1].strip()

        id = f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}/media.{digest_type}.{priority:02}.{utils.sanitize_file_name(keyword)}'

        media_data = {
            'id': id,
            'keyword': keyword,
            'source': '',
            'author': '',
            'credit': '',
            'license': '',
            'effects': 'ZoomOutCenter'
        }

        media[line_idx] = Media(**media_data)

    digest.media = media


def reload_digest(digest):
    file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    return Digest(**yaml_data)


def media_exists(digest):

    for media in digest.media.values():

        if os.path.exists(f'{config.DATA_FOLDER}/{media.id}'):
            continue

        files = glob.glob(f'{config.DATA_FOLDER}/{media.id}*')
        if len(files) == 1:
            if files[0].startswith(f'{config.DATA_FOLDER}/{media.id}'):
                b = files[0][len(media.id):]
                media.id += '.' + files[0].split('.')[-1]
                save_digest(digest)
                continue

        return False

    return True


def search_media(digest):

    lines = [digest.title]
    lines += digest.content

    os.system('pkill -f firefox')
    os.system('pkill -f kate')

    # Search for article

    ret = os.system(f'google-chrome "https://www.google.com/search?tbm=nws&q={utils.url_encode(digest.title)}" &')
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error launching firefox')

    time.sleep(1)

    for idx, media in enumerate(digest.media.values()):

        # Skip title
        if idx == 0 and media.keyword == '':
            continue

        pages = f''

        # Google image
        pages += f' \"https://www.google.com/search?tbm=isch&q={utils.url_encode(media.keyword)}\"'

        # Videos
        # pages += f' \"https://commons.wikimedia.org/w/index.php?search={utils.url_encode(media.keyword)}&title=Special:MediaSearch&go=Go&type=video\"'
        pages += f' \"https://www.freepik.com/search?aspect_ratio=16%3A9&category=footage&format=search&query={utils.url_encode(media.keyword)}&type=video\"'
        pages += f' \"https://elements.envato.com/stock-video/{utils.url_encode(media.keyword)}\"'
        pages += f' \"https://www.shutterstock.com/video/search/{utils.url_encode(media.keyword)}?aspect_ratio=16%3A9\"'
        # pages += f' \"https://www.dreamstime.com/stock-footage/{utils.url_encode(media.keyword)}.html\"'
        pages += f' \"https://www.pond5.com/search?kw={utils.url_encode(media.keyword)}&media=footage\"'

        # Images
        pages += f' \"https://commons.wikimedia.org/w/index.php?search={utils.url_encode(media.keyword)}&title=Special:MediaSearch&go=Go&type=image\"'
        pages += f' \"https://www.flickr.com/search/?safe_search=3&license=2%2C3%2C4%2C5%2C6%2C9&text={utils.url_encode(media.keyword)}\"'
        pages += f' \"https://www.freepik.com/search?format=search&last_filter=orientation&orientation=landscape&query={utils.url_encode(media.keyword)}&type=photo\"'
        pages += f' \"https://elements.envato.com/photos/{utils.url_encode(media.keyword)}\"'
        pages += f' \"https://www.shutterstock.com/search/{utils.url_encode(media.keyword)}?image_type=photo\"'
        # pages += f' \"https://www.dreamstime.com/photos-images/{utils.url_encode(media.keyword)}.html\"'
        pages += f' \"https://www.pond5.com/search?kw={utils.url_encode(media.keyword)}&media=photo\"'

        ret = os.system(f'firefox {pages} &')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error launching firefox')

        # Sleep needed, else windows may be opened out of order
        time.sleep(1)

    time.sleep(1)
    p = subprocess.Popen(['kate', f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'])
    p.wait()


def save_digest(digest):
    file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
    with open(file_path, 'w') as file:
        yaml.dump(digest.model_dump(), file, sort_keys=False)

    logging.info(f'Saved: {file_path}')


def crop_and_resize_media():

    os.system('pkill -f firefox')
    os.system(f'nohup firefox "https://www.birme.net/?target_width=1920&target_height=1080" &')

    logging.info('Please press enter when done')
    input()


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create symlink')

    src = config.DOWNLOADMEDIA_FOLDER
    dst = f'{os.path.expanduser("~")}/Downloads/g_download_media'

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
    logging.info(f'[BEGIN] Load digests')

    input_list = sorted(input_list)
    digests = list()

    for digest_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        digest = Digest(**yaml_data)

        if os.path.exists(f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'):
            file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
            with open(file_path, 'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            digest = Digest(**yaml_data)

        digests.append(digest)

        logging.info(f'Loaded: {digest_file}')

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate keywords')

    for digest in digests:

        type = digest.id.split('.')[1]
        if type != 'primary':
            save_digest(digest)
            continue

        if digest.media is None:
            generate_keywords(digest)
            save_digest(digest)

    logging.info(f'[END  ] Generate keywords')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Search media')

    for digest in digests:

        type = digest.id.split('.')[1]
        if type != 'primary':
            continue

        if media_exists(digest):
            logging.info(f'Media exists. Skipping: {digest.id}')
            continue

        while True:

            logging.info(f'Searching: {digest.id}')
            search_media(digest)

            digest = reload_digest(digest)
            if not media_exists(digest):
                logging.info(f'Media does not exists.')
                continue

            break

    logging.info(f'[END  ] Search media')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Crop and resize media')

    crop_and_resize_media()

    logging.info(f'[END  ] Crop and resize media')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check if media exists')

    output_list = list()

    for digest in digests:

        output_list.append(os.path.join(config.DOWNLOADMEDIA_RELATIVE_FOLDER, digest.id))

        type = digest.id.split('.')[1]
        if type != 'primary':
            continue

        digest = reload_digest(digest)
        if not media_exists(digest):
            logging.info(f'Media does not exists.')

    logging.info(f'[END  ] Check if media exists')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Review digests')

    files = [f for f in os.listdir(config.DOWNLOADMEDIA_FOLDER)]
    files = sorted(files)
    cmd = ["kate"] + [os.path.join(config.DOWNLOADMEDIA_FOLDER, f) for f in files if 'digest.secondary' in f]

    p = subprocess.Popen(cmd)
    p.wait()

    logging.info(f'[END  ] Review secondary digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

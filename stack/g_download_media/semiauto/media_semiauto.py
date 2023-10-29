import subprocess
import logging
import yaml
import os

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

from common import utils
from common.pydantic.digest import Digest
from config import config
from keys import keys


def generate_keywords(digest):

    lines = [digest.title]
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
                     f' We will need at least one or at more images to illustrate the lines in the video.' \
                     f' In the video, an image may start at the beginning of a line, span one or more lines, before being replaced with another image.' \
                     f' Images are searched from stock photo databases using keywords.' \
                     f' The keywords are usually simple and not complicated.' \
                     f'\n' \
                     f'Your task is to determine the best images to use as well as the line where the image would begin.' \
                     f' You need to produce a minimum of 3 images which best tells the story of the article.'\
                     f' You should prefer using images of named people and entities from the article.' \
                     f' You should prefer images that are easy to describe via keywords.' \
                     f' You should return the keywords which corresponds to the image you would like to use.'\
                     f' In your reply, simply state the line number followed by a colon and then a single keyword.' \
                     f' Separate each entry with a newline.' \
                     f' An example is as follows:' \
                     f'\n' \
                     f'0:<keyword>' \
                     f'1:<keyword>' \
                     f'3:<keyword>' \
                     f'5:<keyword>'
# f' You need to produce a minimum of 2 images or a maximum which is equal to the number of lines.' \
# f' You need at most 2 images which best tells the story of the article.' \
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt().to_messages()

    chat = ChatOpenAI(openai_api_key=keys.OPENAI_KEY,
                      model_name=config.DOWNLOADMEDIA_SEMIAUTO_OPENAI_MODEL,
                      temperature=config.DOWNLOADMEDIA_SEMIAUTO_OPENAI_TEMPERATURE)

    res = chat(prompt)

    line_results = res.content.split('\n')

    media = dict()

    for results in line_results:

        line_result = results.split(':')

        line_idx = int(line_result[0])
        keyword = line_result[1]
        priority = digest.id.split('.')[1]
        id = f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}/media.{priority}.{utils.sanitize_file_name(keyword)}.jpg'

        media[line_idx] = {
            'id': id,
            'keyword': keyword,
            'source': '',
            'credit': '',
            'license': '',
        }

    digest.media_path = f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}'
    digest.media = media


def reload_digest(digest):
    file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    return Digest(**yaml_data)


def media_exists(digest):
    for media in digest.media.values():
        if not os.path.exists(f'{config.DOWNLOADMEDIA_FOLDER}/{media["id"]}'):
            return False
    return True


def search_media(digest):

    lines = [digest.title]
    lines += digest.content

    os.system('pkill -f firefox')
    os.system('pkill -f kate')
    p = subprocess.Popen(['kate', f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'])

    pages = ""

    for media in digest.media.values():
        pages += f'\"https://www.google.com/search?tbm=isch&q={utils.url_encode(media["keyword"])}\" '
        pages += f'\"https://www.shutterstock.com/search/{utils.url_encode(media["keyword"])}?orientation=horizontal&image_type=photo\" '
        pages += f'\"https://www.dreamstime.com/photos-images/{utils.url_encode(media["keyword"])}.html\" '
        pages += f'\"https://www.flickr.com/search/?safe_search=3&license=2%2C3%2C4%2C5%2C6%2C9&text={utils.url_encode(media["keyword"])}\" '
        pages += f'\"https://www.unsplash.com/s/photos/{utils.url_encode(media["keyword"])}\" '
        pages += f'\"https://www.freepik.com/search?format=search&last_filter=orientation&orientation=landscape&query={utils.url_encode(media["keyword"])}&type=photo\" '

    os.system(f'nohup firefox {pages} &')
    p.wait()


def save_digest(digest):
    file_path = f'{config.DOWNLOADMEDIA_FOLDER}/{digest.id}'
    with open(file_path, 'w') as file:
        yaml.dump(digest.model_dump(), file, sort_keys=False)

    logging.info(f'Saved: {file_path}')


def crop_and_resize_media():

    os.system('pkill -f firefox')
    os.system(f'nohup firefox https://www.birme.net/?target_width=1280&target_height=720 &')

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
        print(f'Created symlink: {dst}')
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

        logging.info(f'Loaded: {file_path}')

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate keywords')

    for digest in digests:
        if digest.media is None:
            generate_keywords(digest)
            save_digest(digest)

    logging.info(f'[END  ] Generate keywords')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Search media')

    for digest in digests:

        if media_exists(digest):
            logging.info(f'Media exists. Skipping: {digest.id}')
            continue

        logging.info(f'Searching: {digest.id}')
        search_media(digest)

        digest = reload_digest(digest)
        if not media_exists(digest):
            logging.info(f'Media does not exists.')

    logging.info(f'[END  ] Search media')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Crop and resize media')

    crop_and_resize_media()

    logging.info(f'[END  ] Crop and resize media')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Check if media exists')

    output_list = list()

    for digest in digests:

        output_list.append(f'{config.DOWNLOADMEDIA_RELATIVE_FOLDER}/{digest.id}')

        digest = reload_digest(digest)
        if not media_exists(digest):
            logging.info(f'Media does not exists.')

    logging.info(f'[END  ] Check if media exists')

    logging.info(f'------------------------------------------------------------------------------------------')
    return output_list

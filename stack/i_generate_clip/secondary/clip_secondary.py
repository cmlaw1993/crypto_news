import logging
import random
import math
import yaml

from moviepy.editor import *

from common import utils
from common.pydantic.digest import Effects, Digest
from config import config

def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sort input')

    def sort_by_rank(item):
        return item.split(".")[2]

    input_list = sorted(input_list, key=sort_by_rank)

    logging.info(f'[END  ] Sort input')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load secondary digests')

    digests = list()

    for digest_file in input_list:

        digest_type = digest_file.split('.')[1]
        if digest_type != 'secondary':
            continue

        file_path = os.path.join(f'{config.DATA_FOLDER}', f'{digest_file}')
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load secondary digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate clips')

    outputs = list()

    for digest in digests:

        logging.info(f'Generating secondary clip: {digest.id}')

        priority = digest.id.split('.')[2]
        score = digest.id.split('.')[3]
        name = digest.id.split('.')[4]

        base_id = f'clip.secondary.{priority}.{score}.{name}'

        width = config.VIDEO_WIDTH
        height = config.VIDEO_HEIGHT
        bitrate = config.VIDEO_BITRATE
        fps = config.VIDEO_FPS
        codec = config.VIDEO_CODEC
        preset = config.VIDEO_CODEC_PRESET

        slide_t = config.GENERATECLIP_SECONDARY_SLIDE_DURATION
        sec_per_word_t = config.GENERATECLIP_SECONDARY_SEC_PER_WORD
        
        tmps = set()

        # Generate text png and calculate duration

        font = config.GENERATECLIP_SECONDARY_TITLE_FONT
        size = config.GENERATECLIP_SECONDARY_TITLE_SIZE
        color = config.GENERATECLIP_SECONDARY_TITLE_COLOR
        border_width = config.GENERATECLIP_SECONDARY_TITLE_BORDER_WIDTH
        border_height = config.GENERATECLIP_SECONDARY_TITLE_BORDER_HEIGHT
        gravity = config.GENERATECLIP_SECONDARY_TITLE_GRAVITY
        
        text_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.text.png')
        tmps.add(text_tmp)

        caption_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.caption.txt')
        with open(caption_tmp, 'w') as file:
            file.write(digest.oneliner)
        tmps.add(caption_tmp)

        ret = os.system(f'convert'
                        f' -bordercolor transparent'
                        f' -border {border_width}x{border_height}'
                        f' -background transparent'
                        f' -fill {color}'
                        f' -font {font}'
                        f' -pointsize {size}'
                        f' -size {width-2*border_width}x{height-2*border_height}'
                        f' -gravity {gravity}'
                        f' caption:@{caption_tmp}'
                        f' -type truecolormatte'
                        f' PNG32:{text_tmp}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error running image magick')

        duration = math.ceil((utils.count_words(digest.oneliner) * sec_per_word_t)
                             + (2 * slide_t))

        # Generate final clip

        final_clip = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.mp4')

        ret = os.system(f'ffmpeg -y -loop 1 -t {duration} -i {config.GENERATECLIP_SECONDARY_TITLE_BACKGROUND}'
                        f' -loop 1 -t {duration} -i {config.GENERATECLIP_SECONDARY_TITLE_BACKDROP}'
                        f' -loop 1 -t {duration} -i {text_tmp}'
                        f' -filter_complex "[0:v]scale={width}:{height},fps={fps}[f0];'
                        f' [f0][1]overlay=0:0:enable=\'between(t,0,{duration})\'[f1];'
                        f' [f1][2]overlay=\'if(lte(t,({slide_t})), -W+(t/{slide_t})*W, if(lte(t,({duration}-{slide_t})), 0, ((t-({duration}-{slide_t}))/{slide_t})*W))\':H-h[f2];"'
                        f' -map [f2] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {final_clip}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error generating secondary clip')

        # Cleanup temporary files

        for tmp in tmps:
            os.system(f'rm -rf {tmp}')

        # Append to output and log completion

        outputs.append(os.path.join(f'{config.GENERATECLIP_RELATIVE_FOLDER}', f'{base_id}.mp4'))
        logging.info(f'Saved: {base_id}.mp4')

    logging.info(f'[END  ] Generate secondary clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    return outputs

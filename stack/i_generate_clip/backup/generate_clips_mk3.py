import logging
import random
import math
import yaml

from moviepy.editor import *
from PIL import Image

from common import utils
from common.pydantic.digest import Digest
from config import config


def calculate_image_miny(image_path):
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    pixels = image.load()

    min_y = height

    for x in range(width):
        for y in range(height):
            _, _, _, alpha = pixels[x, y]
            if alpha > 0:
                min_y = min(min_y, y)

    return min_y


def run(clean, input_list):
    logging.info(f'g_generate_clips/generate_clips started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.GENERATECLIP_FOLDER):
        try:
            os.makedirs(config.GENERATECLIP_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.GENERATECLIP_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.GENERATECLIP_FOLDER}/*')
        logging.info(f'Cleaned: {config.GENERATECLIP_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for digest_file in sorted(input_list):
        file_path = f'{config.DATA_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate clips')

    outputs = list()

    for digest in digests:

        logging.info(f'Generating clip: {digest.id}')

        text_pngs = list()
        text_durations = list()
        backdrop_pngs = list()
        media_clips = list()
        media_durations = list()

        total_duration = 0

        width = config.VIDEO_WIDTH
        height = config.VIDEO_HEIGHT
        bitrate = config.VIDEO_BITRATE
        fps = config.VIDEO_FPS

        codec = config.GENERATECLIPS_CODEC
        preset = config.GENERATECLIPS_PRESET

        wait = config.GENERATECLIPS_SLIDE_WAIT_DURATION
        slide = config.GENERATECLIPS_SLIDE_DURATION

        lines = [digest.title]
        for line in digest.content:
            lines.append(line)

        # Prime text and calculate duration

        for idx, line in enumerate(lines):

            tmp_text = f'{config.GENERATECLIP_FOLDER}/{digest.id}.{idx}.text.png'

            font = config.GENERATECLIPS_CONTENT_FONT
            fontsize = config.GENERATECLIPS_CONTENT_FONT_SIZE
            color = config.GENERATECLIPS_CONTENT_COLOR
            border_width = config.GENERATECLIPS_CONTENT_BORDER_WIDTH
            border_height = config.GENERATECLIPS_CONTENT_BORDER_HEIGHT
            gravity = 'South'

            if idx == 0:
                font = config.GENERATECLIPS_TITLE_FONT
                fontsize = config.GENERATECLIPS_TITLE_FONT_SIZE
                color = config.GENERATECLIPS_TITLE_COLOR
                border_width = config.GENERATECLIPS_TITLE_BORDER_WIDTH
                border_height = config.GENERATECLIPS_TITLE_BORDER_HEIGHT
                gravity = 'Center'

            image_magick_tmp = f'{config.GENERATECLIP_FOLDER}/{digest.id}.{idx}.image_magick.txt'
            with open(image_magick_tmp, 'w') as file:
                file.write(line)

            ret = os.system(f'convert'
                            f' -bordercolor transparent'
                            f' -border {border_width}x{border_height}'
                            f' -background transparent'
                            f' -fill {color}'
                            f' -font {font}'
                            f' -pointsize {fontsize}'
                            f' -size {width-2*border_width}x{height-2*border_height}'
                            f' -gravity {gravity}'
                            f' caption:@{image_magick_tmp}'
                            f' -type truecolormatte'
                            f' PNG32:{tmp_text}')
            if os.WEXITSTATUS(ret) != 0:
                logging.error('Error running image magick')

            os.system(f'rm {image_magick_tmp}')

            text_pngs.append(tmp_text)

            backdrop_pngs.append(config.GENERATECLIPS_TITLE_BACKDROP)
            if idx > 0:
                min_y = calculate_image_miny(tmp_text)
                for ref_min_y, bk in config.GENERATECLIPS_CONTENT_BACKDROP:
                    if abs(min_y - ref_min_y) < (0.3 * fontsize):
                        backdrop_pngs[-1] = bk

            duration = math.ceil((utils.count_words(line) * config.GENERATECLIPS_SEC_PER_WORD)
                                  + (2 * config.GENERATECLIPS_SLIDE_WAIT_DURATION)
                                  + (2 * config.GENERATECLIPS_SLIDE_DURATION))
            text_durations.append(duration)
            total_duration += duration

        # Generate media clips and calculate duration

        media_idx = -1
        for idx in range(len(lines)):
            media_durations.append(0)
            if idx in digest.media.keys():
                media_idx = idx
            media_durations[media_idx] += text_durations[idx]

        for idx, media in digest.media.items():

            media_path = f'{config.DATA_FOLDER}/{media.id}'
            tmp_media_clip = f'{config.GENERATECLIP_FOLDER}/{digest.id}.{idx}.media.mp4'

            duration = media_durations[idx]
            frames = duration * fps

            ret = os.system(f'ffmpeg -y -i {media_path}'
                            f' -filter_complex "[0]setsar=1:1,scale=3000:-1,zoompan=z=\'zoom+0.0005\':x=0:y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                            f' -map [out] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -t {duration} -b:v {bitrate} -bufsize {bitrate} {tmp_media_clip}')
            if os.WEXITSTATUS(ret) != 0:
                logging.error('Error creating media clips')

                

            media_clips.append(tmp_media_clip)

        # Concatenate media clips into a full media clip

        full_media_clip = f'{config.GENERATECLIP_FOLDER}/{digest.id}.full.media.mp4'

        input = ''
        concat = ''
        for idx, media_clip in enumerate(media_clips):
            input += f' -i {media_clip}'
            concat += f'[{idx}:0]'

        ret = os.system(f'ffmpeg {input} -c copy'
                        f' -filter_complex "{concat}concat=n={len(media_clips)}:v=1:a=0[out]"'
                        f' -map [out] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {full_media_clip}')

        # Generate final clip
        # Start with the full media clip as a base

        final_content_clip = f'{config.GENERATECLIP_FOLDER}/{digest.id.replace("yaml", "content.mp4")}'
        os.system(f'cp {full_media_clip} {final_content_clip}')

        tmp_clip = f'{final_content_clip.replace("mp4", "tmp.mp4")}'

        # Add content backdrop

        input = f'-i {final_content_clip}'
        filter = f'[0:v]scale={width}:{height},fps={30}[f0];'
        last_out = f'[f0]'
        cum_dur = 0
        for idx in range(len(text_pngs)):
            dur = text_durations[idx]
            input += f' -loop 1 -t {dur} -i {backdrop_pngs[idx]}'
            if idx == 0:
                filter += f'{last_out}[{idx + 1}]overlay=\'if(lte(t,({cum_dur}+{wait}+{slide})), -W+((t-{cum_dur}-{wait})/{slide})*W, if(lte(t,({cum_dur}+{dur}-{wait}-{slide})), 0, ((t-({cum_dur}+{dur}-{wait}-{slide}))/{slide})*W))\':H-h[f{idx + 1}];'
            else:
                filter += f'{last_out}[{idx + 1}]overlay=W-w:\'if(lte(t,({cum_dur}+{wait}+{slide})), H-((t-{cum_dur}-{wait})/{slide})*H, if(lte(t,({cum_dur}+{dur}-{wait}-{slide})), 0, ((t-({cum_dur}+{dur}-{wait}-{slide}))/{slide})*H))\'[f{idx + 1}];'
            cum_dur += dur
            last_out = f'[f{idx + 1}]'

        ret = os.system(f'ffmpeg -y {input} -filter_complex "{filter}"'
                        f' -map {last_out} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {tmp_clip}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error adding content backdrop to final clip')

        os.system(f'cp {tmp_clip} {final_content_clip}')

        # Add texts to final clip

        input = f'-i {final_content_clip}'
        filter = f'[0:v]scale={width}:{height},fps={fps}[f0];'
        last_out = f'[f0]'
        cum_dur = 0
        for idx, text_png in enumerate(text_pngs):
            dur = text_durations[idx]
            input += f' -loop 1 -t {dur} -i {text_png}'
            if idx == 0:
                filter += f'{last_out}[{idx + 1}]overlay=\'if(lte(t,({cum_dur}+{wait}+{slide})), -W+((t-{cum_dur}-{wait})/{slide})*W, if(lte(t,({cum_dur}+{dur}-{wait}-{slide})), 0, ((t-({cum_dur}+{dur}-{wait}-{slide}))/{slide})*W))\':H-h[f{idx + 1}];'
            else:
                filter += f'{last_out}[{idx + 1}]overlay=W-w:\'if(lte(t,({cum_dur}+{wait}+{slide})), H-((t-{cum_dur}-{wait})/{slide})*H, if(lte(t,({cum_dur}+{dur}-{wait}-{slide})), 0, ((t-({cum_dur}+{dur}-{wait}-{slide}))/{slide})*H))\'[f{idx + 1}];'
            cum_dur += dur
            last_out = f'[f{idx+1}]'

        ret = os.system(f'ffmpeg -y {input} -filter_complex "{filter}"'
                        f' -map {last_out} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {tmp_clip}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error adding texts to final clip')

        os.system(f'cp {tmp_clip} {final_content_clip}')

        # Create cover clip

        tmp_text = f'{config.GENERATECLIP_FOLDER}/{digest.id}.full.text.png'

        font = config.GENERATECLIPS_COVER_FONT
        fontsize = config.GENERATECLIPS_COVER_FONT_SIZE
        color = config.GENERATECLIPS_COVER_COLOR
        border_width = config.GENERATECLIPS_COVER_BORDER_WIDTH
        border_height = config.GENERATECLIPS_COVER_BORDER_HEIGHT
        gravity = 'South'

        image_magick_tmp = f'{config.GENERATECLIP_FOLDER}/{digest.id}.full.image_magick.txt'
        with open(image_magick_tmp, 'w') as file:
            file.write(lines[0])

        ret = os.system(f'convert'
                        f' -bordercolor transparent'
                        f' -border {border_width}x{border_height}'
                        f' -background transparent'
                        f' -fill {color}'
                        f' -font {font}'
                        f' -pointsize {fontsize}'
                        f' -size {width - 2 * border_width}x{height - 2 * border_height}'
                        f' -gravity {gravity}'
                        f' caption:@{image_magick_tmp}'
                        f' -type truecolormatte'
                        f' PNG32:{tmp_text}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error running image magick')

        os.system(f'rm {image_magick_tmp}')
            
        dur = text_durations[0]
        wait = config.GENERATECLIPS_SLIDE_WAIT_DURATION
        slide = config.GENERATECLIPS_SLIDE_DURATION
        
        final_cover_clip = f'{config.GENERATECLIP_FOLDER}/{digest.id.replace("yaml", "cover.mp4")}'

        ret = os.system(f'ffmpeg -y'
                        f' -loop 1 -t {dur} -i {config.DATA_FOLDER}/{digest.media[0].id}'
                        f' -loop 1 -t {dur} -i {config.GENERATECLIPS_COVER_BACKDROP}'
                        f' -loop 1 -t {dur} -i {tmp_text}'
                        f' -filter_complex "'
                        f'[0:v]scale={width}:{height},fps={fps}[f0];'
                        f'[f0][1]overlay=0:0:enable=\'between(t,0,{dur})\'[f1];'
                        f'[f1][2]overlay=\'if(lte(t,({wait}+{slide})), -W+((t-{wait})/{slide})*W, if(lte(t,({dur}-{wait}-{slide})), 0, ((t-({dur}-{wait}-{slide}))/{slide})*W))\':H-h[f2];"'
                        f' -map [f2] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {final_cover_clip}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error creating final cover clip')

        # Cleanup temporary files

        for text_png in text_pngs:
            os.system(f'rm {text_png}')
        for media_clip in media_clips:
            os.system(f'rm {media_clip}')
        os.system(f'rm {full_media_clip}')
        os.system(f'rm {tmp_clip}')
        os.system(f'rm {tmp_text}')

        outputs.append(f'{config.GENERATECLIP_RELATIVE_FOLDER}/{digest.id.replace("yaml", "content.mp4")}')
        outputs.append(f'{config.GENERATECLIP_RELATIVE_FOLDER}/{digest.id.replace("yaml", "cover.mp4")}')

        logging.info(f'Saved: {final_content_clip}')
        logging.info(f'Saved: {final_cover_clip}')

    logging.info(f'[END  ] Generate clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'g_generate_clips/generate_clips ended')

    return [outputs]

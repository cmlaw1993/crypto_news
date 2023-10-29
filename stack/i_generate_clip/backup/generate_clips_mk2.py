import logging
import random
import math
import yaml
import time
import os

from moviepy.editor import *

from common import utils
from common.pydantic.digest import Digest
from config import config


class TitleSlideInSlideOut:
    def __init__(self, duration):
        self.duration = duration
        self.padding_duration = 0.5
        self.slide_in_duration = 0.35
        self.slide_out_duration = 0.35

        # Wait
        self.t1_start = 0
        self.t1_end = self.padding_duration

        # Slide in
        self.t2_start = self.t1_end
        self.t2_end = self.t2_start + self.slide_in_duration

        # Wait
        self.t3_start = self.t2_end
        self.t3_end = self.duration - (self.slide_out_duration + self.padding_duration)

        # Slide out
        self.t4_start = self.t3_end
        self.t4_end = self.t4_start + self.slide_out_duration

        # Wait
        self.t5_start = self.t4_end
        self.t5_end = self.duration

        self.lambda_func = self.get_lambda()

    def ease_out_quad(self, x):
        return 1 - (1 - x) * (1 - x)

    def get_lambda(self):
        def compute_position(t):

            if self.t1_start <= t < self.t1_end:
                return config.VIDEO_WIDTH

            elif self.t2_start <= t < self.t2_end:
                progress = (t - self.t2_start) / (self.t2_end - self.t2_start)
                eased_progress = self.ease_out_quad(progress)
                return -config.VIDEO_WIDTH + eased_progress * config.VIDEO_WIDTH

            elif self.t3_start <= t < self.t3_end:
                return 0

            elif self.t4_start <= t < self.t4_end:
                progress = (t - self.t4_start) / (self.t4_end - self.t4_start)
                eased_progress = self.ease_out_quad(progress)
                return eased_progress * config.VIDEO_WIDTH

            else:
                return config.VIDEO_WIDTH

        return lambda t: (compute_position(t), 0)


class ContentSlideInSlideOut:
    def __init__(self, duration):
        self.duration = duration
        self.padding_duration = 0.5
        self.slide_in_duration = 0.2
        self.slide_out_duration = 0.2

        # Wait
        self.t1_start = 0
        self.t1_end = self.padding_duration

        # Slide in
        self.t2_start = self.t1_end
        self.t2_end = self.t2_start + self.slide_in_duration

        # Wait
        self.t3_start = self.t2_end
        self.t3_end = self.duration - (self.slide_out_duration + self.padding_duration)

        # Slide out
        self.t4_start = self.t3_end
        self.t4_end = self.t4_start + self.slide_out_duration

        # Wait
        self.t5_start = self.t4_end
        self.t5_end = self.duration

        self.lambda_func = self.get_lambda()

    def ease_out_quad(self, x):
        return 1 - (1 - x) * (1 - x)

    def get_lambda(self):
        def compute_position(t):

            if self.t1_start <= t < self.t1_end:
                return config.VIDEO_HEIGHT / 2

            elif self.t2_start <= t < self.t2_end:
                progress = (t - self.t2_start) / (self.t2_end - self.t2_start)
                eased_progress = self.ease_out_quad(progress)
                return config.VIDEO_HEIGHT / 2 * (1 - eased_progress)

            elif self.t3_start <= t < self.t3_end:
                return 0

            elif self.t4_start <= t < self.t4_end:
                progress = (t - self.t4_start) / (self.t4_end - self.t4_start)
                eased_progress = self.ease_out_quad(progress)
                return config.VIDEO_HEIGHT / 2 * eased_progress

            else:
                return config.VIDEO_HEIGHT

        return lambda t: (0, compute_position(t))


def create_text_clip(text, font, font_size, color, alignment, duration):

    clip_tmp = TextClip(txt=text,
                        size=(0.9 * config.VIDEO_WIDTH, 0.9 * config.VIDEO_HEIGHT),
                        bg_color="transparent",
                        color=color,
                        font=font,
                        fontsize=font_size,
                        method="caption",
                        align=alignment,
                        transparent=True)

    clip = CompositeVideoClip(
        clips=[
            clip_tmp.set_position((0.05 * config.VIDEO_WIDTH, 0.05 * config.VIDEO_HEIGHT))
        ],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    )

    clip = clip.set_duration(duration)
    return clip


def create_image_clip(path, duration):
    clip = ImageClip(path)
    clip = clip.set_duration(duration)
    return clip


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

    for digest_file in input_list:
        file_path = f'{config.DATA_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate content clip')

    outputs = list()

    remaining_digests = digests
    pids = set()

    while True:

        if len(remaining_digests) == 0 and len(pids) == 0:
            break

        while True:

            if len(pids) >= config.GENERATECLIPS_NUM_CONCURRENT:
                break

            if len(remaining_digests) == 0:
                break

            digest = remaining_digests.pop(0)

            pid = os.fork()
            if pid != 0:
                pids.add(pid)
                id = f'{digest.id.replace("yaml", "mp4")}'
                outputs.append(f'{config.GENERATECLIP_RELATIVE_FOLDER}/{id}')
                continue

            image_clips = list()
            image_animations = list()

            text_filter_clips = list()
            text_clips = list()
            text_animations = list()

            logo_clip = None

            # Generate title text clip

            title_duration = int(utils.count_words(digest.title) * config.GENERATECLIPS_TITLE_SEC_PER_WORD) + 2

            text_filter_clips.append(create_image_clip(config.GENERATECLIPS_TITLE_FILTER_FILE, title_duration))

            text_clips.append(create_text_clip(digest.title.upper(),
                                               config.GENERATECLIPS_TITLE_FONT,
                                               config.GENERATECLIPS_TITLE_FONT_SIZE,
                                               config.GENERATECLIPS_TITLE_COLOR,
                                               "Center",
                                               title_duration))

            text_animations.append(TitleSlideInSlideOut(title_duration))

            # Generate content text clip

            for idx, line in enumerate(digest.content):

                content_duration = int(utils.count_words(line) * config.GENERATECLIPS_CONTENT_SEC_PER_WORD) + 2

                text_filter_clips.append(create_image_clip(config.GENERATECLIPS_CONTENT_BACKDROP_FILE, content_duration))

                font_size = config.GENERATECLIPS_CONTENT_FONT_SIZE
                if len(line) > config.GENERATECLIPS_CONTENT_OVERSIZED_CHAR_LIMIT:
                    font_size = config.GENERATECLIPS_CONTENT_OVERSIZED_FONT_SIZE

                text_clips.append(create_text_clip(line,
                                                   config.GENERATECLIPS_CONTENT_FONT,
                                                   font_size,
                                                   config.GENERATECLIPS_CONTENT_COLOR,
                                                   "SouthWest",
                                                   content_duration))

                text_animations.append(ContentSlideInSlideOut(content_duration))

            # Generate image clip

            image_duration = 0
            for i in reversed(range(len(text_clips))):

                image_duration += text_clips[i].duration

                if i not in digest.media:
                    continue

                media_path = f'{config.DATA_FOLDER}/{digest.media[i].id}'
                logging.info(media_path)
                image_clips.insert(0, create_image_clip(media_path, image_duration))
                image_duration = 0

            # Generate logo clips

            logo_duration = 0
            for i in range(len(text_clips)):
                logo_duration += text_clips[i].duration

            logo_clip = create_image_clip(config.GENERATECLIPS_LOGO_FILE, logo_duration)

            # Composite clips

            clips = list()

            prev_end = 0
            for image in image_clips:
                start = prev_end
                prev_end = start + image.duration
                clips.append(image.set_start(start).set_end(prev_end))

            prev_end = 0
            for idx in range(len(text_filter_clips)):

                filter = text_filter_clips[idx]
                text = text_clips[idx]
                animation = text_animations[idx]

                start = prev_end
                prev_end = start + filter.duration

                clips.append(filter.set_start(start).set_end(prev_end).set_position(animation.lambda_func))
                clips.append(text.set_start(start).set_end(prev_end).set_position(animation.lambda_func))

            clips.append(logo_clip.set_start(0).set_end(logo_clip.duration))

            final_clip = CompositeVideoClip(clips=clips)

            id = f'{digest.id.replace("yaml", "mp4")}'
            file_path = f'{config.GENERATECLIP_FOLDER}/{id}'
            final_clip.write_videofile(file_path,
                                       fps=config.VIDEO_FPS,
                                       bitrate=config.VIDEO_BITRATE,
                                       codec=config.GENERATECLIPS_CODEC,
                                       preset=config.GENERATECLIPS_PRESET,
                                       threads=config.GENERATECLIPS_THREADS,
                                       verbose=False)

            logging.info(f'Saved: {file_path}')
            exit(0)

        time.sleep(5)

        for pid in set(pids):
            result_pid, status = os.waitpid(pid, os.WNOHANG)
            if result_pid != 0:
                pids.remove(pid)
                if os.WIFEXITED(status):
                    logging.info(f"Process {pid} ended with exit code {os.WEXITSTATUS(status)}")
                    if os.WEXITSTATUS(status) != 0:
                        exit(1)
                elif os.WIFSIGNALED(status):
                    logging.info(f"Process {pid} was killed by signal {os.WTERMSIG(status)}")
                    exit(1)

    logging.info(f'[END  ] Generate content clip')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'g_generate_clips/generate_clips ended')

    return [outputs]

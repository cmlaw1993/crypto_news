
import logging
import random
import math
import yaml
import os

from moviepy.video.fx.resize import resize
from moviepy.video.VideoClip import TextClip
from moviepy.editor import *

from common import utils
from common.pydantic.digest import Digest
from config import config
from keys import keys


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

    input_list = sorted(input_list)
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

    for digest in digests:

        durations = list()

        # ################################################################################
        # ################################################################################
        # Generate word based clip
        # ################################################################################
        # Generate title clip

        clips = list()

        title_duration = int(utils.count_words(digest.title) * config.GENERATECLIPS_TITLE_SEC_PER_WORD) + 2
        durations.append(title_duration)

        # --------------------------------------------------------------------------------
        # Generate filter clip

        filter_clip = create_image_clip(config.GENERATECLIPS_TITLE_FILTER_FILE, title_duration)

        # --------------------------------------------------------------------------------
        # Generate text clip

        text_clip = create_text_clip(digest.title.upper(),
                                     config.GENERATECLIPS_TITLE_FONT,
                                     config.GENERATECLIPS_TITLE_FONT_SIZE,
                                     config.GENERATECLIPS_TITLE_COLOR,
                                     "Center",
                                     title_duration)

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

        title_slide_in_slide_out = TitleSlideInSlideOut(title_duration)

        # --------------------------------------------------------------------------------
        # Combine clips

        composite_clip = CompositeVideoClip(
            clips=[
                filter_clip.set_position(title_slide_in_slide_out.lambda_func),
                text_clip.set_position(title_slide_in_slide_out.lambda_func)
            ],
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
        )
        composite_clip.set_duration(title_duration)

        clips.append(composite_clip)

        # ################################################################################
        # Generate content clip

        last_random = -1

        for idx, line in enumerate(digest.content):

            content_duration = int(utils.count_words(line) * config.GENERATECLIPS_CONTENT_SEC_PER_WORD) + 2
            durations.append(content_duration)

            # --------------------------------------------------------------------------------
            # Generate filter clip

            filter_clip = create_image_clip(config.GENERATECLIPS_CONTENT_FILTER_FILE, content_duration)

            # --------------------------------------------------------------------------------
            # Generate backdrop clip

            backdrop_clip = create_image_clip(config.GENERATECLIPS_CONTENT_BACKDROP_FILE, content_duration)

            # --------------------------------------------------------------------------------
            # Generate text clip

            text_clip = create_text_clip(line,
                                         config.GENERATECLIPS_CONTENT_FONT,
                                         config.GENERATECLIPS_CONTENT_FONT_SIZE,
                                         config.GENERATECLIPS_CONTENT_COLOR,
                                         "SouthWest",
                                         content_duration)

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

            content_slide_in_slide_out = ContentSlideInSlideOut(content_duration)

            # --------------------------------------------------------------------------------
            # Combine clips

            composite_clip = CompositeVideoClip(
                clips=[
                    filter_clip.set_position((0, 0)),
                    backdrop_clip.set_position(content_slide_in_slide_out.lambda_func),
                    text_clip.set_position(content_slide_in_slide_out.lambda_func)
                ],
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
            )
            composite_clip = composite_clip.set_duration(content_duration)

            clips.append(composite_clip)

        # Concatenate clips

        word_based_clip = concatenate_videoclips(clips, method="chain")

        # ################################################################################
        # ################################################################################
        # Generate image based clip

        clips = list()

        image_duration = 0

        for i in reversed(range(1 + len(digest.content))):

            image_duration += durations[i]

            if i not in digest.media:
                continue

            media_path = f'{config.DATA_FOLDER}/{digest.media_path}/{digest.media[i]["id"]}'

            image_clip = create_image_clip(media_path, image_duration)
            clips.insert(0, image_clip)

            image_duration = 0

        # Concatenate clips

        image_based_clip = concatenate_videoclips(clips, method="chain")

        # ################################################################################
        # ################################################################################
        # Generate word and image based clip

        total_duration = 0
        for duration in durations:
            total_duration += duration

        final_clip = CompositeVideoClip(
            clips=[
                image_based_clip.set_position((0, 0)),
                word_based_clip.set_position((0, 0))
            ],
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
        )
        final_clip = final_clip.set_duration(total_duration)

        id = f'{digest.id.replace("yaml", "mp4")}'


        file_name = f'{config.GENERATECLIP_FOLDER}/{id}'
        final_clip.write_videofile(file_name,
                                   fps=config.VIDEO_FPS,
                                   codec=config.GENERATECLIPS_CODEC,
                                   preset=config.GENERATECLIPS_PRESET,
                                   threads=config.GENERATECLIPS_THREADS,
                                   verbose=False)


        outputs.append(f'{config.GENERATECLIP_RELATIVE_FOLDER}/{id}')

        logging.info(f'Saved: {file_name}')

    logging.info(f'g_generate_clips/generate_clips ended')

    return outputs
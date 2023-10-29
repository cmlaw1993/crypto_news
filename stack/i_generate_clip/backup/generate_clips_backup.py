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

    width_scale = config.VIDEO_WIDTH / clip.size[0]
    height_scale = config.VIDEO_HEIGHT / clip.size[1]

    if width_scale > height_scale:
        clip = clip.resize(width=config.VIDEO_WIDTH)
    else:
        clip = clip.resize(height=config.VIDEO_HEIGHT)

    clip = clip.crop(
        x_center=clip.size[0] / 2,
        y_center=clip.size[1] / 2,
        width=config.VIDEO_WIDTH,
        height=config.VIDEO_HEIGHT
    )

    clip = clip.set_duration(duration)
    return clip


def run(input_list):

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
    logging.info(f'[BEGIN] Load digests')

    digests = list()

    for digest_file in input_list:
        file_path = f'{config.CODEPATH_FOLDER}/{digest_file}'
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate content clip')

    outputs = list()

    for digest in digests:

        clips = list()

        # ################################################################################
        # Generate title clip

        title_duration = utils.count_words(digest.title) * config.GENERATECLIPS_TITLE_SEC_PER_WORD

        # --------------------------------------------------------------------------------
        # Generate image clip

        image_clip = create_image_clip(digest.title_media, title_duration)

        # --------------------------------------------------------------------------------
        # Generate filter clip

        filter_clip = create_image_clip(config.GENERATECLIPS_TITLE_FILTER_FILE, title_duration)

        # --------------------------------------------------------------------------------
        # Generate text clip

        text_clip = create_text_clip(digest.title.upper(),
                                     config.GENERATECLIPS_TITLE_FONT,
                                     config.GENERATECLIPS_TITLE_FONT_SIZE,
                                     config.GENERATECLIPS_TITLE_COLOR,
                                     "South",
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
                image_clip.set_position((0, 0)),
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

            content_duration = utils.count_words(line) * config.GENERATECLIPS_CONTENT_SEC_PER_WORD

            # --------------------------------------------------------------------------------
            # Generate image clip

            image_clip = create_image_clip(digest.content_media[idx], content_duration)
            
            # Scale image for panning effect
            
            image_width = 1.05 * config.VIDEO_WIDTH
            image_height = 1.05 * config.VIDEO_HEIGHT
            
            image_min_width_offset = 0
            image_max_width_offset = -0.05 * config.VIDEO_WIDTH
            image_half_width_offset = -0.025 * config.VIDEO_WIDTH

            image_min_height_offset = 0
            image_max_height_offset = -0.05 * config.VIDEO_HEIGHT
            image_half_heigth_offset = -0.025 * config.VIDEO_HEIGHT
            
            pan_offsets = (
                # {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_min_width_offset, image_min_height_offset)},
                {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_min_width_offset, image_max_height_offset)},
                # {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_max_width_offset, image_min_height_offset)},
                {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_max_width_offset, image_max_height_offset)},
                {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_min_width_offset, image_half_heigth_offset)},
                {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_max_width_offset, image_half_heigth_offset)},
                # {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_half_width_offset, image_min_height_offset)},
                {'start': (image_half_width_offset, image_half_heigth_offset), 'end': (image_half_width_offset, image_max_height_offset)},
            )

            class ImagePan:
                def __init__(self, start_pos, end_pos, duration):
                    self.start_x = start_pos[0]
                    self.start_y = start_pos[1]
                    self.end_x = end_pos[0]
                    self.end_y = end_pos[1]
                    self.duration = duration
                    self.lambda_func = self.get_lambda()

                def ease_out_quad(self, x):
                    return 1 - (1 - x) * (1 - x)

                def get_lambda(self):
                    def compute_position(t):
                        progress = min(t / self.duration, 1)
                        eased_progress = self.ease_out_quad(progress)
                        new_x = self.start_x + eased_progress * (self.end_x - self.start_x)
                        new_y = self.start_y + eased_progress * (self.end_y - self.start_y)
                        return new_x, new_y

                    return lambda t: compute_position(t)

            while True:
                new_random = random.randint(0, 4)
                if new_random != last_random:
                    last_random = new_random
                    break

            image_pan = ImagePan(pan_offsets[last_random]['start'], pan_offsets[last_random]['end'], content_duration)

            image_clip = image_clip.resize(width=image_width, height=image_height)

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
                            return config.VIDEO_HEIGHT / 4

                        elif self.t2_start <= t < self.t2_end:
                            progress = (t - self.t2_start) / (self.t2_end - self.t2_start)
                            eased_progress = self.ease_out_quad(progress)
                            return config.VIDEO_HEIGHT / 4 * (1 - eased_progress)

                        elif self.t3_start <= t < self.t3_end:
                            return 0

                        elif self.t4_start <= t < self.t4_end:
                            progress = (t - self.t4_start) / (self.t4_end - self.t4_start)
                            eased_progress = self.ease_out_quad(progress)
                            return config.VIDEO_HEIGHT / 4 * eased_progress

                        else:
                            return config.VIDEO_HEIGHT

                    return lambda t: (0, compute_position(t))

            content_slide_in_slide_out = ContentSlideInSlideOut(content_duration)

            # --------------------------------------------------------------------------------
            # Combine clips

            composite_clip = CompositeVideoClip(
                clips=[
                    image_clip.set_position(image_pan.lambda_func),
                    filter_clip.set_position((0, 0)),
                    backdrop_clip.set_position(content_slide_in_slide_out.lambda_func),
                    text_clip.set_position(content_slide_in_slide_out.lambda_func)
                ],
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
            )
            composite_clip = composite_clip.set_duration(content_duration)

            clips.append(composite_clip)

        # Concatenate clips

        concat_clip = concatenate_videoclips(clips)

        id = f'{digest.id.replace("yaml", "mp4")}'

        file_name = f'{config.GENERATECLIP_FOLDER}/{id}'
        concat_clip.write_videofile(file_name, fps=config.VIDEO_FPS, codec=config.VIDEO_CODEC, preset="ultrafast")

        outputs.append(f'{config.GENERATECLIP_RELATIVE_FOLDER}/{id}')

        logging.info(f'Saved: {file_name}')

    logging.info(f'g_generate_clips/generate_clips ended')

    return outputs
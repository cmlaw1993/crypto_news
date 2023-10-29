import logging

from moviepy.editor import *
import moviepy.audio.fx.all as afx

from config import config


def run(clean, input_list):

    logging.info(f'j_combine_clips/combine_clips started')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create folders')

    if not os.path.exists(config.COMBINECLIPS_FOLDER):
        try:
            os.makedirs(config.COMBINECLIPS_FOLDER)
        except:
            logging.error(f'Unable to create folder: {config.COMBINECLIPS_FOLDER}')

    logging.info(f'[END  ] Create folders')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean')

    if clean == True:
        os.system(f'rm -rf {config.COMBINECLIPS_FOLDER}/*')
        logging.info(f'Cleaned: {config.COMBINECLIPS_FOLDER}')
    else:
        logging.info("Clean skipped")

    logging.info(f'[END  ] Clean')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sort input')

    def sort_by_rank(item):
        return item.split(".")[2]

    input_list = sorted(input_list, key=sort_by_rank)

    logging.info(f'[END  ] Sort input')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load clips')

    cover_clips = list()
    content_clips = list()
    duration = 0

    for clip_file in input_list:

        file_path = f'{config.DATA_FOLDER}/{clip_file}'
        clip = VideoFileClip(file_path)
        if clip_file.contains('cover.mp4'):
            cover_clips.append(clip)
        else:
            content_clips.append(clip)
        duration += clip.duration

    clips = content_clips + cover_clips

    logging.info(f'[END  ] Load clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Add intro and outro')

    intro = VideoFileClip(f'{config.DATA_FOLDER}/{config.COMBINECLIPS_INTRO}')
    outro = VideoFileClip(f'{config.DATA_FOLDER}/{config.COMBINECLIPS_OUTRO}')

    clips.insert(0, intro)
    clips.append(outro)

    logging.info(f'[END  ] Add intro and outro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine clips')

    combined = concatenate_videoclips(clips, method='chain')

    music = AudioFileClip(config.COMBINECLIPS_AUDIO)
    audio = afx.audio_loop(music, duration=combined.duration)

    combined.audio = audio

    file_path = f'{config.COMBINECLIPS_FOLDER}/combined.mp4'
    combined.write_videofile(file_path,
                             fps=config.VIDEO_FPS,
                             bitrate=config.VIDEO_BITRATE,
                             codec=config.COMBINECLIPS_CODEC,
                             audio_codec='mp3',
                             preset=config.COMBINECLIPS_PRESET,
                             threads=config.COMBINECLIPS_THREADS,
                             verbose=False)

    logging.info(f'[END  ] Combine clips')
    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'j_combine_clips/combine_clips ended')

    return [[f'{config.COMBINECLIPS_RELATIVE_FOLDER}/combined.mp4']]

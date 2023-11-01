import subprocess
import logging
import yaml

from moviepy.editor import *

from common import utils
from common.pydantic.digest import Digest
from common.pydantic.upload import Upload, Chapter
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
    logging.info(f'[BEGIN] Load articles')

    primary_digests = list()
    secondary_digests = list()

    for digest_file in input_list:

        file_path = os.path.join(config.DATA_FOLDER, digest_file)
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)

        digest_type = digest_file.split('.')[1]
        if digest_type == 'primary':
            primary_digests.append(digest)
        elif digest_type == 'secondary':
            secondary_digests.append(digest)
        else:
            logging.error(f'Invalid digest type: {digest_type}')

    digests = primary_digests + secondary_digests

    logging.info(f'[END  ] Load articles')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load clips')

    clips = list()

    for digest in digests:
        clips.append(os.path.join(config.DATA_FOLDER, digest.clip))

    logging.info(f'[END  ] Load clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Add intro and outro')

    intro = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_INTRO)
    clips.insert(0, intro)

    outro = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_OUTRO)
    clips.append(outro)

    logging.info(f'[END  ] Add intro and outro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Get clip duration')

    durations = list()
    total_duration = 0

    for clip in clips:
        duration = utils.get_video_duration(clip)
        durations.append(duration)
        total_duration += duration

    logging.info(f'[END  ] Add intro and outro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load audio')

    audio = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_AUDIO)

    logging.info(f'[END  ] Load audio')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine clips')

    clip_id = f'clip.final.{config.ACTIVE_DATE_STR}.mp4'
    file_path = os.path.join(config.COMBINECLIPS_FOLDER, clip_id)

    bitrate = config.VIDEO_BITRATE
    fps = config.VIDEO_FPS
    codec = config.VIDEO_CODEC
    preset = config.VIDEO_CODEC_PRESET
    acodec = config.AUDIO_CODEC

    finput = ''
    fconcat = ''
    for idx, clip in enumerate(clips):
        finput += f' -i {clip}'
        fconcat += f'[{idx}:0]'
    finput += f' -stream_loop -1 -i {audio} -shortest '

    afade_start = total_duration - config.COMBINECLIPS_AUDIO_FADE_DURATION
    afade_duration = config.COMBINECLIPS_AUDIO_FADE_DURATION

    ret = os.system(f'ffmpeg {finput} '
                    f' -filter_complex "{fconcat}concat=n={len(clips)}:v=1:a=0[outv]"'
                    f' -af "afade=out:st={afade_start}:d={afade_duration}"'
                    f' -map [outv] -map {len(clips)}a  -acodec {acodec} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {file_path}')
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating media clips')

    logging.info(f'[END  ] Combine clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create and save upload data')

    upload_data = {'id': f'upload.{config.ACTIVE_DATE_STR}.yaml',
                   'clip': os.path.join(config.COMBINECLIPS_RELATIVE_FOLDER, clip_id),
                   'chapters': list()}

    cumulative_duration = 0

    for idx, clip in enumerate(clips):

        chapter_data = dict()

        chapter_data['ts'] = cumulative_duration
        cumulative_duration += durations[idx]

        if idx == 0:
            chapter_data['title'] = 'Introduction'
        elif idx == len(clips) - 1:
            break
        else:
            chapter_data['title'] = digests[idx-1].title

        chapter = Chapter(**chapter_data)

        upload_data['chapters'].append(chapter)

    upload = Upload(**upload_data)

    file_path = f'{config.COMBINECLIPS_FOLDER}/{upload.id}'
    with open(file_path, 'w') as file:
        yaml.dump(upload.model_dump(), file, sort_keys=False)

    outputs = [f'{config.COMBINECLIPS_RELATIVE_FOLDER}/{upload.id}']

    logging.info(f'Saved: {file_path}')

    logging.info(f'[END  ] Create and save upload data')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'j_combine_clips/combine_clips ended')

    return [outputs]

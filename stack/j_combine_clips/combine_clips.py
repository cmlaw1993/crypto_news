import subprocess
import logging

from moviepy.editor import *
import moviepy.audio.fx.all as afx

from config import config


def get_video_duration(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logging.error('Error getting video duration:', result.stderr)
        return None

    try:
        duration = float(result.stdout)
        return int(round(duration))
    except ValueError:
        logging.error('Could not convert duration to float')
        return None


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

    primary_clips = list()
    secondary_clips = list()
    all_clips = list()
    duration = 0

    for clip_file in input_list:

        file_path = os.path.join(config.DATA_FOLDER, clip_file)

        clip_type = clip_file.split('.')[1]
        if clip_type == 'primary':
            primary_clips.append(file_path)
        elif clip_type == 'secondary':
            secondary_clips.append(file_path)
        else:
            logging.error(f'Invalid clip_type: {clip_type}')

    all_clips = primary_clips + secondary_clips

    logging.info(f'[END  ] Load clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Add intro and outro')

    intro = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_INTRO)
    outro = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_OUTRO)
    all_clips.insert(0, intro)
    all_clips.append(outro)

    logging.info(f'[END  ] Add intro and outro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Get clip duration')

    durations = list()
    total_duration = 0

    for clip in all_clips:
        duration = get_video_duration(clip)
        durations.append(duration)
        total_duration += duration

    logging.info(f'[END  ] Add intro and outro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load audio')

    audio = os.path.join(config.DATA_FOLDER, config.COMBINECLIPS_AUDIO)

    logging.info(f'[END  ] Load audio')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine clips')

    id = f'clip.final.{config.ACTIVE_DATE_STR}.mp4'
    file_path = os.path.join(config.COMBINECLIPS_FOLDER, id)

    bitrate = config.VIDEO_BITRATE
    fps = config.VIDEO_FPS
    codec = config.VIDEO_CODEC
    preset = config.VIDEO_CODEC_PRESET
    acodec = config.VIDEO_AUDIO_CODEC

    finput = ''
    fconcat = ''
    for idx, clip in enumerate(all_clips):
        finput += f' -i {clip}'
        fconcat += f'[{idx}:0]'
    finput += f' -stream_loop -1 -i {audio} -shortest '

    afade_start = total_duration - config.COMBINECLIPS_AUDIO_FADE_DURATION
    afade_duration = config.COMBINECLIPS_AUDIO_FADE_DURATION

    ret = os.system(f'ffmpeg {finput} '
                    f' -filter_complex "{fconcat}concat=n={len(all_clips)}:v=1:a=0[outv]"'
                    f' -af "afade=out:st={afade_start}:d={afade_duration}"'
                    f' -map [outv] -map {len(all_clips)}a  -acodec {acodec} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {file_path}')
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating media clips')

    logging.info(f'[END  ] Combine clips')
    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'j_combine_clips/combine_clips ended')

    return [[os.path.join(config.COMBINECLIPS_RELATIVE_FOLDER, id)]]

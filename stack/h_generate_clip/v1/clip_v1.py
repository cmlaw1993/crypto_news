import logging
import yaml
import os

from stack.h_generate_clip.v1.clip_v1_audio import run as run_audio
from stack.h_generate_clip.v1.clip_v1_primary import run as run_primary
from stack.h_generate_clip.v1.clip_v1_secondary import run as run_secondary

from common import utils
from common.pydantic.digest import Digest
from common.pydantic.clipinfo import ClipInfo
from common.pydantic.clipinfo import Chapter
from config import config


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sort input')

    input_list = sorted(input_list)

    logging.info(f'[END  ] Sort input')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load digests')

    primary_digests = list()
    secondary_digests = list()

    for digest_file in input_list:

        file_path = os.path.join(config.DATA_FOLDER, digest_file)
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)

        if '.primary.' in digest_file:
            primary_digests.append(digest)
        elif '.secondary.' in digest_file:
            secondary_digests.append(digest)
        else:
            logging.error(f'Invalid digest.  Expected only primary or secondary: {digest_file}')

    logging.info(f'[END  ] Load digests')

    logging.info(f'------------------------------------------------------------------------------------------')

    audio_path, deficit, padding = run_audio(primary_digests, secondary_digests)
    primary_path, primary_offsets = run_primary(primary_digests, deficit, padding)
    secondary_path, secondary_offsets = run_secondary(secondary_digests, deficit, padding)

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Add enter effects to primary')

    w = config.VIDEO_WIDTH
    h = config.VIDEO_HEIGHT
    fps = config.VIDEO_FPS
    br = config.VIDEO_BITRATE
    vcdc = config.VIDEO_CODEC
    vpre = config.VIDEO_CODEC_PRESET
    pix = config.VIDEO_PIXEL_FORMAT
    clr = config.VIDEO_COLOR_RANGE
    acdc = config.AUDIO_CODEC
    abr = config.AUDIO_BITRATE

    primary_enter_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.primary_enter.mp4')

    duration = utils.get_video_duration(primary_path)
    enter_end = 0.5
    enter_duration = enter_end

    ret = os.system(
        f'ffmpeg -y'
        f' -i {primary_path}'
        f' -filter_complex "'
        f'     [0:v]rgbashift=20:20:enable=\'lte(t,{enter_end})\'[vf0];'
        f'     [vf0]rotate=\'if(  lt(t,{enter_end}),  -0.15*PI+(t/{enter_duration})*0.15*PI,  0  )\'[vf1];'
        f'     [vf1]zoompan=z=\'if(  lt(it,{enter_end}),  2-(it/{enter_duration})*2,  1)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s={w}x{h}:d=1:fps={fps}[vf2]'
        f' "'
        f' -map [vf2]'
        f' -map 0:a'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr}  -t {duration} -r {fps} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {primary_enter_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error adding effects to primary')

    logging.info(f'[END  ] Add exit effects to intro')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine intro and primary')

    intro_primary_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.intro_primary.mp4')

    intro_path = config.GENERATECLIP_V1_INTRO
    trans_path = config.GENERATECLIP_V1_INTRO_TRANSITiON

    trans_start = utils.get_video_duration(intro_path) - 0.5
    trans_start_ms = trans_start * 1000

    ret = os.system(
        f'ffmpeg -y'
        f' -i {intro_path}'
        f' -i {primary_enter_path}'
        f' -i {trans_path}'
        f' -filter_complex "'
        f'     [0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vf0][af0];'
        f'     [2:a]adelay={trans_start_ms}|{trans_start_ms}[a1];'
        f'     [af0][a1]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a];'
        f' "'
        f' -map [vf0]'
        f' -map [a]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {intro_primary_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating primary into intro')

    logging.info(f'[END  ] Combine intro and primary')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine secondary into intro, primary')

    intro_primary_secondary_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.intro_primary_secondary.mp4')
    trans_duration = config.GENERATECLIP_V1_SECONDARY_TRANSITION_DURATION
    trans_offset = utils.get_video_duration(intro_primary_path) - (trans_duration / 2)
    trans_offset_ms = trans_offset * 1000

    trans_audio_path = config.GENERATECLIP_V1_SECONDARY_TRANSITION_AUDIO

    ret = os.system(
        f'ffmpeg -y'
        f' -i {intro_primary_path}'
        f' -i {secondary_path}'
        f' -i {trans_audio_path}'
        f' -filter_complex "'
        f'     [0:v][1:v]xfade=transition=hblur:duration={trans_duration}:offset={trans_offset}[vf0];'
        f'     [2:a]adelay={trans_offset_ms}|{trans_offset_ms}[a1];'
        f'     [0:a][a1]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[af0];'
        f' "'
        f' -map [vf0]'
        f' -map [af0]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {intro_primary_secondary_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating secondary into intro, primary')

    logging.info(f'[END  ] Combine secondary into intro, primary')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine outro into intro, primary, secondary')

    intro_primary_secondary_outro_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.intro_primary_secondary_outro.mp4')

    outro_path = config.GENERATECLIP_V1_OUTRO

    outro_start = utils.get_video_duration(intro_primary_secondary_path) - config.GENERATECLIP_V1_OUTRO_OVERLAP_DURATION

    duration = utils.get_video_duration(intro_primary_secondary_path) - config.GENERATECLIP_V1_OUTRO_OVERLAP_DURATION \
                + utils.get_video_duration(outro_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {intro_primary_secondary_path}'
        f' -i {outro_path}'
        f' -filter_complex "'
        f'     [1:v]setpts=PTS+{outro_start}/TB[v1];'
        f'     [0:v][v1]overlay=0:0[v];'
        f'     [0:a]amix=inputs=1:duration=longest:dropout_transition=0:normalize=0[a];'
        f' "'
        f' -map [v]'
        f' -map [a]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {intro_primary_secondary_outro_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating outro into intro, primary, secondary')

    logging.info(f'[END  ] Combine secondary into intro, primary')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine audio into final clip')

    final_path = os.path.join(config.GENERATECLIP_FOLDER, f'clip.{config.ACTIVE_DATE_STR}.mp4')
    final_relative_path = os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, f'clip.{config.ACTIVE_DATE_STR}.mp4')

    ret = os.system(
        f'ffmpeg -y'
        f' -i {intro_primary_secondary_outro_path}'
        f' -i {audio_path}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[v];'
        f'     [0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a];'
        f' "'
        f' -map [v]'
        f' -map [a]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {final_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error adding audio')

    logging.info(f'[END  ] Combine audio into final clip')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Save digests')

    for digest in primary_digests:
        file_path = os.path.join(config.GENERATECLIP_FOLDER, digest.id)
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)
        logging.info(f'Saved: {digest.id}')

    for digest in secondary_digests:
        file_path = os.path.join(config.GENERATECLIP_FOLDER, digest.id)
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)
        logging.info(f'Saved: {digest.id}')

    logging.info(f'[END  ] Save digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Create clip info')

    chapters = list()

    base_duration = utils.get_video_duration(config.GENERATECLIP_V1_INTRO)

    for idx, offset in enumerate(primary_offsets):

        chapter_data = dict()

        chapter_data['digest'] = os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, primary_digests[idx].id)
        chapter_data['ts'] = int(base_duration + offset)

        chapter = Chapter(**chapter_data)
        chapters.append(chapter)

    base_duration = utils.get_video_duration(config.GENERATECLIP_V1_INTRO) + utils.get_video_duration(primary_path)

    for idx, offset in enumerate(secondary_offsets):

        chapter_data = dict()

        chapter_data['digest'] = os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, secondary_digests[idx].id)
        chapter_data['ts'] = int(base_duration + offset)

        chapter = Chapter(**chapter_data)
        chapters.append(chapter)

    clipinfo_data = {
        'id': f'clipinfo.{config.ACTIVE_DATE_STR}.yaml',
        'clip': final_relative_path,
        'chapters': chapters
    }

    clipinfo = ClipInfo(**clipinfo_data)

    output_relative_path = os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, clipinfo.id)
    output_path = os.path.join(config.GENERATECLIP_FOLDER, clipinfo.id)

    with open(output_path, 'w') as file:
        yaml.dump(clipinfo.model_dump(), file, sort_keys=False)

    logging.info(f'Saved: {clipinfo.id}')

    logging.info(f'[END  ] Create clip info')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Clean temporary files')

    if config.GENERATECLIP_V1_CLEAN_TMP_FILES:
        files = os.listdir(config.GENERATECLIP_FOLDER)
        for file in files:
            if file.startswith('tmp.'):
                f = os.path.join(config.GENERATECLIP_FOLDER, file)
                os.remove(f)
                logging.info(f'Deleted: {file}')

    logging.info(f'------------------------------------------------------------------------------------------')
    return [output_relative_path]


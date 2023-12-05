import logging
import os
from common import utils
from stack.h_generate_clip.v1.clip_v1_common import calculate_text_duration, get_padding
from config import config


def create_oneline(line, out_path):

    font = config.GENERATECLIP_V1_SECONDARY_ONELINE_FONT
    size = config.GENERATECLIP_V1_SECONDARY_ONELINE_SIZE
    color = config.GENERATECLIP_V1_SECONDARY_ONELINE_COLOR
    border_width = config.GENERATECLIP_V1_SECONDARY_ONELINE_BORDER_WIDTH
    border_height = config.GENERATECLIP_V1_SECONDARY_ONELINE_BORDER_HEIGHT
    gravity = config.GENERATECLIP_V1_SECONDARY_ONELINE_GRAVITY

    caption_tmp = out_path + '.caption.txt'
    with open(caption_tmp, 'w') as file:
        file.write(line)

    # Generate text with unlimited height to measure the actual text height

    tbox_width = config.GENERATECLIP_V1_SECONDARY_TEXTBOX_WIDTH[0]
    tbox_height = config.VIDEO_HEIGHT

    ret = os.system(
        f'convert'
        f' -bordercolor transparent'
        f' -border {border_width}x{border_height}'
        f' -background transparent'
        f' -fill {color}'
        f' -font {font}'
        f' -pointsize {size}'
        f' -size {tbox_width - 2 * border_width}x{tbox_height - 2 * border_height}'
        f' -gravity {gravity}'
        f' caption:@{caption_tmp}'
        f' -type truecolormatte'
        f' PNG32:{out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error running image magick')

    min_x, max_x, min_y, max_y = utils.calculate_image_bounds(out_path)
    text_height = max_y - min_y

    # Select the best fit textbox based on text height

    tbox_idx = None

    for idx, height in enumerate(config.GENERATECLIP_V1_SECONDARY_TEXTBOX_HEIGHT):

        if (text_height + (2*border_height)) < height:
            tbox_idx = idx
            break

    if tbox_idx is None:
        logging.error(f'Unable to find suitable textbox for {line}')

    # Regenerate text according to selected textbox height

    tbox_height = config.GENERATECLIP_V1_SECONDARY_TEXTBOX_HEIGHT[tbox_idx]

    ret = os.system(
        f'convert'
        f' -bordercolor transparent'
        f' -border {border_width}x{border_height}'
        f' -background transparent'
        f' -fill {color}'
        f' -font {font}'
        f' -pointsize {size}'
        f' -size {tbox_width - 2 * border_width}x{tbox_height - 2 * border_height}'
        f' -gravity {gravity}'
        f' caption:@{caption_tmp}'
        f' -type truecolormatte'
        f' PNG32:{out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error running image magick')

    return tbox_idx


def create_tbox(tbox_idx, duration, out_path):

    w = config.VIDEO_WIDTH
    h = config.VIDEO_HEIGHT
    fps = config.VIDEO_FPS
    br = config.VIDEO_BITRATE
    vcdc = config.VIDEO_CODEC
    vpre = config.VIDEO_CODEC_PRESET
    pix = config.VIDEO_PIXEL_FORMAT
    clr = config.VIDEO_COLOR_RANGE

    tbox_enter = config.GENERATECLIP_V1_SECONDARY_TEXTBOX_ENTER[tbox_idx]
    tbox_static = config.GENERATECLIP_V1_SECONDARY_TEXTBOX_STATIC[tbox_idx]
    tbox_exit = config.GENERATECLIP_V1_SECONDARY_TEXTBOX_EXIT[tbox_idx]

    tbox_enter_duration = utils.get_video_duration(tbox_enter)
    tbox_exit_duration = utils.get_video_duration(tbox_exit)
    tbox_static_duration = duration - tbox_enter_duration - tbox_exit_duration

    ret = os.system(
        f'ffmpeg -y'
        f' -i {tbox_enter}'
        f' -loop 1 -i {tbox_static}'
        f' -i {tbox_exit}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
        f'     [1:v]scale={w}:{h},setsar=sar=1/1,trim=duration={tbox_static_duration}[vf1];'
        f'     [2:v]scale={w}:{h},setsar=sar=1/1[vf2];'
        f'     [vf0][vf1][vf2]concat=n=3:v=1:a=0[vf3];'
        f' "'
        f' -map [vf3]'
        f' -c:v qtrle -pix_fmt argb'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error generating tbox: {out_path}')


def combine_oneline_tbox(oneline_path, tbox_path, out_path):

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

    duration = utils.get_video_duration(tbox_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {tbox_path}'
        f' -loop 1 -i {oneline_path}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
        f'     [1:v]fade=in:st=0.5:d=0.3:alpha=1,fade=out:st={duration-1}:d=0.3:alpha=1,setsar=sar=1/1,trim=duration={duration}[vf1];'
        f'     [vf0][vf1]overlay=348:420:format=auto[vf2];'
        f' "'
        f' -map [vf2]'
        f' -c:v qtrle'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error combining tbox and oneline')


def generate_secondary_frag(digest, deficit, padding):

    id = digest.id.replace('digest.', 'tmp.')
    id = id.replace('.yaml', '')

    # Calculate duration for each content line

    oneline = digest.oneliner
    oneline_duration = get_padding(deficit, padding) + calculate_text_duration(oneline)

    # Generate oneline

    oneline_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.oneline.png')

    tbox_idx = create_oneline(oneline, oneline_path)

    # Generate tbox

    tbox_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.tbox.mov')

    create_tbox(tbox_idx, oneline_duration, tbox_path)

    # Combine oneline and tbox

    secondary_frag_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.secondary_frag.mov')

    combine_oneline_tbox(oneline_path, tbox_path, secondary_frag_path)

    return secondary_frag_path


def concatenate_secondary_frags(in_paths, out_path):

    # Concatenate fragments

    durations = list()
    inpath = ''
    concat = ''

    for idx, path in enumerate(in_paths):
        durations.append(utils.get_video_duration(path))
        inpath += f' -i {path}'
        concat += f'[{idx}:0]'

    duration = sum(durations)

    ret = os.system(
        f'ffmpeg -y'
        f' {inpath}'
        f' -filter_complex "'
        f'     {concat}concat=n={len(in_paths)}:v=1:a=0[vf0];'
        f' "'
        f' -map [vf0]'
        f' -c:v qtrle'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating secondary fragments')


def combine_secondary_comp_bg(in_path, out_path):

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

    bg_path = config.GENERATECLIP_V1_SECONDARY_BACKGROUND

    entry_duration = config.GENERATECLIP_V1_SECONDARY_ENTRY_DURATION
    total_duration = entry_duration + utils.get_video_duration(in_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {bg_path}'
        f' -i {in_path}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
        f'     [1:v]scale={w}:{h},setsar=sar=1/1,setpts=PTS-STARTPTS+{entry_duration}/TB[vf1];'
        f'     [vf0][vf1]overlay=0:0[vf2];'
        f' "'
        f' -map [vf2]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {total_duration} -b:v {br} -bufsize {br}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining secondary comp to bg')


def combine_logo(in_path, out_path):

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

    duration = utils.get_video_duration(in_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {in_path}'
        f' -loop 1 -i {config.GENERATECLIP_V1_LOGO}'
        f' -filter_complex "'
        f'     [0:v][1:v]overlay=0:0[vf0];'
        f' "'
        f' -map [vf0]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining logo')



def run(secondary_digests, deficit, padding):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate secondary fragments')

    secondary_frag_paths = list()

    for digest in secondary_digests:
        path = generate_secondary_frag(digest, deficit, padding)
        secondary_frag_paths.append(path)

    logging.info(f'[END  ] Generate secondary fragments')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Concatenate secondary fragments')

    secondary_comp_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.secondary_comp.mov')

    concatenate_secondary_frags(secondary_frag_paths, secondary_comp_path)

    logging.info(f'[END  ] Concatenate secondary fragments')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine secondary composition into background')

    secondary_comp_bg_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.secondary_comp_bg.mp4')

    combine_secondary_comp_bg(secondary_comp_path, secondary_comp_bg_path)

    logging.info(f'[END  ] Combine secondary composition into background')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Combine logo')

    secondary_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.secondary.mp4')

    combine_logo(secondary_comp_bg_path, secondary_path)

    logging.info(f'[END  ] Combine logo')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate secondary offsets')

    durations = list()
    for frag in secondary_frag_paths:
        durations.append(utils.get_video_duration(frag))

    secondary_offsets = list()
    for idx in range(len(secondary_frag_paths)):
        offset = config.GENERATECLIP_V1_SECONDARY_ENTRY_DURATION + sum(durations[:idx])
        secondary_offsets.append(offset)

    logging.info(f'[END  ] Calculate secondary offsets')

    logging.info(f'------------------------------------------------------------------------------------------')
    return secondary_path, secondary_offsets

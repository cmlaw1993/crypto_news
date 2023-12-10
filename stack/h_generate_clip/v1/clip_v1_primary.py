import logging
import shutil
import math
import os

from common import utils
from config import config
from stack.h_generate_clip.v1.clip_v1_common import calculate_text_duration, get_padding


def create_media_from_video(duration, in_path, out_path):

    w = config.VIDEO_WIDTH
    h = config.VIDEO_HEIGHT
    fps = config.VIDEO_FPS
    br = config.VIDEO_BITRATE
    vcdc = config.VIDEO_CODEC
    vpre = config.VIDEO_CODEC_PRESET
    pix = config.VIDEO_PIXEL_FORMAT
    clr = config.VIDEO_COLOR_RANGE

    in_duration = utils.get_video_duration(in_path)

    if in_duration < duration:
        ret = os.system(
            f'ffmpeg -y'
            f' -i {in_path}'
            f' -filter_complex "'
            f'     [0:v:0]setpts={math.ceil(duration/in_duration)}*PTS,scale={w}:{h},setsar=sar=1/1[vf0]'
            f' "'
            f' -an '
            f' -map [vf0]'
            f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
            f' {out_path}'
        )
        if os.WEXITSTATUS(ret) != 0:
            logging.error(f'Error creating media clip from video: {in_path}')
    else:
        ret = os.system(
            f'ffmpeg -y '
            f' -i {in_path}'
            f' -filter_complex "'
            f'     [0:v:0]scale={w}:{h},setsar=sar=1/1[vf0]'
            f' "'
            f' -an'
            f' -map [vf0]'
            f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
            f' {out_path}'
        )
        if os.WEXITSTATUS(ret) != 0:
            logging.error(f'Error creating media clip from video: {in_path}')


def create_media_from_image(duration, in_path, out_path):

    w = config.VIDEO_WIDTH
    h = config.VIDEO_HEIGHT
    fps = config.VIDEO_FPS
    br = config.VIDEO_BITRATE
    vcdc = config.VIDEO_CODEC
    vpre = config.VIDEO_CODEC_PRESET
    pix = config.VIDEO_PIXEL_FORMAT
    clr = config.VIDEO_COLOR_RANGE

    ret = os.system(
        f'ffmpeg -y'
        f'  -loop 1 -i {in_path}'
        f' -filter_complex "'
        f'     [0]setsar=1:1,scale=10000:-1,zoompan=z=\'1.2\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)+ih/35*sin(it/4)\':s={w}x{h}:d=1:fps={fps}[vf0];'
        f' "'
        f' -map [vf0]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error creating media clip from image: {in_path}')


def create_media_frag(duration, in_path, out_path):
    if in_path.endswith('.mp4') or in_path.endswith('.mov'):
        create_media_from_video(duration, in_path, out_path)
    else:
        create_media_from_image(duration, in_path, out_path)


def create_media_composite(in_paths, out_path):

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

    # Concatenate fragments

    durations = list()
    inpath = ''
    concat = ''

    for idx, path in enumerate(in_paths):
        durations.append(utils.get_video_duration(path))
        inpath += f' -i {path}'
        concat += f'[{idx}:0]'

    duration = sum(durations)
    tmp_out_path = out_path.replace('.mp4', '.tmp.mp4')

    ret = os.system(
        f'ffmpeg -y'
        f' {inpath}'
        f' -filter_complex "'
        f'     {concat}concat=n={len(in_paths)}:v=1:a=0[vf0]'
        f' "'
        f' -map [vf0]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' {tmp_out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating media fragments into media composite')

    # Overlay transitions

    trans_path = config.GENERATECLIP_V1_PRIMARY_MEDIA_TRANSITION
    trans_dur = utils.get_video_duration(trans_path)
    num_trans = len(in_paths) - 1

    duration = utils.get_video_duration(tmp_out_path)

    for i in range(num_trans):

        last_tmp_out_path = tmp_out_path
        tmp_out_path = out_path.replace('.mp4', f'.tmp_{i}.mp4')

        start = sum(durations[:i + 1]) - (trans_dur / 2)
        start_ms = start * 1000

        # On the first run, input 0 has no audio
        if i == 0:
            ret = os.system(
                f'ffmpeg -y'
                f' -i {last_tmp_out_path}'
                f' -i {trans_path}'
                f' -filter_complex "'
                f'     [1:v]setpts=PTS+{start}/TB[v1];'
                f'     [1:a]adelay={start_ms}|{start_ms}[a1];'
                f'     [0:v][v1]overlay=0:0[v];'
                f'     [a1]amix=inputs=1:duration=longest:dropout_transition=0:normalize=0[a];'
                f' "'
                f' -map [v]'
                f' -map [a]'
                f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
                f' -c:a {acdc} -b:a {abr}'
                f' {tmp_out_path}'
            )
            if os.WEXITSTATUS(ret) != 0:
                logging.error('Error adding primary transitions')
        else:
            ret = os.system(
                f'ffmpeg -y'
                f' -i {last_tmp_out_path}'
                f' -i {trans_path}'
                f' -filter_complex "'
                f'     [1:v]setpts=PTS+{start}/TB[v1];'
                f'     [1:a]adelay={start_ms}|{start_ms}[a1];'
                f'     [0:v][v1]overlay=0:0[v];'
                f'     [0:a][a1]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a];'
                f' "'
                f' -map [v]'
                f' -map [a]'
                f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
                f' -c:a {acdc} -b:a {abr}'
                f' {tmp_out_path}'
            )
            if os.WEXITSTATUS(ret) != 0:
                logging.error('Error adding primary transitions')

    shutil.copy(tmp_out_path, out_path)


def combine_media_bg(in_path, out_path):

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

    bg_path = config.GENERATECLIP_V1_PRIMARY_BACKGROUND

    scaled_w = 0.595 * w
    scaled_h = 0.595 * h

    start_w = 0.1987 * w
    end_w = 0.2232 * w
    delta_w = end_w - start_w

    start_h = 1.0497 * h
    end_h = 0.0123 * h
    delta_h = end_h - start_h

    start_t = config.GENERATECLIP_V1_PRIMARY_ENTRY_DELAY
    end_t = start_t + config.GENERATECLIP_V1_PRIMARY_ENTRY_DURATION
    delta_t = config.GENERATECLIP_V1_PRIMARY_ENTRY_DURATION

    duration = start_t + utils.get_video_duration(in_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {bg_path}'
        f' -i {in_path}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
        f'     [1:v]scale={scaled_w}:{scaled_h},setsar=sar=1/1,setpts=PTS-STARTPTS+{start_t}/TB[vf1];'
        f'     [vf0][vf1]overlay= \'if(  lte(t,{start_t}),  {start_w},  if(  gte(t,{end_t}),  {end_w},  {start_w}+(t-{start_t})/{delta_t}*{delta_w}  )  )\''
        f'                       :\'if(  lte(t,{start_t}),  {start_h},  if(  gte(t,{end_t}),  {end_h},  {start_h}+(t-{start_t})/{delta_t}*{delta_h}  )  )\''
        f'          [vf2];'
        f' "'
        f' -map [vf2]'
        f' -map 1:a'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining media and background: {in_path}')


def generate_title_frag(title, out_path):

    font = config.GENERATECLIP_V1_PRIMARY_TITLE_FONT
    size = config.GENERATECLIP_V1_PRIMARY_TITLE_SIZE
    color = config.GENERATECLIP_V1_PRIMARY_TITLE_COLOR
    border_width = config.GENERATECLIP_V1_PRIMARY_TITLE_BORDER_WIDTH
    border_height = config.GENERATECLIP_V1_PRIMARY_TITLE_BORDER_HEIGHT
    gravity = config.GENERATECLIP_V1_PRIMARY_TITLE_GRAVITY

    caption_tmp = out_path + '.caption.txt'
    with open(caption_tmp, 'w') as file:
        file.write(title.upper())

    while True:

        # Generate text with unlimited height to measure the actual text height

        tbox_width = config.GENERATECLIP_V1_PRIMARY_TEXTBOX_WIDTH
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

        # Regenerate text again but within the alloted height.
        # Text height must remain the same.

        tbox_height = config.GENERATECLIP_V1_PRIMARY_TITLE_TEXTBOX_QUOTA * config.GENERATECLIP_V1_PRIMARY_TEXTBOX_HEIGHT

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
        new_height = max_y - min_y

        if new_height == text_height:
            break

        size -= 1

    logging.info(f'Title size: {size}')


def combine_media_bg_title(media_bg_path, title_path, out_path):

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

    start_w = 0.1094 * w
    end_w = 0.0539 * w
    delta_w = end_w - start_w

    start_h = 1.6324 * h
    end_h = 0.6472 * h
    delta_h = end_h - start_h

    start_t = config.GENERATECLIP_V1_PRIMARY_ENTRY_DELAY
    end_t = start_t + config.GENERATECLIP_V1_PRIMARY_ENTRY_DURATION
    delta_t = config.GENERATECLIP_V1_PRIMARY_ENTRY_DURATION

    duration = utils.get_video_duration(media_bg_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {media_bg_path}'
        f' -loop 1 -i {title_path}'
        f' -filter_complex "'
        f'     [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
        f'     [1:v]fade=in:st=0.50:d=0.85:alpha=1,setsar=sar=1/1,setpts=PTS-STARTPTS+{start_t}/TB[vf1];'
        f'     [vf0][vf1]overlay= \'if(  lte(t,{start_t}),  {start_w},  if(  gte(t,{end_t}),  {end_w},  {start_w}+(t-{start_t})/{delta_t}*{delta_w}  )  )\''
        f'                       :\'if(  lte(t,{start_t}),  {start_h},  if(  gte(t,{end_t}),  {end_h},  {start_h}+(t-{start_t})/{delta_t}*{delta_h}  )  )\''
        f'          [vf2];'
        f' "'
        f' -map [vf2]'
        f' -map 0:a'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining title to media and background: {media_bg_path}')


def create_content_frag(line, out_path):

    font = config.GENERATECLIP_V1_PRIMARY_CONTENT_FONT
    size = config.GENERATECLIP_V1_PRIMARY_CONTENT_SIZE
    color = config.GENERATECLIP_V1_PRIMARY_CONTENT_COLOR
    border_width = config.GENERATECLIP_V1_PRIMARY_CONTENT_BORDER_WIDTH
    border_height = config.GENERATECLIP_V1_PRIMARY_CONTENT_BORDER_HEIGHT
    gravity = config.GENERATECLIP_V1_PRIMARY_CONTENT_GRAVITY

    caption_tmp = out_path + '.caption.txt'
    with open(caption_tmp, 'w') as file:
        file.write(line)

    while True:

        # Generate text with unlimited height to measure the actual text height

        tbox_width = config.GENERATECLIP_V1_PRIMARY_TEXTBOX_WIDTH
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

        # Regenerate text again but within the alloted height.
        # Text height must remain the same.

        tbox_height = config.GENERATECLIP_V1_PRIMARY_CONTENT_TEXTBOX_QUOTA * config.GENERATECLIP_V1_PRIMARY_TEXTBOX_HEIGHT

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
        new_height = max_y - min_y

        if new_height == text_height:
            break

        size -= 1

    logging.info(f'Content size: {size}')


def combine_media_bg_title_content(media_bg_title_path, content_frag_paths, content_durations, out_path):

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

    w_tbox = 0.0539 * w
    h_tbox = (0.6472 * h) \
              + (config.GENERATECLIP_V1_PRIMARY_TITLE_TEXTBOX_QUOTA
                    * config.GENERATECLIP_V1_PRIMARY_TEXTBOX_HEIGHT)

    total_duration = utils.get_video_duration(media_bg_title_path)
    content_duration = sum(content_durations)
    start_anim_duration = total_duration - content_duration

    input = f' -i {media_bg_title_path}'
    filter = f' [0:v]scale={w}:{h},setsar=sar=1/1[vf0];'
    last_out = f'vf0'

    for idx, content_frag_path in enumerate(content_frag_paths):

        start_t = start_anim_duration + sum(content_durations[:idx])
        end_t = start_t + content_durations[idx]
        delta_t = end_t - start_t

        fade_st = 0
        if idx == 0:
            fade_st = 2.5

        input += f' -loop 1 -i {content_frag_path}'
        filter += f'[{idx+1}:v]fade=in:st={fade_st}:d=1.1:alpha=1,fade=out:st={delta_t-1.1}:d=1.1:alpha=1,setsar=sar=1/1,setpts=PTS-STARTPTS+{start_t}/TB[sf{idx+1}];'
        filter += f'[{last_out}][sf{idx+1}]overlay={w_tbox}:{h_tbox}[vf{idx+1}];'

        last_out = f'vf{idx+1}'

    ret = os.system(
        f'ffmpeg -y'
        f' {input}'
        f' -filter_complex "'
        f'     {filter}'
        f' "'
        f' -map [{last_out}]'
        f' -map 0:a'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {total_duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining content to media, background and title: {media_bg_title_path}')


def combine_logo(media_bg_title_content_path, out_path):

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

    duration = utils.get_video_duration(media_bg_title_content_path)

    ret = os.system(
        f'ffmpeg -y'
        f' -i {media_bg_title_content_path}'
        f' -loop 1 -i {config.GENERATECLIP_V1_LOGO}'
        f' -filter_complex "'
        f'     [0:v][1:v]overlay=0:0[vf0];'
        f' "'
        f' -map [vf0]'
        f' -map 0:a'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error combining logo')


def generate_primary_frag(digest, deficit, padding):

    content_durations = list()
    media_durations = list()
    media_frag_paths = list()
    content_frag_paths = list()

    id = digest.id.replace('digest.', 'tmp.')
    id = id.replace('.yaml', '')

    # Calculate duration for each content line

    for idx, line in enumerate(digest.content):

        duration = calculate_text_duration(line) + get_padding(deficit, padding)
        if idx == 0:
            duration += calculate_text_duration(digest.title) + get_padding(deficit, padding)

        content_durations.append(duration)

        if idx in digest.media.keys():
            media_durations.append(0)
        media_durations[-1] += duration

    # Generate media fragments

    sorted_media = [ digest.media[k] for k in sorted(digest.media.keys()) ]

    for idx, media in enumerate(sorted_media):

        input_path = os.path.join(config.DATA_FOLDER, media.id)
        media_frag_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.{idx}.media_frag.mp4')

        create_media_frag(media_durations[idx], input_path, media_frag_path)

        media_frag_paths.append(media_frag_path)

    # Combine media fragments into media composite

    media_comp_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.media_comp.mp4')

    create_media_composite(media_frag_paths, media_comp_path)

    # Combine media composite into background

    media_bg_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.media_bg.mp4')

    combine_media_bg(media_comp_path, media_bg_path)

    # Generate title fragments

    title_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.title_frag.png')

    generate_title_frag(digest.title, title_path)

    # Combine title into media and background

    media_bg_title_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.media_bg_title.mp4')

    combine_media_bg_title(media_bg_path, title_path, media_bg_title_path)

    # Generate content fragments

    for idx, line in enumerate(digest.content):

        content_frag_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.{idx}.content_frag.mp4')

        create_content_frag(line, content_frag_path)

        content_frag_paths.append(content_frag_path)

    # Combine content into media, background and title

    media_bg_title_content_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.media_bg_title_content.mp4')

    combine_media_bg_title_content(media_bg_title_path, content_frag_paths, content_durations, media_bg_title_content_path)

    # Add logo to produce the final fragment

    primary_frag_path = os.path.join(config.GENERATECLIP_FOLDER, f'{id}.primary_frag.mp4')

    combine_logo(media_bg_title_content_path, primary_frag_path)

    return primary_frag_path



def concatenate_primary_frags(in_paths, out_path):

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

    # Concatenate fragments

    durations = list()
    inpath = ''
    concat = ''

    for idx, path in enumerate(in_paths):
        durations.append(utils.get_video_duration(path))
        inpath += f' -i {path}'
        concat += f'[{idx}:v][{idx}:a]'

    duration = sum(durations)
    tmp_out_path = out_path.replace('.mp4', '.tmp.mp4')

    ret = os.system(
        f'ffmpeg -y'
        f' {inpath}'
        f' -filter_complex "'
        f'     {concat}concat=n={len(in_paths)}:v=1:a=1[vf0][af0];'
        f' "'
        f' -map [vf0]'
        f' -map [af0]'
        f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
        f' -c:a {acdc} -b:a {abr}'
        f' {tmp_out_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error('Error concatenating primary fragments')

    # Overlay transitions

    trans_path = config.GENERATECLIP_V1_PRIMARY_TRANSITION
    trans_dur = utils.get_video_duration(trans_path)
    num_trans = len(in_paths) - 1

    duration = utils.get_video_duration(tmp_out_path)

    for i in range(num_trans):

        last_tmp_out_path = tmp_out_path
        tmp_out_path = out_path.replace('.mp4', f'.tmp_{i}.mp4')

        start = sum(durations[:i + 1]) - (trans_dur / 2)
        start_ms = start * 1000

        ret = os.system(
            f'ffmpeg -y'
            f' -i {last_tmp_out_path}'
            f' -i {trans_path}'
            f' -filter_complex "'
            f'     [1:v]setpts=PTS+{start}/TB[v1];'
            f'     [1:a]adelay={start_ms}|{start_ms}[a1];'
            f'     [0:v][v1]overlay=0:0[v];'
            f'     [0:a][a1]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a];'
            f' "'
            f' -map [v]'
            f' -map [a]'
            f' -vcodec {vcdc} -preset {vpre} -pix_fmt {pix} -color_range {clr} -r {fps} -t {duration} -b:v {br} -bufsize {br}'
            f' -c:a {acdc} -b:a {abr}'
            f' {tmp_out_path}'
        )
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error adding primary transitions')

    shutil.copy(tmp_out_path, out_path)


def run(primary_digests, deficit, padding):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate primary fragments')

    primary_frag_paths = list()

    for digest in primary_digests:
        path = generate_primary_frag(digest, deficit, padding)
        primary_frag_paths.append(path)

    logging.info(f'[END  ] Generate primary fragments')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Concatenate primary fragments')

    primary_path = os.path.join(config.GENERATECLIP_FOLDER, f'tmp.primary.mp4')

    concatenate_primary_frags(primary_frag_paths, primary_path)

    logging.info(f'[END  ] Concatenate primary fragments')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate primary offsets')

    durations = list()
    for frag in primary_frag_paths:
        durations.append(utils.get_video_duration(frag))

    primary_offsets = list()
    for idx in range(len(primary_frag_paths)):
        offset = sum(durations[:idx])
        primary_offsets.append(offset)

    logging.info(f'[END  ] Calculate primary offsets')

    logging.info(f'------------------------------------------------------------------------------------------')
    return primary_path, primary_offsets

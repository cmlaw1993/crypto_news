import logging
import random
import math
import yaml

from moviepy.editor import *

from common import utils
from common.pydantic.digest import Effects, Digest
from config import config


def run(input_list):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Sort input')

    def sort_by_rank(item):
        return item.split(".")[2]

    input_list = sorted(input_list, key=sort_by_rank)

    logging.info(f'[END  ] Sort input')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Load primary digests')

    digests = list()

    for digest_file in input_list:

        digest_type = digest_file.split('.')[1]
        if digest_type != 'primary':
            continue

        file_path = os.path.join(f'{config.DATA_FOLDER}', f'{digest_file}')
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)

        digest = Digest(**yaml_data)
        digests.append(digest)

    logging.info(f'[END  ] Load primary digests')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate clips')

    outputs = list()

    for digest in digests:

        logging.info(f'Generating primary clip: {digest.id}')

        priority = digest.id.split('.')[2]
        score = digest.id.split('.')[3]
        name = digest.id.split('.')[4]

        base_id = f'clip.primary.{priority}.{score}.{name}'

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
        codec = config.VIDEO_CODEC
        preset = config.VIDEO_CODEC_PRESET

        slide_wait_t = config.GENERATECLIP_PRIMARY_SLIDE_WAIT_DURATION
        slide_t = config.GENERATECLIP_PRIMARY_SLIDE_DURATION
        sec_per_word_t = config.GENERATECLIP_PRIMARY_SEC_PER_WORD

        lines = [digest.title]
        for line in digest.content:
            lines.append(line)

        tmps = set()

        # Generate text pngs and calculate duration

        for idx, line in enumerate(lines):

            font = config.GENERATECLIP_PRIMARY_CONTENT_FONT
            size = config.GENERATECLIP_PRIMARY_CONTENT_SIZE
            color = config.GENERATECLIP_PRIMARY_CONTENT_COLOR
            border_width = config.GENERATECLIP_PRIMARY_CONTENT_BORDER_WIDTH
            border_height = config.GENERATECLIP_PRIMARY_CONTENT_BORDER_HEIGHT
            gravity = config.GENERATECLIP_PRIMARY_CONTENT_GRAVITY

            if idx == 0:
                font = config.GENERATECLIP_PRIMARY_TITLE_FONT
                size = config.GENERATECLIP_PRIMARY_TITLE_SIZE
                color = config.GENERATECLIP_PRIMARY_TITLE_COLOR
                border_width = config.GENERATECLIP_PRIMARY_TITLE_BORDER_WIDTH
                border_height = config.GENERATECLIP_PRIMARY_TITLE_BORDER_HEIGHT
                gravity = config.GENERATECLIP_PRIMARY_TITLE_GRAVITY

            text_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.{idx}.text.png')
            tmps.add(text_tmp)

            caption_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.{idx}.caption.txt')
            with open(caption_tmp, 'w') as file:
                file.write(line)
            tmps.add(caption_tmp)

            ret = os.system(f'convert'
                            f' -bordercolor transparent'
                            f' -border {border_width}x{border_height}'
                            f' -background transparent'
                            f' -fill {color}'
                            f' -font {font}'
                            f' -pointsize {size}'
                            f' -size {width-2*border_width}x{height-2*border_height}'
                            f' -gravity {gravity}'
                            f' caption:@{caption_tmp}'
                            f' -type truecolormatte'
                            f' PNG32:{text_tmp}')
            if os.WEXITSTATUS(ret) != 0:
                logging.error('Error running image magick')

            text_pngs.append(text_tmp)

            backdrop_pngs.append(config.GENERATECLIP_PRIMARY_TITLE_BACKDROP)
            if idx > 0:
                min_x, max_x, min_y, max_y = utils.calculate_image_bounds(text_tmp)
                for ref_min_y, b in config.GENERATECLIP_PRIMARY_CONTENT_BACKDROP:
                    if abs(min_y - ref_min_y) < (0.3 * size):
                        backdrop_pngs[-1] = b

            duration = math.ceil((utils.count_words(line) * sec_per_word_t)
                                  + (2 * slide_wait_t)
                                  + (2 * slide_t))
            text_durations.append(duration)
            total_duration += duration

        # Prime media and calculate duration

        media_idx = -1
        for idx in range(len(lines)):
            media_durations.append(0)
            if idx in digest.media.keys():
                media_idx = idx
            media_durations[media_idx] += text_durations[idx]

        for idx, media in digest.media.items():

            media_path = os.path.join(f'{config.DATA_FOLDER}', f'{media.id}')
            media_clip_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.{idx}.media.mp4')
            tmps.add(media_clip_tmp)

            if media.id.endswith('.mp4') or media.id.endswith('.mov'):

                duration = media_durations[idx]
                vid_duration = utils.get_video_duration(media_path)

                if vid_duration < duration:
                    ret = os.system(f'ffmpeg -i {media_path} -vf "setpts={math.ceil(duration/vid_duration)}*PTS,scale={width}:{height}"  -t {duration} -an '
                                    f' -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -t {duration} -b:v {bitrate} -bufsize {bitrate} {media_clip_tmp}')
                    if os.WEXITSTATUS(ret) != 0:
                        logging.error('Error creating media clips from video')
                else:
                    ret = os.system(f'ffmpeg -i {media_path} -vf "scale={width}:{height}" -t {duration} -an'
                                    f' -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -t {duration} -b:v {bitrate} -bufsize {bitrate} {media_clip_tmp}')
                    if os.WEXITSTATUS(ret) != 0:
                        logging.error('Error creating media clips from video')

            else:
                duration = media_durations[idx]
                frames = duration * fps
                zoom_speed = 0.0004
                init_zoom = 1 + (zoom_speed * frames)

                e = media.effects
                if e == Effects.Random.value:
                    e = random.choice(list(Effects)).value

                if e == Effects.ZoomInCenter.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+0.0004\':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInUp.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=iw/2-(iw/zoom/2):y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInUpRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=iw-(iw/zoom):y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=iw-(iw/zoom):y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInDownRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=iw-(iw/zoom):y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInDown.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=iw/2-(iw/zoom/2):y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInDownLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=0:y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=0:y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomInUpLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=10000:-1,zoompan=z=\'zoom+{zoom_speed}\':x=0:y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutCenter.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutUp.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw/2-(iw/zoom/2):y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutUpRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=0:y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=0:y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutDownRight.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=0:y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutDown.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw/2-(iw/zoom/2):y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutDownLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw-(iw/zoom):y=0:d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw-(iw/zoom):y=ih/2-(ih/zoom/2):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'
                elif e == Effects.ZoomOutUpLeft.value:
                    effects = f'-filter_complex "[0]setsar=1:1,scale=12000:-1,zoompan=z=\'if(lte(zoom,1),{init_zoom},max(1,zoom-{zoom_speed}))\':x=iw-(iw/zoom):y=ih-(ih/zoom):d={frames}:s={width}x{height}:fps={fps},fps={fps}[out]"'

                ret = os.system(f'ffmpeg -y -i {media_path}'
                                f' {effects}'
                                f' -map [out] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -t {duration} -b:v {bitrate} -bufsize {bitrate} {media_clip_tmp}')
                if os.WEXITSTATUS(ret) != 0:
                    logging.error('Error creating media clips from image')

            media_clips.append(media_clip_tmp)

        # Concatenate media clips

        media_clip_concat_tmp = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.concat.mp4')
        tmps.add(media_clip_concat_tmp)

        finput = ''
        fconcat = ''
        for idx, media_clip in enumerate(media_clips):
            finput += f' -i {media_clip}'
            fconcat += f'[{idx}:0]'

        ret = os.system(f'ffmpeg {finput} -c copy'
                        f' -filter_complex "{fconcat}concat=n={len(media_clips)}:v=1:a=0[out]"'
                        f' -map [out] -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {media_clip_concat_tmp}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error concatenating media clips')

        # Generate final clip
        # Start with the concatenated media clip as a base

        final_clip = os.path.join(f'{config.GENERATECLIP_FOLDER}', f'{base_id}.mp4')
        os.system(f'cp {media_clip_concat_tmp} {final_clip}')

        final_clip_tmp = f'{final_clip.replace("mp4", "tmp.mp4")}'
        tmps.add(final_clip_tmp)

        # Add content backdrop

        finput = f'-i {final_clip}'
        ffilter = f'[0:v]scale={width}:{height},fps={30}[f0];'
        last_out = f'[f0]'
        cum_dur = 0
        for idx in range(len(text_pngs)):
            dur = text_durations[idx]
            finput += f' -loop 1 -t {dur} -i {backdrop_pngs[idx]}'
            if idx == 0:
                ffilter += f'{last_out}[{idx + 1}]overlay=\'if(lte(t,({cum_dur}+{slide_wait_t}+{slide_t})), -W+((t-{cum_dur}-{slide_wait_t})/{slide_t})*W, if(lte(t,({cum_dur}+{dur}-{slide_wait_t}-{slide_t})), 0, ((t-({cum_dur}+{dur}-{slide_wait_t}-{slide_t}))/{slide_t})*W))\':H-h[f{idx + 1}];'
            else:
                ffilter += f'{last_out}[{idx + 1}]overlay=W-w:\'if(lte(t,({cum_dur}+{slide_wait_t}+{slide_t})), H-((t-{cum_dur}-{slide_wait_t})/{slide_t})*H, if(lte(t,({cum_dur}+{dur}-{slide_wait_t}-{slide_t})), 0, ((t-({cum_dur}+{dur}-{slide_wait_t}-{slide_t}))/{slide_t})*H))\'[f{idx + 1}];'
            cum_dur += dur
            last_out = f'[f{idx + 1}]'

        ret = os.system(f'ffmpeg -y {finput} -filter_complex "{ffilter}"'
                        f' -map {last_out} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {final_clip_tmp}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error adding content backdrop to final clip')

        os.system(f'cp {final_clip_tmp} {final_clip}')

        # Add texts to final clip

        finput = f'-i {final_clip}'
        ffilter = f'[0:v]scale={width}:{height},fps={fps}[f0];'
        last_out = f'[f0]'
        cum_dur = 0
        for idx, text_png in enumerate(text_pngs):
            dur = text_durations[idx]
            finput += f' -loop 1 -t {dur} -i {text_png}'
            if idx == 0:
                ffilter += f'{last_out}[{idx + 1}]overlay=\'if(lte(t,({cum_dur}+{slide_wait_t}+{slide_t})), -W+((t-{cum_dur}-{slide_wait_t})/{slide_t})*W, if(lte(t,({cum_dur}+{dur}-{slide_wait_t}-{slide_t})), 0, ((t-({cum_dur}+{dur}-{slide_wait_t}-{slide_t}))/{slide_t})*W))\':H-h[f{idx + 1}];'
            else:
                ffilter += f'{last_out}[{idx + 1}]overlay=W-w:\'if(lte(t,({cum_dur}+{slide_wait_t}+{slide_t})), H-((t-{cum_dur}-{slide_wait_t})/{slide_t})*H, if(lte(t,({cum_dur}+{dur}-{slide_wait_t}-{slide_t})), 0, ((t-({cum_dur}+{dur}-{slide_wait_t}-{slide_t}))/{slide_t})*H))\'[f{idx + 1}];'
            cum_dur += dur
            last_out = f'[f{idx+1}]'

        ret = os.system(f'ffmpeg -y {finput} -filter_complex "{ffilter}"'
                        f' -map {last_out} -vcodec {codec} -preset {preset} -pix_fmt yuv420p -color_range tv -r {fps} -b:v {bitrate} -bufsize {bitrate} {final_clip_tmp}')
        if os.WEXITSTATUS(ret) != 0:
            logging.error('Error adding texts to final clip')

        os.system(f'cp {final_clip_tmp} {final_clip}')

        # Cleanup temporary files

        for tmp in tmps:
            os.system(f'rm -rf {tmp}')

        # Save digest

        outputs.append(os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, digest.id))

        digest.clip = os.path.join(config.GENERATECLIP_RELATIVE_FOLDER, f'{base_id}.mp4')

        file_path = f'{config.GENERATECLIP_FOLDER}/{digest.id}'
        with open(file_path, 'w') as file:
            yaml.dump(digest.model_dump(), file, sort_keys=False)

        logging.info(f'Saved: {file_path}')

    logging.info(f'[END  ] Generate primary clips')

    logging.info(f'------------------------------------------------------------------------------------------')
    return outputs

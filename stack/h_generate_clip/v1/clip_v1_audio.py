import logging
import os

from common import utils
from config import config

from stack.h_generate_clip.v1.clip_v1_common import calculate_text_duration


def run(primary_digests, secondary_digests):

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate minimum clip duration')

    # Calculate intro_duration

    intro_duration = utils.get_video_duration(config.GENERATECLIP_V1_INTRO)

    # Calculate primary duration

    primary_duration = 0

    for digest in primary_digests:
        primary_duration += config.GENERATECLIP_V1_PRIMARY_ENTRY_DELAY
        primary_duration += calculate_text_duration(digest.title)
        for line in digest.content:
            primary_duration += calculate_text_duration(line)

    # Calculate secondary duration

    secondary_duration = 0
    secondary_duration -= config.GENERATECLIP_V1_SECONDARY_TRANSITION_DURATION
    secondary_duration += config.GENERATECLIP_V1_SECONDARY_ENTRY_DURATION

    for digest in secondary_digests:
        secondary_duration += calculate_text_duration(digest.oneliner)

    # Calculate outro_duration

    outro_duration = utils.get_video_duration(config.GENERATECLIP_V1_OUTRO)
    outro_duration -= config.GENERATECLIP_V1_OUTRO_OVERLAP_DURATION

    # Aggregate duration

    min_duration = intro_duration + primary_duration + secondary_duration + outro_duration

    logging.info(f'intro_duration    : {intro_duration}')
    logging.info(f'primary_duration  : {primary_duration}')
    logging.info(f'secondary_duration: {secondary_duration}')
    logging.info(f'outro_duration    : {outro_duration}')

    logging.info(f'[END  ] Calculate minimum clip duration')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate audio stack')

    A = 0
    B = 1
    C = 2
    D = 3

    audio_durations = [
        utils.get_audio_duration(config.GENERATECLIP_V1_AUDIO[A]),
        utils.get_audio_duration(config.GENERATECLIP_V1_AUDIO[B]),
        utils.get_audio_duration(config.GENERATECLIP_V1_AUDIO[C]),
        utils.get_audio_duration(config.GENERATECLIP_V1_AUDIO[D]),
    ]

    def calculate_stack_duration(st):
        duration = 0
        for s in st:
            duration += audio_durations[s]
        return duration

    stack = list()

    stack.append(D)
    stack.append(A)

    while True:

        tmps = list()

        tmp = list(stack)
        tmp.append(B)
        tmps.append(tmp)

        tmp = list(stack)
        tmp.append(C)
        tmps.append(tmp)

        tmp = list(stack)
        tmp.append(B)
        tmp.append(C)
        tmps.append(tmp)

        # Avoid stacking 3 B's together
        if stack[-1] != B:
            tmp = list(stack)
            tmp.append(B)
            tmp.append(B)
            tmps.append(tmp)

        # Avoid stacking 3 C's together
        if stack[-1] != C:
            tmp = list(stack)
            tmp.append(C)
            tmp.append(C)
            tmps.append(tmp)

        candidate = None
        for tmp in tmps:
            duration = calculate_stack_duration(tmp)
            if duration < min_duration:
                continue
            if candidate is None:
                candidate = list(tmp)
                continue
            if duration < calculate_stack_duration(candidate):
                candidate = list(tmp)
                continue

        if candidate is not None:
            stack = list(candidate)
            break

        stack.append(B)
        stack.append(C)

    # Move D from the front to the back
    stack = stack[1:]
    stack.append(D)

    logging.info(f'[END  ] Calculate audio stack')
    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Generate audio')

    audio_path = os.path.join(config.GENERATECLIP_FOLDER, 'tmp.audio.wav')

    input = ''
    filter = ''
    for idx, s in enumerate(stack):
        input += f' -i {config.GENERATECLIP_V1_AUDIO[s]}'
        filter += f'[{idx}:0]'

    ret = os.system(
        f'ffmpeg -y'
        f' {input}'
        f' -filter_complex "'
        f'     {filter}concat=n={len(stack)}:v=0:a=1[af0];'
        f'     [af0]volume=-10dB[af1];'
        f' "'
        f' -map [af1]'
        f' {audio_path}'
    )
    if os.WEXITSTATUS(ret) != 0:
        logging.error(f'Error creating audio clip')

    logging.info(f'[END  ] Generate audio')

    logging.info(f'------------------------------------------------------------------------------------------')
    logging.info(f'[BEGIN] Calculate duration deficit and padding')

    # Estimate number of lines in the video

    lines = 0

    for digest in primary_digests:
        lines += 1
        for line in digest.content:
            lines += 1

    for digest in secondary_digests:
        lines += 1

    # Calculate deficit

    duration = utils.get_audio_duration(audio_path)
    deficit = duration - min_duration

    # Calculate padding for each line

    padding = utils.round_up(deficit / lines, 0.5)

    logging.info(f'Duration: {duration}')
    logging.info(f'Deficit : {deficit}')
    logging.info(f'Lines   : {lines}')
    logging.info(f'Padding : {padding}')

    logging.info(f'[END  ] Calculate duration deficit and padding')

    logging.info(f'------------------------------------------------------------------------------------------')
    return audio_path, [deficit,], padding

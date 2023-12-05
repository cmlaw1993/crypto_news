from common import utils
from config import config

def calculate_text_duration(text):
    num_words = utils.count_words(text)
    duration = num_words * config.GENERATECLIP_V1_SEC_PER_WORD
    return utils.round_up(duration, 0.1)


def get_padding(deficit, padding):

    if deficit[0] == 0:
        return 0

    if deficit[0] < padding:
        ret = deficit[0]
        deficit[0] = 0
        return ret

    deficit[0] -= padding
    return padding

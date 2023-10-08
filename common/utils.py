import subprocess
import tiktoken
import urllib.parse
from PIL import Image


def to_datetime_str(dt):
    return dt.strftime('%Y%m%d_%H%M%S')


def to_date_str(dt):
    return dt.strftime('%Y%m%d')


def to_time_str(dt):
    return dt.strftime('%H%M%S')


def sanitize_file_name(file_name):

    legal_char ="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    last_c = " "
    ret = ""
    for c in file_name:
        if c in legal_char:
            if last_c == " ":
                ret += c.upper()
            else:
                ret += c
        last_c = c
    return ret


def count_words(input):
    return len(input.split(" "))


def count_tokens(model: str, input_str: str) -> (int, int):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(input_str))


def url_encode(s):
    return urllib.parse.quote(s, safe='/', encoding=None, errors=None)


def calculate_image_bounds(image_path):
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    pixels = image.load()

    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for x in range(width):
        for y in range(height):
            _, _, _, alpha = pixels[x, y]
            if alpha > 0:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    return min_x, max_x, min_y, max_y


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
        return None

    try:
        duration = float(result.stdout)
        return int(round(duration))
    except ValueError:
        return None

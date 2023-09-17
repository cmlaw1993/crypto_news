from datetime import datetime


def sanitize_file_name(file_name):

    legal_char ="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
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



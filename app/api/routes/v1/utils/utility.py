import io

from PIL.Image import Image


def translate_filename(filename: str) -> str:
    """
    Method returns translated filename with spaces ' ' changed to '_'

    :param filename: filename
    :return: translated filename
    """
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    return '_'.join(filename.translate(tr).split(' '))


def get_raw_filename(filename: str) -> str:
    """
    Method returns only raw filename of typed filename.
    Description: if we got file.txt, then 'file' is a raw file name and 'txt' is a file type. Method will return 'file'

    :param filename: typed filename
    :return: raw filename
    """
    filename, filetype = filename.split('.')

    return filename


def convert_pillow_image_to_jpg_bytes(image: Image) -> bytes:
    """
    Method for pillow image to bytes conversion.

    :param image: Pillow image object
    :return: Bytes object
    """
    imag_byte_arr = io.BytesIO()
    image.convert("RGB").save(imag_byte_arr, format='jpeg')
    return imag_byte_arr.getvalue()

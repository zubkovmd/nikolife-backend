import io

from PIL.Image import Image
from fastapi import UploadFile


def translate_all(text: str) -> str:
    """
    Method returns translated filename with spaces ' ' changed to '_'

    :param text: filename
    :return: translated filename
    """
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    return '_'.join(text.translate(tr).split(' '))


def get_raw_filename(filename: str) -> str:
    """
    Method returns only raw filename of typed filename.
    Description: if we got file.txt, then 'file' is a raw file name and 'txt' is a file type. Method will return 'file'

    :param filename: typed filename
    :return: raw filename
    """
    filename, filetype = filename.rsplit('.', 1)

    return filename


def build_full_path(path: str, file: UploadFile):
    """
    Method creates link for file

    :param path: base path
    :param file: file object
    :return: generated link
    """
    filename = f"{path}/{get_raw_filename(file.filename)}"
    filename = translate_all(filename)
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

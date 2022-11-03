import io

from PIL.Image import Image
from fastapi import UploadFile


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


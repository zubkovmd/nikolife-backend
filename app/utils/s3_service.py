"""
Module contains AWS S3 compatible manager for file manipulation.
"""
import io

import boto3
import logging

from PIL import ImageOps, Image
from fastapi import UploadFile

from app.api.routes.v1.utils.utility import convert_pillow_image_to_jpg_bytes
from app.config import settings
from app.constants import BACKEND_HOST, S3_BUCKET, S3_PORT


class S3Manager:
    """
    Manager for AWS S3 compatible services (i use https://min.io).
    Can send files (from drive or memory) and generate links on these files by key.
    """
    _bucket: str
    _instance = None

    def __init__(self):
        """S3 manager initialization"""
        logging.getLogger('botocore').setLevel(logging.CRITICAL)  # turns off botocore logging
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)  # turns off urllib logging
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=settings.s3.acckey,
                                      aws_secret_access_key=settings.s3.seckey,
                                      endpoint_url=settings.s3.endpoint,
                                      )
        self._bucket = settings.s3.bucket

    @classmethod
    def get_instance(cls) -> 'S3Manager':
        """
        Singleton method, returns existing S3Manager instance, or creates it first if instance do not exist.

        :return: database manager instance
        """
        if not S3Manager._instance:
            S3Manager._instance = S3Manager()
            return S3Manager._instance
        else:
            return S3Manager._instance

    def send_file_to_s3(self, filename, object_key) -> None:
        """
        Method sends file from drive to s3 storage.

        :param filename: filename of file that should be sent.
        :param object_key: key (path) of object that will be saved in storage.
        :return:
        """
        self.s3_client.upload_file(Filename=filename, Bucket=self._bucket, Key=object_key)

    def send_image_shaped(self, image: UploadFile, base_filename):
        """
        Method reshapes image to big, med, small and micro sizes and uploads these to s3.

        :param image: UploadFile FastApi object
        :param base_filename: base filename
        :return:
        """
        image_bytes = image.file.read()
        # big image
        filename_big = f"{base_filename}_big.jpg"
        self.send_memory_file_to_s3(
            convert_pillow_image_to_jpg_bytes(ImageOps.contain(Image.open(io.BytesIO(image_bytes)), (2048, 2048))),
            filename_big
        )
        # medium image
        filename_med = f"{base_filename}_med.jpg"
        self.send_memory_file_to_s3(
            convert_pillow_image_to_jpg_bytes(ImageOps.contain(Image.open(io.BytesIO(image_bytes)), (1024, 1024))),
            filename_med
        )
        # small image
        filename_small = f"{base_filename}_small.jpg"
        self.send_memory_file_to_s3(
            convert_pillow_image_to_jpg_bytes(ImageOps.contain(Image.open(io.BytesIO(image_bytes)), (512, 512))),
            filename_small
        )
        # micro image
        filename_micro = f"{base_filename}_micro.jpg"
        self.send_memory_file_to_s3(
            convert_pillow_image_to_jpg_bytes(ImageOps.contain(Image.open(io.BytesIO(image_bytes)), (256, 256))),
            filename_micro
        )

    def send_memory_file_to_s3(self, file, object_key) -> None:
        """
        Method sends file from memory to s3 storage.

        :param file: file in memory that should be sent.
        :param object_key: key (path) of object that will be saved in storage.
        :return:
        """
        self.s3_client.put_object(Body=file, Bucket=self._bucket, Key=object_key)

    def get_url(self, object_key) -> str:
        """
        Method creates link to s3 object and returns it

        :param object_key: key of object.
        :return: link to object.
        """
        return f"http://{BACKEND_HOST}:{S3_PORT}/{S3_BUCKET}/{object_key.replace(' ', '%20')}"

    # def get_url(self, object_key) -> str:
    #     """
    #     Method creates link to s3 object and returns it
    #
    #     :param object_key: key of object.
    #     :return: link to object.
    #     """
    #     return self.s3_client.generate_presigned_url(
    #         'get_object',
    #         Params={
    #             'Bucket': self._bucket,
    #             'Key': object_key
    #         },
    #         ExpiresIn=700000
    #     )

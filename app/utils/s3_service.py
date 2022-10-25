"""
Module contains AWS S3 compatible manager for file manipulation.
"""

import boto3
import logging

from app.config import Settings


class S3Manager:
    """
    Manager for AWS S3 compatible services (i use https://min.io).
    Can send files (from drive or memory) and generate links on this files by key.
    """
    _bucket: str
    _instance = None

    def __init__(self):
        """S3 manager initialization"""
        logging.getLogger('botocore').setLevel(logging.CRITICAL)  # turns off botocore logging
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)  # turns off urllib logging
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=Settings().s3.acckey,
                                      aws_secret_access_key=Settings().s3.seckey,
                                      endpoint_url=Settings().s3.endpoint,
                                      )
        self._bucket = Settings().s3.bucket

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
        return self.s3_client.generate_presigned_url('get_object', Params={'Bucket': self._bucket, 'Key': object_key}, ExpiresIn=700000)


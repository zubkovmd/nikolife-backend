import datetime
import boto3
import logging

from app.config import Settings

logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)


class S3Manager:
    bucket: str

    def __init__(self):
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=Settings().s3.acckey,
                                      aws_secret_access_key=Settings().s3.seckey,
                                      endpoint_url=Settings().s3.endpoint,
                                      )
        print(f"{Settings().s3.acckey=} {Settings().s3.seckey=} {Settings().s3.bucket=}")
        self.bucket = Settings().s3.bucket

    def send_file_to_s3(self, filename, object_key):
        self.s3_client.upload_file(Filename=filename, Bucket=self.bucket, Key=object_key)

    def send_memory_file_to_s3(self, file, object_key):
        self.s3_client.put_object(Body=file, Bucket=self.bucket, Key=object_key)

    def get_url(self, filename):
        return self.s3_client.generate_presigned_url('get_object', Params={'Bucket': self.bucket, 'Key': filename})


manager = S3Manager()

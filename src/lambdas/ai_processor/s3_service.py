import boto3
import logging


class S3Service:
    def __init__(self, bucket_name: str):
        self.client = boto3.client("s3")
        self.logger = logging.getLogger(__name__)
        self.bucket_name = bucket_name
        self.logger.info(f"S3Service initialized for bucket: {self.bucket_name}")

    def get_image_from_s3(self, key: str):
        self.logger.info("getting object with key %s ", key)
        return self.client.get_object(Bucket=self.bucket_name, Key=key)["Body"].read()

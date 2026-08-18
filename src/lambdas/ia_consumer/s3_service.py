"""S3 presigned URL helpers for the IA consumer lambda."""

from urllib.parse import urlparse

import boto3


class S3UrlSigner:
    def __init__(self, region: str = "us-east-1"):
        self.s3_client = boto3.client("s3", region_name=region)

    def create_presigned_url(
        self, s3_file_path: str, expiration_seconds: int = 300
    ) -> str:
        bucket, key = self._parse_s3_uri(s3_file_path)
        return self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration_seconds,
        )

    @staticmethod
    def _parse_s3_uri(s3_uri: str):
        if not isinstance(s3_uri, str) or not s3_uri.startswith("s3://"):
            raise ValueError("Invalid s3_file_path. Expected format: s3://bucket/key")

        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if not bucket or not key:
            raise ValueError("Invalid s3_file_path. Expected format: s3://bucket/key")

        return bucket, key

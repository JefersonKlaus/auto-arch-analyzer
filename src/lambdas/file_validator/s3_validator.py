"""
S3 operations for validating file metadata.
Single Responsibility: Handle all S3 metadata validations.
"""

from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from .errors import FILE_NOT_FOUND, INVALID_FORMAT

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SUPPORTED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}


class S3FileValidator:
    """Validates S3 objects used as input for visual analysis."""

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize S3 validator service.

        Args:
            region: AWS region
        """
        self.s3_client = boto3.client("s3", region_name=region)

    def validate_file(self, s3_file_path: str) -> None:
        """
        Validate S3 object existence, size and supported format.

        Args:
            s3_file_path: Full S3 URI (s3://bucket/key)

        Raises:
            FILE_NOT_FOUND: If object does not exist
            INVALID_FORMAT: If URI, size or format is invalid
            Exception: For unexpected AWS errors
        """
        bucket, key = self._parse_s3_uri(s3_file_path)
        metadata = self._head_object(bucket, key)

        self._validate_size(metadata)
        self._validate_visual_format(key, metadata)

    def _parse_s3_uri(self, s3_uri: str):
        if not isinstance(s3_uri, str) or not s3_uri.startswith("s3://"):
            raise INVALID_FORMAT(
                "Invalid s3_file_path. Expected format: s3://bucket/key"
            )

        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if not bucket or not key:
            raise INVALID_FORMAT(
                "Invalid s3_file_path. Expected format: s3://bucket/key"
            )

        return bucket, key

    def _head_object(self, bucket: str, key: str):
        try:
            return self.s3_client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise FILE_NOT_FOUND(
                    f"File not found in S3: s3://{bucket}/{key}"
                ) from exc
            raise

    @staticmethod
    def _validate_size(metadata):
        object_size = metadata.get("ContentLength", 0)
        if object_size > MAX_FILE_SIZE_BYTES:
            raise INVALID_FORMAT(
                f"File exceeds 5MB limit: {object_size} bytes (max {MAX_FILE_SIZE_BYTES})"
            )

    @staticmethod
    def _validate_visual_format(key: str, metadata):
        content_type = (metadata.get("ContentType") or "").split(";")[0].strip().lower()
        has_supported_extension = any(
            key.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS
        )

        if not has_supported_extension and content_type not in SUPPORTED_CONTENT_TYPES:
            raise INVALID_FORMAT(
                "Unsupported file format for visual analysis. "
                "Supported extensions: .png, .jpg, .jpeg, .webp, .gif"
            )

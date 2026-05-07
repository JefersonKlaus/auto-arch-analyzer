"""
S3 operations for uploading diagrams.
Single Responsibility: Handle all S3 storage operations.
"""

import base64
import uuid
from typing import Optional

import boto3


class S3DiagramUploader:
    """Uploads base64-encoded diagrams to S3 bucket."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize S3 uploader.

        Args:
            bucket_name: Target S3 bucket name
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)

    def upload_diagram(self, base64_diagram: str, email: Optional[str] = None) -> str:
        """
        Upload base64-encoded diagram to S3.

        Args:
            base64_diagram: Base64-encoded diagram image data
            email: Optional email for organizing uploads

        Returns:
            S3 object key (path) where the diagram was stored

        Raises:
            ValueError: If base64 data is invalid
            Exception: If S3 upload fails
        """
        try:
            # Decode base64 to validate format
            diagram_bytes = base64.b64decode(base64_diagram)
        except Exception as e:
            raise ValueError(f"Invalid base64 diagram: {str(e)}")

        # Generate unique key with optional email prefix
        timestamp = str(uuid.uuid4())[:8]
        email_prefix = email.replace("@", "-").split("-")[0] if email else "anonymous"
        s3_key = f"{email_prefix}/{timestamp}-diagram.png"

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=diagram_bytes,
                ContentType="image/png",
                Metadata={
                    "email": email or "not-provided",
                    "upload-timestamp": str(uuid.uuid4()),
                },
            )
            return s3_key
        except Exception as e:
            raise Exception(f"Failed to upload diagram to S3: {str(e)}")

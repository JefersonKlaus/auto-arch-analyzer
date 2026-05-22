"""S3 storage helpers for the PDF/Mail consumer."""

import boto3
from botocore.exceptions import ClientError


class S3ReportStorage:
    """Stores PDF reports in S3 and creates download URLs."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        if not bucket_name:
            raise ValueError("REPORTS_PDF_BUCKET_NAME environment variable not set")

        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)

    def upload_pdf(self, execution_id: str, pdf_bytes: bytes) -> str:
        key = f"reports/{execution_id}/analysis-report.pdf"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=pdf_bytes,
                ContentType="application/pdf",
                Metadata={"execution_id": execution_id},
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to upload report PDF to S3: {exc}") from exc

        return key

    def create_download_url(self, key: str, expiration_seconds: int = 86400) -> str:
        try:
            return self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration_seconds,
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to create presigned URL for S3 report: {exc}") from exc

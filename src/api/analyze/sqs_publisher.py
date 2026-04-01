"""
SQS operations for publishing messages to the ingestion queue.
Single Responsibility: Handle all SQS message publishing.
"""
import json
from typing import Any, Dict, Optional

import boto3


class SQSPublisher:
    """Publishes messages to SQS queue for async processing."""

    def __init__(self, queue_url: str, region: str = "us-east-1"):
        """
        Initialize SQS publisher.

        Args:
            queue_url: Full URL of the SQS queue
            region: AWS region
        """
        self.queue_url = queue_url
        self.sqs_client = boto3.client("sqs", region_name=region)

    def publish_diagram_metadata(
        self,
        s3_key: str,
        s3_bucket: str,
        email: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Publish diagram metadata message to SQS.

        Args:
            s3_key: S3 object key where diagram is stored
            s3_bucket: S3 bucket name
            email: Optional email of requester
            prompt: Optional analysis prompt

        Returns:
            Message ID from SQS

        Raises:
            Exception: If SQS publish fails
        """
        message_body = {
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "email": email,
            "prompt": prompt
        }

        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    "Type": {
                        "StringValue": "DiagramUpload",
                        "DataType": "String"
                    },
                    "Email": {
                        "StringValue": email or "not-provided",
                        "DataType": "String"
                    }
                }
            )
            return response["MessageId"]
        except Exception as e:
            raise Exception(f"Failed to publish message to SQS: {str(e)}")

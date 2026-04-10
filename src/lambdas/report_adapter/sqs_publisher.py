"""
SQS publishing for the report_adapter Lambda.
Single Responsibility: Handle all SQS message publishing operations.
"""

import json

import boto3
from botocore.exceptions import ClientError


class SQSPublisher:
    """Publishes report generation notifications to the PDF-Mail-Queue."""

    def __init__(self, queue_url: str, region: str = "us-east-1"):
        """
        Initialize SQS publisher.

        Args:
            queue_url: Full URL of the PDF-Mail-Queue
            region: AWS region
        """
        self.queue_url = queue_url
        self.sqs_client = boto3.client("sqs", region_name=region)

    def publish_report_notification(self, item_id: str, email: str) -> str:
        """
        Publish a report generation notification to the PDF-Mail-Queue.

        Args:
            item_id: DynamoDB item ID referencing the persisted report
            email: Email address of the requester

        Returns:
            SQS MessageId

        Raises:
            RuntimeError: If the SQS send_message operation fails
        """
        message_body = json.dumps({"db_item_id": item_id, "email": email})

        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageAttributes={
                    "Type": {
                        "StringValue": "ReportGeneration",
                        "DataType": "String",
                    },
                    "Email": {
                        "StringValue": email,
                        "DataType": "String",
                    },
                },
            )
        except ClientError as exc:
            raise RuntimeError(
                f"Failed to send message to SQS: {exc}"
            ) from exc

        return response["MessageId"]

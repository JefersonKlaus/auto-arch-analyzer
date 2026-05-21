"""
DynamoDB persistence for the report_adapter Lambda.
Single Responsibility: Handle all DynamoDB storage operations.
"""

from copy import deepcopy
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from models import ReportAdapterRequest


class DynamoDBRepository:
    """Persists analysis report metadata to DynamoDB."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        """
        Initialize DynamoDB repository.

        Args:
            table_name: Target DynamoDB table name
            region: AWS region
        """
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def save_report(self, request: ReportAdapterRequest) -> str:
        """
        Persist a report item to DynamoDB using a single-table item shape.

        Args:
            request: Validated report adapter request

        Returns:
            The execution_id that was persisted

        Raises:
            RuntimeError: If the DynamoDB put_item operation fails
        """
        result = deepcopy(request.raw_payload)
        for field_name in ("execution_id", "email", "prompt", "s3_file_path"):
            result.pop(field_name, None)

        item = {
            "PK": request.execution_id,
            "SK": "REPORT",
            "execution_id": request.execution_id,
            "email": request.email,
            "prompt": request.prompt or "",
            "image": request.s3_file_path,
            "result": result,
        }

        try:
            self.table.put_item(Item=item)
        except ClientError as exc:
            raise RuntimeError(f"Failed to persist item to DynamoDB: {exc}") from exc

        return request.execution_id

    def update_sqs_message_id(self, execution_id: str, sqs_message_id: str) -> None:
        """
        Update an existing report item with the SQS message identifier.

        Args:
            execution_id: Primary key of the report item
            sqs_message_id: Message identifier returned by SQS

        Raises:
            RuntimeError: If the DynamoDB update_item operation fails
        """
        try:
            self.table.update_item(
                Key={"PK": execution_id, "SK": "REPORT"},
                UpdateExpression="SET sqs_message_id = :sqs_message_id",
                ExpressionAttributeValues={
                    ":sqs_message_id": sqs_message_id,
                },
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to update SQS message id in DynamoDB: {exc}") from exc

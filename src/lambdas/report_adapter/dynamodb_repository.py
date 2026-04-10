"""
DynamoDB persistence for the report_adapter Lambda.
Single Responsibility: Handle all DynamoDB storage operations.
"""

from datetime import datetime, timezone
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

    def save_report(self, request: ReportAdapterRequest, item_id: str) -> str:
        """
        Persist a report item to DynamoDB using the single-table design.

        Args:
            request: Validated report adapter request
            item_id: Unique identifier for this report item

        Returns:
            The item_id that was persisted

        Raises:
            RuntimeError: If the DynamoDB put_item operation fails
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        item = {
            "PK": f"REPORT#{request.email}",
            "SK": f"ANALYSIS#{item_id}",
            "GSI1PK": "STATUS#PENDING",
            "GSI1SK": timestamp,
            "id": item_id,
            "email": request.email,
            "prompt": request.prompt or "",
            "s3_file_path": request.s3_file_path,
            "ai_analysis": request.ai_analysis,
            "status": "PENDING",
            "created_at": timestamp,
        }

        try:
            self.table.put_item(Item=item)
        except ClientError as exc:
            raise RuntimeError(
                f"Failed to persist item to DynamoDB: {exc}"
            ) from exc

        return item_id

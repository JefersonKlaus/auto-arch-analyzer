"""DynamoDB access helpers for the PDF/Mail consumer."""

from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError


class DynamoDBRepository:
    """Loads report items from DynamoDB."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table_name = table_name
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def get_report(self, execution_id: str) -> Dict[str, Any]:
        try:
            response = self.table.get_item(Key={"PK": execution_id, "SK": "REPORT"})
        except ClientError as exc:
            raise RuntimeError(f"Failed to load report from DynamoDB: {exc}") from exc

        item = response.get("Item")
        if not item:
            raise ValueError(f"Report not found for execution_id: {execution_id}")

        return item

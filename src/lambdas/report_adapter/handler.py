"""
Lambda handler for the report_adapter step.
Single Responsibility: Wire dependencies from environment and delegate to orchestrator.
"""

import json
import os

from dynamodb_repository import DynamoDBRepository
from orchestrator import ReportAdapterOrchestrator
from sqs_publisher import SQSPublisher


def lambda_handler(event, context):
    """
    Report adapter handler invoked by Step Functions.

    Expected input:
    {
        "execution_id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "prompt": "Análise de custo",
        "s3_file_path": "s3://bucket/inputs/uuid.bin",
        "technical_analysis": {
            "architecture_summary": {...},
            "service_inventory": [...],
            "architecture_findings": [...]
        }
    }

    Persistence model in DynamoDB:
    - PK: execution_id
    - SK: REPORT
    - email: email
    - prompt: prompt
    - image: s3_file_path
    - result: remaining payload fields

    Returns:
    {
        "status": "SUCCESS",
        "db_item_id": "<uuid>",
        "sqs_message_id": "<sqs-message-id>"
    }
    """
    print(f"report-adapter invoked: {json.dumps(event, default=str)}")

    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    queue_url = os.environ.get("SQS_PDF_MAIL_QUEUE_URL")

    if not table_name:
        raise EnvironmentError("DYNAMODB_TABLE_NAME environment variable not set")
    if not queue_url:
        raise EnvironmentError("SQS_PDF_MAIL_QUEUE_URL environment variable not set")

    orchestrator = ReportAdapterOrchestrator(
        repository=DynamoDBRepository(table_name),
        publisher=SQSPublisher(queue_url),
    )

    result = orchestrator.process(event)

    print(f"report-adapter completed: {json.dumps(result.to_dict())}")
    return result.to_dict()

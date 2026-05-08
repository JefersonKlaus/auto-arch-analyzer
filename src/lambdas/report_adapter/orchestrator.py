"""
Orchestration layer for the report_adapter Lambda.
Single Responsibility: Coordinate the DynamoDB persistence and SQS notification workflow.
"""

import uuid
from typing import Any, Dict

from .dynamodb_repository import DynamoDBRepository
from .models import ReportAdapterRequest, ReportAdapterResult
from .request_parser import RequestParser
from .sqs_publisher import SQSPublisher


class ReportAdapterOrchestrator:
    """Orchestrates report persistence and notification publishing."""

    def __init__(self, repository: DynamoDBRepository, publisher: SQSPublisher):
        """
        Initialize orchestrator with dependencies.

        Args:
            repository: DynamoDB repository for persisting report metadata
            publisher: SQS publisher for notifying the PDF-Mail-Queue
        """
        self.repository = repository
        self.publisher = publisher

    def process(self, event: Dict[str, Any]) -> ReportAdapterResult:
        """
        Process a report adapter event end-to-end.

        Steps:
        1. Parse and validate the request
        2. Persist report metadata to DynamoDB
        3. Publish notification to PDF-Mail-Queue

        Args:
            event: Raw Lambda event from Step Functions

        Returns:
            ReportAdapterResult with status, db_item_id and sqs_message_id

        Raises:
            ValueError: If request validation fails
            RuntimeError: If DynamoDB or SQS operations fail
        """
        request: ReportAdapterRequest = RequestParser.parse_event(event)

        item_id = str(uuid.uuid4())
        self.repository.save_report(request, item_id)

        sqs_message_id = self.publisher.publish_report_notification(
            item_id=item_id,
            email=request.email,
        )

        return ReportAdapterResult(
            status="SUCCESS",
            db_item_id=item_id,
            sqs_message_id=sqs_message_id,
        )

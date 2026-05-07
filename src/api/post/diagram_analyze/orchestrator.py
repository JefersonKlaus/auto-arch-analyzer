"""
Orchestration layer coordinating the analyze workflow.
Single Responsibility: Coordinate interaction between S3 and SQS components.
"""

from typing import Dict, Any

from .request_parser import RequestParser
from .s3_uploader import S3DiagramUploader
from .sqs_publisher import SQSPublisher


class AnalyzeOrchestrator:
    """Orchestrates the diagram upload and queue publishing workflow."""

    def __init__(self, s3_bucket: str, sqs_queue_url: str, region: str = "us-east-1"):
        """
        Initialize orchestrator with dependencies.

        Args:
            s3_bucket: S3 bucket for diagram uploads
            sqs_queue_url: SQS queue URL for ingestion messages
            region: AWS region
        """
        self.s3_uploader = S3DiagramUploader(s3_bucket, region)
        self.sqs_publisher = SQSPublisher(sqs_queue_url, region)

    def process_analyze_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an analyze request end-to-end.

        Steps:
        1. Parse and validate request
        2. Upload diagram to S3
        3. Publish metadata to SQS

        Args:
            event: Lambda event

        Returns:
            Dict with processing results

        Raises:
            ValueError: If validation fails
            Exception: If S3 or SQS operations fail
        """
        # Step 1: Parse request
        request = RequestParser.parse_event(event)

        # Step 2: Upload to S3
        s3_key = self.s3_uploader.upload_diagram(request.diagram, request.email)

        # Step 3: Publish to SQS
        message_id = self.sqs_publisher.publish_diagram_metadata(
            s3_key=s3_key,
            s3_bucket=self.s3_uploader.bucket_name,
            email=request.email,
            prompt=request.prompt,
        )

        # Return success response
        return {
            "s3_key": s3_key,
            "message_id": message_id,
            "email": request.email,
            "prompt": request.prompt,
        }

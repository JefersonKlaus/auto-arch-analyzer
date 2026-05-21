"""
Event parsing for the report_adapter Lambda.
Single Responsibility: Parse and extract the request from a Lambda event.
"""

from typing import Any, Dict

from models import ReportAdapterRequest


class RequestParser:
    """Parses Lambda events from Step Functions into ReportAdapterRequest."""

    @staticmethod
    def parse_event(event: Dict[str, Any]) -> ReportAdapterRequest:
        """
        Parse a Step Functions Lambda event into a validated request.

        Args:
            event: Raw Lambda event dict

        Returns:
            Validated ReportAdapterRequest

        Raises:
            ValueError: If required fields are missing or invalid
        """
        payload = event if isinstance(event, dict) else {}

        return ReportAdapterRequest(
            execution_id=payload.get("execution_id"),
            email=payload.get("email"),
            s3_file_path=payload.get("s3_file_path"),
            prompt=payload.get("prompt"),
            raw_payload=payload,
        )

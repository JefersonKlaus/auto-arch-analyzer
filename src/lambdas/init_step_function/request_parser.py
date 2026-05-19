"""
Request parsing and extraction from Lambda events.
Single Responsibility: Parse and extract input data from Lambda events.
"""

import json
from typing import Any, Dict

from models import InitRequest


class RequestParser:
    """Parses incoming events into InitRequest."""

    @staticmethod
    def parse_event(event: Dict[str, Any]) -> InitRequest:
        """
        Parse Lambda event into InitRequest.

        Supports SQS event records, API Gateway body format, and direct payload.

        Args:
            event: Lambda event from SQS, API Gateway, or direct call

        Returns:
            Validated InitRequest object

        Raises:
            ValueError: If required fields are missing or payload is invalid
            json.JSONDecodeError: If event body is not valid JSON
        """
        body = RequestParser._extract_payload(event)

        try:
            return InitRequest(
                s3_bucket=body["s3_bucket"],
                s3_key=body["s3_key"],
                email=body["email"],
                prompt=body.get("prompt"),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid request: {str(e)}")

    @staticmethod
    def _extract_payload(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract payload from SQS, API Gateway, or direct invocation events.

        Args:
            event: Raw Lambda invocation event

        Returns:
            Payload dictionary

        Raises:
            ValueError: If event shape is unsupported
        """
        if (
            isinstance(event, dict)
            and "Records" in event
            and isinstance(event["Records"], list)
        ):
            if not event["Records"]:
                raise ValueError("Records list is empty")

            first_record = event["Records"][0]
            record_body = first_record.get("body")

            if isinstance(record_body, str):
                return json.loads(record_body)
            if isinstance(record_body, dict):
                return record_body
            raise ValueError("SQS record body must be a JSON string or object")

        if isinstance(event, dict) and "body" in event:
            if isinstance(event["body"], str):
                return json.loads(event["body"])
            if isinstance(event["body"], dict):
                return event["body"]
            raise ValueError("Event body must be a JSON string or object")

        if isinstance(event, dict):
            return event

        raise ValueError("Unsupported event format")

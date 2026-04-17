"""
Request parsing and extraction from Lambda events.
Single Responsibility: Parse and extract input data from Lambda events.
"""

import json
from typing import Any, Dict

from .models import FileValidationRequest


class RequestParser:
    """Parses incoming Step Function payloads into domain models."""

    @staticmethod
    def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Lambda event into a normalized payload dictionary.

        Supports direct payload and body-wrapped payload.

        Args:
            event: Lambda event from Step Functions

        Returns:
            Normalized payload dictionary

        Raises:
            ValueError: If payload is invalid
            json.JSONDecodeError: If body is not valid JSON
        """
        if not isinstance(event, dict):
            raise ValueError("Invalid event: expected object")

        if "body" in event:
            body = event["body"]
            if isinstance(body, str):
                payload = json.loads(body)
            elif isinstance(body, dict):
                payload = body
            else:
                raise ValueError("Invalid event body: expected object or JSON string")
        else:
            payload = event

        if not isinstance(payload, dict):
            raise ValueError("Invalid payload: expected object")

        return payload

    @staticmethod
    def to_request(payload: Dict[str, Any]) -> FileValidationRequest:
        """
        Build validated request model from payload.

        Args:
            payload: Normalized payload dictionary

        Returns:
            Validated FileValidationRequest

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            return FileValidationRequest(
                s3_file_path=payload.get("s3_file_path"),
                email=payload.get("email"),
                prompt=payload.get("prompt"),
            )
        except ValueError as exc:
            raise ValueError(f"Invalid request: {str(exc)}") from exc

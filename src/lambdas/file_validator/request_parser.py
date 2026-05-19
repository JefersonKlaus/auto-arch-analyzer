"""
Request parsing and extraction from Lambda events.
Single Responsibility: Parse and extract input data from Lambda events.
"""

import json
from typing import Any, Dict

from models import FileValidationRequest


class RequestParser:
    """Parses incoming Step Function payloads into domain models."""

    @staticmethod
    def _build_s3_file_path(payload: Dict[str, Any]) -> str:
        """Return the canonical S3 URI from the payload."""
        s3_file_path = payload.get("s3_file_path")
        if isinstance(s3_file_path, str) and s3_file_path.strip():
            return s3_file_path

        s3_bucket = payload.get("s3_bucket")
        s3_key = payload.get("s3_key")

        if isinstance(s3_bucket, str) and isinstance(s3_key, str):
            return f"s3://{s3_bucket}/{s3_key}"

        return ""

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

        s3_file_path = RequestParser._build_s3_file_path(payload)
        if not s3_file_path:
            raise ValueError(
                "Invalid payload: missing s3_file_path or s3_bucket/s3_key"
            )

        payload["s3_file_path"] = s3_file_path

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
                s3_file_path=payload["s3_file_path"],
                email=payload["email"],
                prompt=payload["prompt"],
            )
        except Exception as exc:
            print(payload)
            raise ValueError(f"Invalid request: {str(exc)}") from exc

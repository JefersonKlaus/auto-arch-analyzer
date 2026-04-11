"""
Request parsing and extraction from Lambda events.
Single Responsibility: Parse and extract input data from Lambda events.
"""

import json
from typing import Any, Dict

from .models import AnalyzeRequest


class RequestParser:
    """Parses incoming API Gateway requests into domain models."""

    @staticmethod
    def parse_event(event: Dict[str, Any]) -> AnalyzeRequest:
        """
        Parse Lambda event into AnalyzeRequest.

        Supports both direct JSON body and API Gateway format.

        Args:
            event: Lambda event from API Gateway

        Returns:
            Validated AnalyzeRequest object

        Raises:
            ValueError: If required fields are missing or invalid
            json.JSONDecodeError: If body is not valid JSON
        """
        # Extract body from API Gateway event or direct JSON
        if "body" in event:
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]
        else:
            body = event

        # Extract fields (diagram and email are required, prompt is optional)
        email = body.get("email")
        diagram = body.get("diagram")
        prompt = body.get("prompt")

        # Validate and construct request
        try:
            return AnalyzeRequest(diagram=diagram, email=email, prompt=prompt)
        except ValueError as e:
            raise ValueError(f"Invalid request: {str(e)}")

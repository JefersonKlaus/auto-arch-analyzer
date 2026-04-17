"""
Orchestration layer coordinating the file validation workflow.
Single Responsibility: Coordinate parsing and S3 validation components.
"""

from typing import Any, Dict

from .request_parser import RequestParser
from .s3_validator import S3FileValidator


class FileValidatorOrchestrator:
    """Orchestrates the file-validation workflow."""

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize orchestrator with dependencies.

        Args:
            region: AWS region
        """
        self.s3_validator = S3FileValidator(region)

    def process_validation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input file and return original payload for next state.

        Steps:
        1. Parse event and normalize payload
        2. Build validated request model
        3. Validate referenced file in S3

        Args:
            event: Lambda event from Step Functions

        Returns:
            Original payload dictionary to preserve state contract
        """
        payload = RequestParser.parse_event(event)
        request = RequestParser.to_request(payload)

        self.s3_validator.validate_file(request.s3_file_path)

        return payload

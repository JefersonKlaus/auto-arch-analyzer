"""
Lambda handler for file validation state.
Single Responsibility: Handle Lambda input/output and error propagation.
"""

import os

from orchestrator import FileValidatorOrchestrator
from errors import FILE_NOT_FOUND, INVALID_FORMAT


def lambda_handler(event, context):
    region = os.environ.get("AWS_REGION", "us-east-1")
    orchestrator = FileValidatorOrchestrator(region)

    try:
        return orchestrator.process_validation(event)
    except (FILE_NOT_FOUND, INVALID_FORMAT):
        # Re-raise domain exceptions with their exact names for Step Functions Catch.
        raise
    except Exception as exc:
        print(f"Unexpected error in file validator handler: {str(exc)}")
        raise

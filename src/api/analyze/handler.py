"""
Lambda handler for POST /analyze endpoint.
Single Responsibility: Handle HTTP request/response and error mapping.
"""

import json
import os
from datetime import datetime, timezone
from orchestrator import AnalyzeOrchestrator

from common.response import error_response, success_response


def lambda_handler(event, context):
    """
    POST /analyze handler that processes diagram analysis requests.

    Expected input (JSON):
    {
        "diagram": "base64-encoded-diagram-data",  # REQUIRED
        "email": "user@example.com",               # Optional
        "prompt": "Analysis prompt"                # Optional
    }

    Returns: 202 Accepted with execution metadata
    """
    try:
        # Get environment variables from Terraform
        s3_bucket = os.environ.get("S3_DIAGRAM_BUCKET")
        sqs_queue_url = os.environ.get("SQS_INGESTION_QUEUE_URL")

        # Initialize orchestrator and process request
        orchestrator = AnalyzeOrchestrator(s3_bucket, sqs_queue_url)
        result = orchestrator.process_analyze_request(event)

        # Return 202 Accepted
        return success_response(
            {
                "status": "ACCEPTED",
                "message": "Diagrama aceito para processamento",
                "message_id": result["message_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            202,
        )

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return error_response(
            {
                "error": "Invalid JSON",
                "message": "Payload JSON invalido",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            400,
        )

    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return error_response(
            {
                "error": "Validation failed",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            400,
        )

    except Exception as e:
        print(f"Unexpected error in analyze handler: {str(e)}")
        return error_response(
            {
                "error": "Internal server error",
                "message": "Falha ao processar requisição",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            500,
        )

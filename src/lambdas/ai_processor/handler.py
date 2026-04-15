import os
import logging
from decorators import body_parser
from models import ProcessImageAIDTO
from orchestrator import AIProcessorOrchestrator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Initialization (runs once per container) ---

# Get environment variables once during initialization


# Instantiate the orchestrator once to be reused across warm invocations


@body_parser
def lambda_handler(event, context):
    """
    Lambda handler for the AI processor.
    This function is triggered by an event (e.g., SQS, Step Function) and is
    responsible for analyzing a diagram image using Amazon Bedrock.

    It expects an event payload containing s3_file_path, email, and prompt.

    Returns:
        The JSON analysis result from the AI model, which can be used by the
        caller (e.g., passed to the next state in a Step Function).
    """
    try:
        S3_BUCKET = os.environ.get("S3_DIAGRAM_BUCKET")

        # Fail fast if configuration is missing
        if not S3_BUCKET:
            logger.critical("Missing required environment variable: S3_DIAGRAM_BUCKET")
            raise RuntimeError("Missing required environment variable: S3_DIAGRAM_BUCKET")
        logger.info("AI Processor handler started.")
        payload = event if isinstance(event, dict) else {}
        dto: ProcessImageAIDTO = ProcessImageAIDTO.from_dict(payload)
        orchestrator = AIProcessorOrchestrator(s3_bucket_name=S3_BUCKET)

        result = orchestrator.process_diagram(dto)

        logger.info("AI Processor handler finished successfully.")
        # The result from the orchestrator is the analysis payload,
        # which should be returned directly to the caller (e.g., Step Function).
        return result

    except ValueError as e:
        logger.error("Validation error in from_dict: %s", e)
        # Re-raise to fail the Lambda execution, which can be caught by Step Functions
        raise

    except Exception as e:
        logger.exception("Unexpected error in AI Processor handler: %s", e)
        # Re-raise to fail the Lambda execution
        raise


if __name__ == "__main__":
    sqs_message = {
        "Records": [
            {
                "messageId": "string-gerado-pelo-sqs",
                "receiptHandle": "string-gerado-pelo-sqs",
                "body": "{\"email\": \"emailtest@gmail.com\", \"prompt\": null, \"s3_file_path\": \"voce/95490a0e-diagram.png\"}",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1678886400000",
                    "SenderId": "AIDAIXMPLSPXMPL",
                    "ApproximateFirstReceiveTimestamp": "1678886400000"
                },
                "messageAttributes": {
                    "Type": {
                        "stringValue": "DiagramUpload",
                        "dataType": "String"
                    },
                    "Email": {
                        "stringValue": "user@example.com",
                        "dataType": "String"
                    }
                },
                "md5OfBody": "md5-hash-do-body",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-ingestion-queue-dev",
                "awsRegion": "us-east-1"
            }
        ]
    }
    result = lambda_handler(sqs_message, None)

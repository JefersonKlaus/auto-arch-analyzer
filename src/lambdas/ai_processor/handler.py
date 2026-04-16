import os
import logging
from lambdas.ai_processor.decorators import body_parser
from lambdas.ai_processor.models import ProcessImageAIDTO
from lambdas.ai_processor.orchestrator import AIProcessorOrchestrator

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
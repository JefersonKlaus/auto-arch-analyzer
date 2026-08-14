"""Lambda handler for the IA consumer step."""

import logging
import os

from orchestrator import IAConsumerOrchestrator


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    api_url = os.environ.get("IA_CONSUMER_API_URL")
    api_key = os.environ.get("IA_CONSUMER_API_KEY")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not api_url:
        raise RuntimeError("Missing required environment variable: IA_CONSUMER_API_URL")
    if not api_key:
        raise RuntimeError("Missing required environment variable: IA_CONSUMER_API_KEY")

    logger.info("IA consumer handler started")
    orchestrator = IAConsumerOrchestrator(
        api_url=api_url, api_key=api_key, region=region
    )
    result = orchestrator.process(event if isinstance(event, dict) else {})
    logger.info("IA consumer handler finished successfully")
    return result

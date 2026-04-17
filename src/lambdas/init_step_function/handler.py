"""
Lambda handler for init workflow trigger.
Single Responsibility: Handle event response mapping and error handling.
"""

import logging
import os
import sys
from datetime import datetime, timezone

from orchestrator import InitOrchestrator
from common.response import error_response, success_response


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Init lambda handler that triggers the workflow.

    Supports SQS record payloads, API Gateway body format, and direct invocation.

    Returns: 202 Accepted when workflow execution is started.
    """
    try:
        state_machine_arn = os.environ.get("STEPFUNCTION_STATE_MACHINE_ARN")

        orchestrator = InitOrchestrator(state_machine_arn=state_machine_arn)
        result = orchestrator.process_event(event)

        return success_response(result, 202)

    except ValueError as e:
        logger.error("Validation error in init_step_function: %s", e)
        return error_response(
            {
                "error": "Validation failed",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            400,
        )

    except Exception as e:
        logger.exception("Unexpected error in init_step_function handler: %s", e)
        return error_response(
            {
                "error": "Internal server error",
                "message": "Falha ao processar payload",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            500,
        )

"""
Step Functions operations for workflow initialization.
Single Responsibility: Handle Step Functions execution start.
"""

import logging
import json
import uuid
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StepFunctionTriggerService():
    """Triggers Step Functions execution for validated init payloads."""

    def __init__(self, state_machine_arn: str, region: str = "us-east-1"):
        """
        Initialize Step Functions client.

        Args:
            state_machine_arn: Target state machine ARN
            region: AWS region
        """
        logger.info("Initializing StepFunctionTriggerService.")
        self.state_machine_arn = state_machine_arn
        self.stepclient = boto3.client("stepfunctions", region_name=region)

    def start_step_functions(self, payload: Any) -> str:
        """Start Step Functions execution and return execution ARN."""
        payload_dict = payload.to_dict() if hasattr(payload, "to_dict") else payload
        email = payload_dict.get("email", "unknown") if isinstance(payload_dict, dict) else "unknown"
        logger.info("Attempting to start Step Functions execution for email: %s", email)

        execution_name = f"execution-{uuid.uuid4()}"

        try:
            response = self.stepclient.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=execution_name,
                input=json.dumps(payload_dict),
            )
            execution_arn = response["executionArn"]
            logger.info("Step Functions execution started successfully. ARN: %s", execution_arn)
            return execution_arn
        except Exception as e:
            logger.error("Error starting Step Functions execution: %s", e, exc_info=True)
            raise

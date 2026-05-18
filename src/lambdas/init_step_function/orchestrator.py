"""
Orchestration layer coordinating the init-lambda workflow.
Single Responsibility: Coordinate parsing and Step Functions execution.
"""

from typing import Any, Dict, Optional

from request_parser import RequestParser
from stepfunction_service import StepFunctionTriggerService


class InitOrchestrator:
    """Orchestrates payload parsing and Step Functions triggering."""

    def __init__(
        self,
        state_machine_arn: str,
        region: str = "us-east-1",
        stepfunction_service: Optional[StepFunctionTriggerService] = None,
    ):
        """
        Initialize orchestrator dependencies.

        Args:
            state_machine_arn: Step Functions state machine ARN
            region: AWS region
            stepfunction_service: Optional injected service for testing
        """
        self.stepfunction_service = stepfunction_service or StepFunctionTriggerService(
            state_machine_arn=state_machine_arn,
            region=region,
        )

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an init event end-to-end.

        Steps:
        1. Parse and validate request
        2. Trigger Step Functions execution

        Args:
            event: Lambda event payload

        Returns:
            Dict with status, email, and Step Functions execution ARN
        """
        request = RequestParser.parse_event(event)
        execution_arn = self.stepfunction_service.start_step_functions(request)

        return {
            "status": "ACCEPTED",
            "message": "Payload aceito para processamento",
            "email": request.email,
            "execution_arn": execution_arn,
        }

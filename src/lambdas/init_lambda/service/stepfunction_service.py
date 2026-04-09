import boto3
import uuid
import json
import logging
from dto.original_payload import OriginalPayload  # Importação relativa corrigida

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StepFunctionTriggerService():
    def __init__(self):
        logger.info("Initializing StepFunctionTriggerService.")
        self.stepclient = boto3.client('stepfunctions',
                                       region_name='us-east-1')

    def start_step_functions(self, original_payload: OriginalPayload):
        logger.info(
            f"Attempting to start Step Functions execution for email: {original_payload.email}")
        state_machine_arn = 'arn:aws:states:us-east-1:827088068392:stateMachine:auto-arch-analyzer-workflow'
        execution_name = 'execution' + \
            str(uuid.uuid4())  # Opcional, mas recomendado
        logger.debug(
            f"State Machine ARN: {state_machine_arn}, Execution Name: {execution_name}")
        try:
            response = self.stepclient.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,  # Opcional, mas útil para rastreamento
                # Converte o objeto para dicionário antes de serializar
                input=json.dumps(original_payload.to_dict())
            )
            logger.info(
                f"Step Functions execution started successfully. ARN: {response['executionArn']}, Start Date: {response['startDate']}")
        except Exception as e:
            logger.error(
                f"Error starting Step Functions execution: {e}", exc_info=True)
            raise  # Re-raise the exception after logging

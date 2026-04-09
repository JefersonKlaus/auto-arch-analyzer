import os
import uuid
import json
from dto.original_payload import OriginalPayload
from service.stepfunction_service import StepFunctionTriggerService
import logging


def _extract_payload(event) -> dict:
    # Verifica se é um evento SQS
    if "Records" in event and isinstance(event["Records"], list) and len(event["Records"]) > 0:
        # Assume um único registro para simplicidade, ou processa todos os registros em um loop
        sqs_record = event["Records"][0]
        if "body" in sqs_record and isinstance(sqs_record["body"], str):
            try:
                return json.loads(sqs_record["body"])
            except json.JSONDecodeError:
                print(
                    f"Warning: SQS record body is not valid JSON: {sqs_record['body']}")
                return {}
    # Verifica se é uma invocação direta da Lambda com um campo 'body' (ex: API Gateway)
    elif isinstance(event, dict) and "body" in event:
        if isinstance(event["body"], str):
            try:
                return json.loads(event["body"])
            except json.JSONDecodeError:
                print(
                    f"Warning: Event body is not valid JSON: {event['body']}")
                return {}
        elif isinstance(event["body"], dict):
            return event["body"]
    # Caso contrário, assume que o próprio evento é o dicionário de payload
    return event if isinstance(event, dict) else {}


def lambda_handler(event, context):
    payload = _extract_payload(event)

    # Transforma o dicionário em um objeto OriginalPayload
    try:
        original_payload_obj = OriginalPayload(
            s3_bucket=payload["s3_bucket"],
            s3_key=payload["s3_key"],
            email=payload["email"],
            prompt=payload["prompt"]
        )
        print(
            f"Successfully created OriginalPayload object for email: {original_payload_obj.email}")
        sftservice = StepFunctionTriggerService()
        sftservice.start_step_functions(original_payload_obj)
    except KeyError as e:
        print(f"Error: Missing key in payload for OriginalPayload: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps(f"Missing required field in payload: {e}")
        }
    except Exception as e:
        print(
            f"An unexpected error occurred while creating OriginalPayload: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Internal server error: {e}")
        }


# if __name__ == "__main__":
#     sqs_message = {
#         "Records": [
#             {
#                 "messageId": "string-gerado-pelo-sqs",
#                 "receiptHandle": "string-gerado-pelo-sqs",
#                 "body": "{\"s3_bucket\": \"auto-arch-analyzer-diagram-upload-dev\", \"s3_key\": \"user@example.com/550e8400-e29b-41d4-a716-446655440000-diagram.png\", \"email\": \"user@example.com\", \"prompt\": \"Analyze this architecture\"}",
#                 "attributes": {
#                     "ApproximateReceiveCount": "1",
#                     "SentTimestamp": "1678886400000",
#                     "SenderId": "AIDAIXMPLSPXMPL",
#                     "ApproximateFirstReceiveTimestamp": "1678886400000"
#                 },
#                 "messageAttributes": {
#                     "Type": {
#                         "stringValue": "DiagramUpload",
#                         "dataType": "String"
#                     },
#                     "Email": {
#                         "stringValue": "user@example.com",
#                         "dataType": "String"
#                     }
#                 },
#                 "md5OfBody": "md5-hash-do-body",
#                 "eventSource": "aws:sqs",
#                 "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-ingestion-queue-dev",
#                 "awsRegion": "us-east-1"
#             }
#         ]
#     }

#     lambda_handler(sqs_message, None)

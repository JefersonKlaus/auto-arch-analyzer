import json
import boto3
import uuid
import base64
import os
from datetime import datetime

sqs = boto3.client("sqs")

def lambda_handler(event, context):
    """
    POST /analyze handler
    
    Expected payload:
    {
        "email": "user@example.com",
        "prompt": "Analyze this architecture diagram",
        "diagram": "base64_encoded_image_data"
    }
    
    Returns 202 Accepted immediately and enqueues the data for async processing
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # Validate required fields
        required_fields = ["email", "diagram"]
        for field in required_fields:
            if not body.get(field):
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": f"Missing required field: {field}",
                        "message": "Request must include 'email', 'diagram', and optionally 'prompt'"
                    })
                }

        # Generate execution ID for tracking
        execution_id = str(uuid.uuid4())

        # Validate that diagram is valid base64
        try:
            base64.b64decode(body["diagram"], validate=True)
        except Exception as e:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Invalid base64 encoding",
                    "message": str(e)
                })
            }

        # Prepare message for SQS
        message_body = {
            "execution_id": execution_id,
            "email": body["email"],
            "prompt": body.get("prompt", "Analyze this architecture diagram"),
            "diagram": body["diagram"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "INGESTED"
        }

        # Send to SQS
        sqs_queue_url = os.environ.get("SQS_INGESTION_QUEUE_URL")
        
        if not sqs_queue_url:
            # Fallback: Discover queue by name pattern
            try:
                project_name = os.environ.get("PROJECT_NAME", "archintel-predictor")
                response = sqs.get_queue_url(
                    QueueName=f"{project_name}-ingestion-queue"
                )
                sqs_queue_url = response['QueueUrl']
            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Configuration error",
                        "message": f"Could not find SQS queue: {str(e)}"
                    })
                }

        response = sqs.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                "ExecutionId": {
                    "StringValue": execution_id,
                    "DataType": "String"
                },
                "Email": {
                    "StringValue": body["email"],
                    "DataType": "String"
                }
            }
        )

        # Return 202 Accepted response
        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
                "Location": f"/analyze/{execution_id}"
            },
            "body": json.dumps({
                "message": "Request accepted for processing",
                "execution_id": execution_id,
                "status": "QUEUED",
                "timestamp": datetime.utcnow().isoformat()
            })
        }

    except json.JSONDecodeError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Invalid JSON",
                "message": str(e)
            })
        }
    except Exception as e:
        print(f"Error in analyze handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }

import json
from datetime import datetime, timezone

def lambda_handler(event, context):
    """POST /analyze handler that acknowledges process start."""
    try:
        # Keep API contract simple while orchestration flow is being implemented.
        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "STARTED",
                "message": "Processo de analise iniciado",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Invalid JSON",
                "message": "Payload JSON invalido"
            })
        }
    except Exception as e:
        print(f"Error in analyze handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": "Falha ao iniciar o processo"
            })
        }

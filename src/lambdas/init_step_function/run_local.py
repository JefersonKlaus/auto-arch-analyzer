import json
import os
import sys
from pathlib import Path

# <repo>/src/lambdas/init_step_function/run_local.py
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent.parent
REPO_DIR = SRC_DIR.parent

# Add import paths needed for local execution.
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(1, str(SRC_DIR))
sys.path.insert(2, str(SRC_DIR / "layers" / "common" / "python"))

# Configure required env var for handler/orchestrator.
os.environ.setdefault(
    "STEPFUNCTION_STATE_MACHINE_ARN",
    "arn:aws:states:us-east-1:[ADD_YOUR_ACCOUNT_ID_HERE]:stateMachine:auto-arch-analyzer-workflow",
)

from handler import lambda_handler # noqa: E402


if __name__ == "__main__":
    sqs_message = {
        "Records": [
            {
                "messageId": "string-gerado-pelo-sqs",
                "receiptHandle": "string-gerado-pelo-sqs",
                "body": '{"s3_bucket": "auto-arch-analyzer-diagram-upload-dev", "s3_key": "user@example.com/550e8400-e29b-41d4-a716-446655440000-diagram.png", "email": "user@example.com", "prompt": "Analyze this architecture"}',
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1678886400000",
                    "SenderId": "AIDAIXMPLSPXMPL",
                    "ApproximateFirstReceiveTimestamp": "1678886400000",
                },
                "messageAttributes": {
                    "Type": {"stringValue": "DiagramUpload", "dataType": "String"},
                    "Email": {"stringValue": "user@example.com", "dataType": "String"},
                },
                "md5OfBody": "md5-hash-do-body",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-ingestion-queue-dev",
                "awsRegion": "us-east-1",
            }
        ]
    }
    result = lambda_handler(sqs_message, None)

    print(json.dumps(result, indent=2, ensure_ascii=False))

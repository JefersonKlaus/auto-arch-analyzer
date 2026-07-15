import json


def lambda_handler(event, context):
    print("Workflow error captured:")
    print(json.dumps(event, default=str))

    error_type = event.get("Error", "UnknownError")
    error_cause = event.get("Cause", "No cause provided by parent state")

    return {
        "error": error_type,
        "cause": error_cause,
        "status": "FAILED_AT_ORCHESTRATION",
    }

import json


def lambda_handler(event, context):
    payload = event if isinstance(event, dict) else {}

    email = payload.get("email")
    prompt = payload.get("prompt")
    s3_file_path = payload.get("s3_file_path")

    report = {
        "status": "stub",
        "message": "AI processing not implemented yet",
        "prompt": prompt,
    }

    return {
        "email": email,
        "s3_file_path": s3_file_path,
        "report_json": json.dumps(report),
    }

import os
import uuid


def _extract_payload(event):
    if isinstance(event, dict) and isinstance(event.get("body"), dict):
        return event["body"]
    return event if isinstance(event, dict) else {}


def lambda_handler(event, context):
    payload = _extract_payload(event)

    email = payload.get("email")
    prompt = payload.get("prompt")
    _ = payload.get("base64")

    bucket = os.environ.get("S3_DIAGRAM_BUCKET", "pending-bucket")
    object_key = f"inputs/{uuid.uuid4()}.bin"

    return {
        "email": email,
        "prompt": prompt,
        "s3_file_path": f"s3://{bucket}/{object_key}",
    }

def lambda_handler(event, context):
    payload = event if isinstance(event, dict) else {}

    _ = payload.get("email")
    _ = payload.get("s3_file_path")
    _ = payload.get("report_json")

    return {}

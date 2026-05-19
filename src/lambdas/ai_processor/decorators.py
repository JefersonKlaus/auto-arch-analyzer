from functools import wraps
import json
from typing import Any, Dict


def body_parser(func):
    @wraps(func)
    def wrapper(event, context):
        msg = parse_message(event)
        return func(msg, context)

    return wrapper


def parse_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract payload from SQS, API Gateway, or direct invocation events.

    Args:
        event: Raw Lambda invocation event

    Returns:
        Payload dictionary

    Raises:
        ValueError: If event shape is unsupported
    """
    result: Dict
    result = _extract_from_sqs(event=event)
    if result is None:
        result = _extract_from_gateway(event=event)
    return result


def _extract_from_sqs(event: Dict[str, Any]):
    if (
        isinstance(event, dict)
        and "Records" in event
        and isinstance(event["Records"], list)
    ):
        if not event["Records"]:
            raise ValueError("Records list is empty")

        first_record = event["Records"][0]
        record_body = first_record.get("body")

        if isinstance(record_body, str):
            return json.loads(record_body)
        if isinstance(record_body, dict):
            return record_body
        raise ValueError("SQS record body must be a JSON string or object")


def _extract_from_gateway(event: Dict[str, Any]):
    if isinstance(event, dict) and "body" in event:
        if isinstance(event["body"], str):
            return json.loads(event["body"])
        if isinstance(event["body"], dict):
            return event["body"]
        raise ValueError("Event body must be a JSON string or object")

    if isinstance(event, dict):
        return event

    raise ValueError("Unsupported event format")

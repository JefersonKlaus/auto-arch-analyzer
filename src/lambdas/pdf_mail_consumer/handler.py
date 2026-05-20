"""
Lambda handler for the PDF/Mail SQS consumer.
Single Responsibility: Read SQS records and log the work to be done.
"""

import json
import logging
from typing import Any, Dict, List


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _safe_json_loads(payload: str) -> Any:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def _log_record(record: Dict[str, Any], index: int) -> None:
    body = _safe_json_loads(record.get("body", ""))
    message_attributes = record.get("messageAttributes", {})

    logger.info(
        "pdf-mail-consumer record processed",
        extra={
            "record_index": index,
            "message_id": record.get("messageId"),
            "event_source": record.get("eventSource"),
            "event_source_arn": record.get("eventSourceARN"),
            "body": body,
            "message_attributes": message_attributes,
        },
    )


def lambda_handler(event, context):
    """
    SQS consumer for the PDF/Mail queue.

    Current behavior:
    - Reads each SQS record
    - Logs the payload and message attributes
    - Returns a small summary for direct invocations
    """
    records: List[Dict[str, Any]] = event.get("Records", []) if isinstance(event, dict) else []

    if not records and isinstance(event, dict):
        logger.info("pdf-mail-consumer invoked without SQS records", extra={"event": event})
        return {"status": "NO_RECORDS", "processed_records": 0}

    for index, record in enumerate(records):
        _log_record(record, index)

    logger.info("pdf-mail-consumer finished", extra={"processed_records": len(records)})

    return {"status": "SUCCESS", "processed_records": len(records)}
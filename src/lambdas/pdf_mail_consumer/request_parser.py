"""
Request parsing utilities for the PDF/Mail consumer.
"""

import json
from typing import Any, Dict

from models import PdfMailMessage


def _safe_json_loads(payload: str) -> Any:
    try:
        return json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return payload


class RequestParser:
    @staticmethod
    def parse_record(record: Dict[str, Any]) -> PdfMailMessage:
        body = _safe_json_loads(record.get("body", ""))
        message_attributes = record.get("messageAttributes", {}) or {}

        return PdfMailMessage(
            message_id=record.get("messageId"),
            body=body,
            message_attributes=message_attributes,
            event_source=record.get("eventSource"),
            event_source_arn=record.get("eventSourceARN"),
        )

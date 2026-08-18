"""Request parsing for the IA consumer lambda."""

import json
from typing import Any, Dict

from models import IAConsumerRequest


class RequestParser:
    @staticmethod
    def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("Invalid event: expected object")

        if "body" in event:
            body = event["body"]
            if isinstance(body, str):
                payload = json.loads(body)
            elif isinstance(body, dict):
                payload = body
            else:
                raise ValueError("Invalid event body: expected object or JSON string")
        else:
            payload = event

        if not isinstance(payload, dict):
            raise ValueError("Invalid payload: expected object")

        if not payload.get("imagem_url") and isinstance(payload.get("imagem"), str):
            payload["imagem_url"] = payload["imagem"]

        if (
            not payload.get("s3_file_path")
            and isinstance(payload.get("s3_bucket"), str)
            and isinstance(payload.get("s3_key"), str)
        ):
            payload["s3_file_path"] = f"s3://{payload['s3_bucket']}/{payload['s3_key']}"

        return payload

    @staticmethod
    def to_request(payload: Dict[str, Any]) -> IAConsumerRequest:
        try:
            return IAConsumerRequest(
                prompt=payload["prompt"],
                imagem_url=payload.get("imagem_url"),
                s3_file_path=payload.get("s3_file_path"),
            )
        except Exception as exc:
            raise ValueError(f"Invalid request: {str(exc)}") from exc

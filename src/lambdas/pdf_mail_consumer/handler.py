"""
Lambda handler for the PDF/Mail SQS consumer.

This module follows SRP by delegating parsing and processing to
`request_parser.py` and `orchestrator.py` respectively.
"""

import logging
from typing import Any, Dict, List

from orchestrator import PdfMailConsumerOrchestrator


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Any, context: Any) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = event.get("Records", []) if isinstance(event, dict) else []

    if not records and isinstance(event, dict):
        logger.info("pdf-mail-consumer invoked without SQS records", extra={"event": event})
        return {"status": "NO_RECORDS", "processed_records": 0}

    try:
        orchestrator = PdfMailConsumerOrchestrator()
        result = orchestrator.process_records(records)
        logger.info("pdf-mail-consumer finished", extra={"processed_records": result.get("processed_records")})
        return result

    except Exception:
        logger.exception("Unexpected error in pdf-mail-consumer handler")
        raise
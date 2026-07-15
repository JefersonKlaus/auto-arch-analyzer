"""
Orchestrator for the PDF/Mail consumer.
Single Responsibility: load report data, render artifacts and send e-mail notifications.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from dynamodb_repository import DynamoDBRepository
from models import PdfMailMessage
from report_renderer import build_html_report, build_pdf_report, build_text_report
from request_parser import RequestParser
from s3_service import S3ReportStorage
from ses_service import SesReportMailer


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} environment variable not set")
    return value


class PdfMailConsumerOrchestrator:
    """Orchestrates processing of SQS records for the pdf-mail consumer."""

    def __init__(
        self,
        repository: Optional[DynamoDBRepository] = None,
        storage: Optional[S3ReportStorage] = None,
        mailer: Optional[SesReportMailer] = None,
        region: Optional[str] = None,
    ):
        resolved_region = (
            region
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        self.repository = repository or DynamoDBRepository(
            _env("DYNAMODB_TABLE_NAME"),
            region=resolved_region,
        )
        self.storage = storage or S3ReportStorage(
            _env("REPORTS_PDF_BUCKET_NAME"),
            region=resolved_region,
        )
        self.mailer = mailer or SesReportMailer(
            _env("SES_FROM_EMAIL"),
            region=resolved_region,
        )

    def process_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        parsed: List[PdfMailMessage] = []
        recipients: List[str] = []
        failures: List[Dict[str, str]] = []

        for index, record in enumerate(records):
            msg = RequestParser.parse_record(record)
            parsed.append(msg)

            payload = msg.payload
            execution_id = payload.get("db_item_id") or payload.get("execution_id")
            if not execution_id:
                failures.append(
                    {"record_index": str(index), "reason": "missing_db_item_id"}
                )
                logger.error(
                    "db_item_id missing in SQS record", extra={"record_index": index}
                )
                continue

            try:
                report = self.repository.get_report(execution_id)
                recipient_email = payload.get("email") or report.get("email")
                if not recipient_email:
                    raise ValueError(
                        "email field is required to send the analysis report"
                    )

                logger.info(
                    "Sending report",
                    extra={
                        "recipient_email": recipient_email,
                        "execution_id": execution_id,
                    },
                )

                pdf_bytes = build_pdf_report(report)
                pdf_key = self.storage.upload_pdf(execution_id, pdf_bytes)
                download_url = self.storage.create_download_url(pdf_key)

                html_body = build_html_report(report, download_url)
                text_body = build_text_report(report, download_url)
                subject = f"Architecture analysis report - {execution_id}"

                message_id = self.mailer.send_report_email(
                    recipient_email=recipient_email,
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                )

                recipients.append(recipient_email)

                logger.info(
                    "pdf-mail-consumer report sent",
                    extra={
                        "record_index": index,
                        "sqs_message_id": msg.message_id,
                        "execution_id": execution_id,
                        "pdf_key": pdf_key,
                        "ses_message_id": message_id,
                        "event_source": msg.event_source,
                        "event_source_arn": msg.event_source_arn,
                        "recipient_email": recipient_email,
                    },
                )

            except Exception as exc:
                logger.exception(
                    "Failed to process SQS record",
                    extra={"record_index": index, "sqs_message_id": msg.message_id},
                )
                failures.append(
                    {
                        "record_index": str(index),
                        "execution_id": execution_id or "",
                        "recipient": str(
                            payload.get("email")
                            or (report.get("email") if "report" in locals() else "")
                        ),
                        "reason": str(exc),
                    }
                )
                continue

        status = (
            "SUCCESS"
            if not failures
            else ("PARTIAL_FAILURE" if recipients else "FAILURE")
        )
        return {
            "status": status,
            "processed_records": len(parsed),
            "recipients": recipients,
            "failures": failures,
        }

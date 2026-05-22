"""
Unit tests for the PDF/Mail SQS consumer Lambda.
"""

from unittest.mock import MagicMock, patch

import pytest

from lambdas.pdf_mail_consumer.handler import lambda_handler
from lambdas.pdf_mail_consumer.orchestrator import PdfMailConsumerOrchestrator
from lambdas.pdf_mail_consumer.report_renderer import build_html_report, build_pdf_report


@patch("lambdas.pdf_mail_consumer.handler.PdfMailConsumerOrchestrator")
def test_lambda_handler_processes_sqs_records(mock_orchestrator_class, caplog):
    mock_orchestrator = MagicMock()
    mock_orchestrator.process_records.return_value = {"status": "SUCCESS", "processed_records": 1}
    mock_orchestrator_class.return_value = mock_orchestrator

    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": '{"db_item_id": "item-1", "email": "user@example.com"}',
                "messageAttributes": {
                    "Type": {
                        "stringValue": "ReportGeneration",
                        "dataType": "String",
                    }
                },
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-pdf-mail-queue-dev",
            }
        ]
    }

    with caplog.at_level("INFO"):
        result = lambda_handler(event, None)

    assert result == {"status": "SUCCESS", "processed_records": 1}
    mock_orchestrator.process_records.assert_called_once()
    assert "pdf-mail-consumer finished" in caplog.text


def test_lambda_handler_without_records_returns_summary(caplog):
    with caplog.at_level("INFO"):
        result = lambda_handler({"foo": "bar"}, None)

    assert result == {"status": "NO_RECORDS", "processed_records": 0}
    assert "pdf-mail-consumer invoked without SQS records" in caplog.text


def test_build_html_report_includes_download_link():
    report = {
        "execution_id": "exec-1",
        "email": "user@example.com",
        "prompt": "Explain the architecture",
        "image": "s3://bucket/input.png",
        "result": {"technical_analysis": {"findings": ["ok"]}},
    }

    html = build_html_report(report, "https://signed-url")

    assert "https://signed-url" in html
    assert "exec-1" in html
    assert "technical_analysis" in html


def test_build_pdf_report_returns_pdf_bytes():
    report = {
        "execution_id": "exec-1",
        "email": "user@example.com",
        "prompt": "Explain the architecture",
        "image": "s3://bucket/input.png",
        "result": {"technical_analysis": {"findings": ["ok"]}},
    }

    pdf_bytes = build_pdf_report(report)

    assert pdf_bytes.startswith(b"%PDF-")


def test_orchestrator_process_records_sends_report():
    repository = MagicMock()
    repository.get_report.return_value = {
        "execution_id": "exec-1",
        "email": "user@example.com",
        "prompt": "Explain the architecture",
        "image": "s3://bucket/input.png",
        "result": {"technical_analysis": {"findings": ["ok"]}},
    }

    storage = MagicMock()
    storage.upload_pdf.return_value = "reports/exec-1/analysis-report.pdf"
    storage.create_download_url.return_value = "https://signed-url"

    mailer = MagicMock()
    mailer.send_report_email.return_value = "ses-message-1"

    orchestrator = PdfMailConsumerOrchestrator(
        repository=repository,
        storage=storage,
        mailer=mailer,
        region="us-east-1",
    )

    event = [
        {
            "messageId": "msg-1",
            "body": '{"db_item_id": "exec-1", "email": "user@example.com"}',
            "messageAttributes": {},
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-pdf-mail-queue-dev",
        }
    ]

    result = orchestrator.process_records(event)

    assert result == {"status": "SUCCESS", "processed_records": 1}
    repository.get_report.assert_called_once_with("exec-1")
    storage.upload_pdf.assert_called_once()
    storage.create_download_url.assert_called_once_with("reports/exec-1/analysis-report.pdf")
    mailer.send_report_email.assert_called_once()
    sent_kwargs = mailer.send_report_email.call_args.kwargs
    assert sent_kwargs["recipient_email"] == "user@example.com"
    assert sent_kwargs["subject"] == "Architecture analysis report - exec-1"
    assert "https://signed-url" in sent_kwargs["html_body"]


def test_orchestrator_requires_db_item_id():
    orchestrator = PdfMailConsumerOrchestrator(
        repository=MagicMock(),
        storage=MagicMock(),
        mailer=MagicMock(),
        region="us-east-1",
    )

    with pytest.raises(ValueError, match="db_item_id field is required"):
        orchestrator.process_records(
            [
                {
                    "messageId": "msg-1",
                    "body": '{"email": "user@example.com"}',
                    "messageAttributes": {},
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:auto-arch-analyzer-pdf-mail-queue-dev",
                }
            ]
        )
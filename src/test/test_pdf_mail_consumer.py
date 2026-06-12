"""
Unit tests for the PDF/Mail SQS consumer Lambda.
"""

import base64
from unittest.mock import MagicMock, patch

from lambdas.pdf_mail_consumer.handler import lambda_handler
from lambdas.pdf_mail_consumer.orchestrator import PdfMailConsumerOrchestrator
from lambdas.pdf_mail_consumer.report_renderer import (
    build_html_report,
    build_pdf_report,
)


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5Y7f8AAAAASUVORK5CYII="
)


@patch("lambdas.pdf_mail_consumer.handler.PdfMailConsumerOrchestrator")
def test_lambda_handler_processes_sqs_records(mock_orchestrator_class, caplog):
    mock_orchestrator = MagicMock()
    mock_orchestrator.process_records.return_value = {
        "status": "SUCCESS",
        "processed_records": 1,
    }
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


@patch("lambdas.pdf_mail_consumer.report_renderer.boto3.client")
def test_build_html_report_includes_download_link(mock_s3_client_factory):
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://image-signed-url"
    mock_s3_client_factory.return_value = mock_s3_client

    report = {
        "PK": {"S": "123e4567-e89b-12d3-a456-426614174000"},
        "SK": {"S": "REPORT"},
        "email": {"S": "voce@exemplo.com"},
        "execution_id": {"S": "123e4567-e89b-12d3-a456-426614174000"},
        "image": {
            "S": "s3://auto-arch-analyzer-diagram-upload-dev/voce/e7c255a9-diagram.png"
        },
        "prompt": {"S": "Analise a arquitetura"},
        "result": {
            "M": {
                "analysis_date": {"S": "2024-05-21T14:30:00Z"},
                "processing_status": {"S": "ANALYZED"},
                "s3_bucket": {"S": "auto-arch-analyzer-diagram-upload-dev"},
                "s3_key": {"S": "voce/e7c255a9-diagram.png"},
                "technical_analysis": {
                    "M": {
                        "architecture_findings": {
                            "L": [
                                {
                                    "M": {
                                        "criticality": {"S": "High"},
                                        "description": {
                                            "S": "O bucket S3 de armazenamento de imagens não possui bloqueio de acesso público habilitado."
                                        },
                                        "type": {"S": "Security"},
                                    }
                                },
                                {
                                    "M": {
                                        "criticality": {"S": "Medium"},
                                        "description": {
                                            "S": "O DynamoDB está configurado com capacidade provisionada fixa. Recomenda-se mudar para sob demanda (on-demand) para melhor lidar com picos de tráfego."
                                        },
                                        "type": {"S": "Scalability"},
                                    }
                                },
                            ]
                        },
                        "architecture_summary": {
                            "M": {
                                "architectural_style": {"S": "Serverless"},
                                "cloud_provider": {"S": "AWS"},
                                "description": {
                                    "S": "Uma aplicação web moderna utilizando backend serverless e banco de dados NoSQL gerenciado."
                                },
                            }
                        },
                        "service_inventory": {
                            "L": [
                                {
                                    "M": {
                                        "category": {"S": "Networking"},
                                        "name": {"S": "Amazon API Gateway"},
                                        "quantity": {"N": "1"},
                                    }
                                },
                                {
                                    "M": {
                                        "category": {"S": "Compute"},
                                        "name": {"S": "AWS Lambda"},
                                        "quantity": {"N": "3"},
                                    }
                                },
                            ]
                        },
                    }
                },
            }
        },
    }

    html = build_html_report(report, "https://signed-url")

    assert "https://signed-url" in html
    assert "voce@exemplo.com" in html
    assert "Analise a arquitetura" in html
    assert (
        "s3://auto-arch-analyzer-diagram-upload-dev/voce/e7c255a9-diagram.png" in html
    )
    assert "https://image-signed-url" in html
    assert "Analysis Date" not in html
    assert "Processing Status" not in html
    assert "S3 Bucket" not in html
    assert "S3 Key" not in html
    assert "Technical Analysis" in html
    assert "Architecture Findings" in html
    assert "High" in html
    assert "Amazon API Gateway" in html
    assert "Serverless" in html
    assert '<img src="https://image-signed-url"' in html
    assert "<pre>" not in html


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
    pdf_text = pdf_bytes.decode("latin-1")
    # PDF must contain only the Technical Analysis content
    assert "Technical Analysis" in pdf_text
    assert "ok" in pdf_text
    # removed metadata fields
    assert "Email" not in pdf_text
    assert "Prompt" not in pdf_text
    assert "s3://bucket/input.png" not in pdf_text


@patch("lambdas.pdf_mail_consumer.report_renderer.boto3.client")
def test_orchestrator_process_records_sends_report(mock_s3_client_factory):
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://image-signed-url"
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=PNG_BYTES))
    }
    mock_s3_client_factory.return_value = mock_s3_client

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

    assert result.get("status") == "SUCCESS"
    assert result.get("processed_records") == 1
    assert "user@example.com" in result.get("recipients", [])
    repository.get_report.assert_called_once_with("exec-1")
    storage.upload_pdf.assert_called_once()
    storage.create_download_url.assert_called_once_with(
        "reports/exec-1/analysis-report.pdf"
    )
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

    result = orchestrator.process_records(
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

    # Validate that the missing db_item_id is properly handled
    assert result["status"] == "FAILURE"
    assert result["processed_records"] == 1
    assert result["recipients"] == []
    assert len(result["failures"]) == 1
    assert result["failures"][0]["reason"] == "missing_db_item_id"
    assert result["failures"][0]["record_index"] == "0"

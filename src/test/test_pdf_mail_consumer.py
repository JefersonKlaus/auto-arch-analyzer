"""
Unit tests for the PDF/Mail SQS consumer Lambda.
"""

from lambdas.pdf_mail_consumer.handler import lambda_handler


def test_lambda_handler_processes_sqs_records(caplog):
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
    assert "pdf-mail-consumer record processed" in caplog.text
    assert "pdf-mail-consumer finished" in caplog.text


def test_lambda_handler_without_records_returns_summary(caplog):
    with caplog.at_level("INFO"):
        result = lambda_handler({"foo": "bar"}, None)

    assert result == {"status": "NO_RECORDS", "processed_records": 0}
    assert "pdf-mail-consumer invoked without SQS records" in caplog.text
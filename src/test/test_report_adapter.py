"""
Unit tests for report_adapter components.

Run with: python -m pytest src/test/test_report_adapter.py
"""

from unittest.mock import patch, MagicMock

import pytest

from lambdas.report_adapter.models import ReportAdapterRequest, ReportAdapterResult
from lambdas.report_adapter.request_parser import RequestParser
from lambdas.report_adapter.dynamodb_repository import DynamoDBRepository
from lambdas.report_adapter.sqs_publisher import SQSPublisher
from lambdas.report_adapter.orchestrator import ReportAdapterOrchestrator
from lambdas.report_adapter import handler as handler_module


class TestReportAdapterRequest:
    def test_valid_request(self):
        req = ReportAdapterRequest(
            email="user@example.com",
            s3_file_path="s3://bucket/key",
            ai_analysis={"findings": []},
            prompt="Please analyze",
        )

        assert req.email == "user@example.com"
        assert req.s3_file_path == "s3://bucket/key"
        assert req.ai_analysis == {"findings": []}

    def test_missing_email_raises(self):
        with pytest.raises(ValueError, match="email field is required"):
            ReportAdapterRequest(email=None, s3_file_path="s3://x", ai_analysis={})

    def test_missing_s3_path_raises(self):
        with pytest.raises(ValueError, match="s3_file_path field is required"):
            ReportAdapterRequest(email="a@b.com", s3_file_path=None, ai_analysis={})


class TestRequestParser:
    def test_parse_direct_event(self):
        event = {
            "email": "u@e.com",
            "s3_file_path": "s3://bucket/file",
            "ai_analysis": {"findings": []},
        }
        req = RequestParser.parse_event(event)
        assert req.email == "u@e.com"
        assert req.s3_file_path == "s3://bucket/file"

    def test_missing_fields_raises(self):
        event = {"email": "u@e.com"}
        with pytest.raises(ValueError):
            RequestParser.parse_event(event)


class TestDynamoDBRepository:
    @patch("lambdas.report_adapter.dynamodb_repository.boto3.resource")
    def test_save_report_success(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_table.put_item.return_value = {}
        mock_boto3_resource.return_value.Table.return_value = mock_table

        repo = DynamoDBRepository("test-table")

        class DummyReq:
            email = "u@e.com"
            prompt = "p"
            s3_file_path = "s3://b/k"
            ai_analysis = {"a": 1}

        item_id = repo.save_report(DummyReq(), "item-1")
        assert item_id == "item-1"
        mock_table.put_item.assert_called_once()

    @patch("lambdas.report_adapter.dynamodb_repository.boto3.resource")
    def test_save_report_failure_raises(self, mock_boto3_resource):
        from botocore.exceptions import ClientError

        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {"Error": {"Message": "err", "Code": "500"}}, "PutItem"
        )
        mock_boto3_resource.return_value.Table.return_value = mock_table

        repo = DynamoDBRepository("t")

        class DummyReq:
            email = "u@e.com"
            prompt = "p"
            s3_file_path = "s3://b/k"
            ai_analysis = {}

        with pytest.raises(RuntimeError, match="Failed to persist item to DynamoDB"):
            repo.save_report(DummyReq(), "id")


class TestSQSPublisher:
    @patch("lambdas.report_adapter.sqs_publisher.boto3.client")
    def test_publish_success(self, mock_boto3_client):
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "m-1"}
        mock_boto3_client.return_value = mock_sqs

        publisher = SQSPublisher("https://sqs/url")
        msg_id = publisher.publish_report_notification("id-1", "u@e.com")
        assert msg_id == "m-1"
        mock_sqs.send_message.assert_called_once()

    @patch("lambdas.report_adapter.sqs_publisher.boto3.client")
    def test_publish_failure_raises(self, mock_boto3_client):
        from botocore.exceptions import ClientError

        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Message": "err", "Code": "500"}}, "SendMessage"
        )
        mock_boto3_client.return_value = mock_sqs

        publisher = SQSPublisher("https://sqs/url")
        with pytest.raises(RuntimeError, match="Failed to send message to SQS"):
            publisher.publish_report_notification("id-1", "u@e.com")


class TestReportAdapterOrchestrator:
    def test_process_success(self):
        repo = MagicMock()
        publisher = MagicMock()
        publisher.publish_report_notification.return_value = "msg-1"

        orchestrator = ReportAdapterOrchestrator(repository=repo, publisher=publisher)

        event = {
            "email": "u@e.com",
            "s3_file_path": "s3://b/k",
            "ai_analysis": {"findings": []},
        }

        result = orchestrator.process(event)

        assert result.status == "SUCCESS"
        assert result.db_item_id
        assert result.sqs_message_id == "msg-1"
        repo.save_report.assert_called_once()
        publisher.publish_report_notification.assert_called_once()


class TestHandler:
    @patch("lambdas.report_adapter.handler.ReportAdapterOrchestrator")
    def test_lambda_handler_success(self, mock_orch_class, monkeypatch):
        # Setup env
        monkeypatch.setenv("DYNAMODB_TABLE_NAME", "tbl")
        monkeypatch.setenv("SQS_PDF_MAIL_QUEUE_URL", "https://sqs/url")

        mock_orch = MagicMock()
        mock_result = ReportAdapterResult(
            status="SUCCESS", db_item_id="id", sqs_message_id="msg"
        )
        mock_orch.process.return_value = mock_result
        mock_orch_class.return_value = mock_orch

        event = {
            "email": "u@e.com",
            "s3_file_path": "s3://b/k",
            "ai_analysis": {"findings": []},
        }

        res = handler_module.lambda_handler(event, None)
        assert res["status"] == "SUCCESS"
        assert res["db_item_id"] == "id"
        assert res["sqs_message_id"] == "msg"

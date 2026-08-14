"""
Unit tests for report_adapter components.

Run with: python -m pytest src/test/test_report_adapter.py
"""

from unittest.mock import MagicMock, patch

import pytest

from lambdas.report_adapter import handler as handler_module
from lambdas.report_adapter.dynamodb_repository import DynamoDBRepository
from lambdas.report_adapter.models import ReportAdapterRequest, ReportAdapterResult
from lambdas.report_adapter.orchestrator import ReportAdapterOrchestrator
from lambdas.report_adapter.request_parser import RequestParser
from lambdas.report_adapter.sqs_publisher import SQSPublisher


class TestReportAdapterRequest:
    def test_valid_request(self):
        req = ReportAdapterRequest(
            execution_id="123e4567-e89b-12d3-a456-426614174000",
            email="user@example.com",
            s3_file_path="s3://bucket/key",
            prompt="Please analyze",
            raw_payload={"technical_analysis": {"findings": []}},
        )

        assert req.execution_id == "123e4567-e89b-12d3-a456-426614174000"
        assert req.email == "user@example.com"
        assert req.s3_file_path == "s3://bucket/key"

    def test_missing_email_raises(self):
        with pytest.raises(ValueError, match="email field is required"):
            ReportAdapterRequest(
                execution_id="id",
                email=None,
                s3_file_path="s3://x",
                raw_payload={},
            )

    def test_missing_s3_path_raises(self):
        with pytest.raises(ValueError, match="s3_file_path field is required"):
            ReportAdapterRequest(
                execution_id="id",
                email="a@b.com",
                s3_file_path=None,
                raw_payload={},
            )


class TestRequestParser:
    def test_parse_direct_event(self):
        event = {
            "execution_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "u@e.com",
            "s3_file_path": "s3://bucket/file",
            "technical_analysis": {"findings": []},
        }
        req = RequestParser.parse_event(event)
        assert req.execution_id == "123e4567-e89b-12d3-a456-426614174000"
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
            def __init__(self):
                self.execution_id = "123e4567-e89b-12d3-a456-426614174000"
                self.email = "u@e.com"
                self.prompt = "p"
                self.s3_file_path = "s3://b/k"
                self.raw_payload = {
                    "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "u@e.com",
                    "prompt": "p",
                    "s3_file_path": "s3://b/k",
                    "technical_analysis": {"a": 1},
                }

        item_id = repo.save_report(DummyReq())
        assert item_id == "123e4567-e89b-12d3-a456-426614174000"
        mock_table.put_item.assert_called_once_with(
            Item={
                "PK": "123e4567-e89b-12d3-a456-426614174000",
                "SK": "REPORT",
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "u@e.com",
                "prompt": "p",
                "image": "s3://b/k",
                "result": {"technical_analysis": {"a": 1}},
            }
        )

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
            def __init__(self):
                self.execution_id = "id"
                self.email = "u@e.com"
                self.prompt = "p"
                self.s3_file_path = "s3://b/k"
                self.raw_payload = {}

        with pytest.raises(RuntimeError, match="Failed to persist item to DynamoDB"):
            repo.save_report(DummyReq())

    @patch("lambdas.report_adapter.dynamodb_repository.boto3.resource")
    def test_update_sqs_message_id_success(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_table.update_item.return_value = {}
        mock_boto3_resource.return_value.Table.return_value = mock_table

        repo = DynamoDBRepository("test-table")

        repo.update_sqs_message_id(
            execution_id="123e4567-e89b-12d3-a456-426614174000",
            sqs_message_id="msg-1",
        )

        mock_table.update_item.assert_called_once_with(
            Key={"PK": "123e4567-e89b-12d3-a456-426614174000", "SK": "REPORT"},
            UpdateExpression="SET sqs_message_id = :sqs_message_id",
            ExpressionAttributeValues={":sqs_message_id": "msg-1"},
        )

    @patch("lambdas.report_adapter.dynamodb_repository.boto3.resource")
    def test_update_sqs_message_id_failure_raises(self, mock_boto3_resource):
        from botocore.exceptions import ClientError

        mock_table = MagicMock()
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Message": "err", "Code": "500"}}, "UpdateItem"
        )
        mock_boto3_resource.return_value.Table.return_value = mock_table

        repo = DynamoDBRepository("test-table")

        with pytest.raises(
            RuntimeError, match="Failed to update SQS message id in DynamoDB"
        ):
            repo.update_sqs_message_id("id", "msg-1")


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
            "execution_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "u@e.com",
            "s3_file_path": "s3://b/k",
            "technical_analysis": {"findings": []},
        }

        result = orchestrator.process(event)

        assert result.status == "SUCCESS"
        assert result.db_item_id
        assert result.sqs_message_id == "msg-1"
        repo.save_report.assert_called_once()
        repo.update_sqs_message_id.assert_called_once_with(
            execution_id=repo.save_report.return_value,
            sqs_message_id="msg-1",
        )
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

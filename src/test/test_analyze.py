"""
Unit tests for analyze handler components.

These tests demonstrate how each component can be tested in isolation.
Run with: python -m pytest src/test/test_analyze.py
"""

import json
import base64
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Make handler modules importable when running tests from src/test.
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "api" / "post" / "diagram-analyze")
)

from models import AnalyzeRequest
from request_parser import RequestParser
from s3_uploader import S3DiagramUploader
from sqs_publisher import SQSPublisher
from orchestrator import AnalyzeOrchestrator


class TestAnalyzeRequest:
    """Tests for AnalyzeRequest model."""

    def test_valid_request_with_all_fields(self):
        """Test creating a valid request with all fields."""
        req = AnalyzeRequest(
            diagram="base64data", email="test@example.com", prompt="Analyze this"
        )
        assert req.diagram == "base64data"
        assert req.email == "test@example.com"
        assert req.prompt == "Analyze this"

    def test_valid_request_only_required_fields(self):
        """Test creating a valid request with only required fields."""
        req = AnalyzeRequest(diagram="base64data", email="test@example.com")
        assert req.diagram == "base64data"
        assert req.email == "test@example.com"
        assert req.prompt is None

    def test_missing_required_diagram(self):
        """Test that missing diagram raises error."""
        with pytest.raises(ValueError, match="diagram field is required"):
            AnalyzeRequest(diagram=None, email="test@example.com")

    def test_empty_diagram(self):
        """Test that empty diagram raises error."""
        with pytest.raises(ValueError, match="diagram must be a non-empty string"):
            AnalyzeRequest(diagram="", email="test@example.com")

    def test_invalid_email_type(self):
        """Test that invalid email type raises error."""
        with pytest.raises(ValueError, match="email must be a non-empty string"):
            AnalyzeRequest(diagram="base64", email=123)

    def test_missing_required_email(self):
        """Test that missing email raises error."""
        with pytest.raises(ValueError, match="email field is required"):
            AnalyzeRequest(diagram="base64", email=None)


class TestRequestParser:
    """Tests for RequestParser."""

    def test_parse_direct_json_event(self):
        """Test parsing direct JSON event."""
        event = {
            "diagram": "base64data",
            "email": "test@example.com",
            "prompt": "Analyze",
        }
        req = RequestParser.parse_event(event)
        assert req.diagram == "base64data"
        assert req.email == "test@example.com"

    def test_parse_api_gateway_event(self):
        """Test parsing API Gateway wrapped event."""
        event = {
            "body": json.dumps({"diagram": "base64data", "email": "test@example.com"})
        }
        req = RequestParser.parse_event(event)
        assert req.diagram == "base64data"
        assert req.email == "test@example.com"

    def test_missing_required_field(self):
        """Test parsing event without required field."""
        event = {"diagram": "base64data"}
        with pytest.raises(ValueError):
            RequestParser.parse_event(event)

    def test_invalid_json_in_body(self):
        """Test parsing event with invalid JSON."""
        event = {"body": "invalid json"}
        with pytest.raises(json.JSONDecodeError):
            RequestParser.parse_event(event)


class TestS3DiagramUploader:
    """Tests for S3DiagramUploader."""

    @patch("s3_uploader.boto3.client")
    def test_upload_diagram_success(self, mock_boto3_client):
        """Test successful diagram upload."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        uploader = S3DiagramUploader("test-bucket")

        # Test
        # Create valid base64
        test_image = b"test image data"
        base64_image = base64.b64encode(test_image).decode()

        s3_key = uploader.upload_diagram(base64_image, "test@example.com")

        # Verify
        assert s3_key.startswith("test/")
        assert s3_key.endswith("-diagram.png")
        mock_s3.put_object.assert_called_once()

    @patch("s3_uploader.boto3.client")
    def test_upload_invalid_base64(self, mock_boto3_client):
        """Test upload with invalid base64."""
        uploader = S3DiagramUploader("test-bucket")
        with pytest.raises(ValueError, match="Invalid base64"):
            uploader.upload_diagram("not valid base64!!!", "test@example.com")

    @patch("s3_uploader.boto3.client")
    def test_upload_s3_failure(self, mock_boto3_client):
        """Test handling S3 upload failure."""
        # Setup
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("S3 error")
        mock_boto3_client.return_value = mock_s3
        uploader = S3DiagramUploader("test-bucket")

        # Test
        test_image = b"test image"
        base64_image = base64.b64encode(test_image).decode()

        with pytest.raises(Exception, match="Failed to upload"):
            uploader.upload_diagram(base64_image)


class TestSQSPublisher:
    """Tests for SQSPublisher."""

    @patch("sqs_publisher.boto3.client")
    def test_publish_success(self, mock_boto3_client):
        """Test successful message publication."""
        # Setup
        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        mock_boto3_client.return_value = mock_sqs

        publisher = SQSPublisher("https://sqs.region.amazonaws.com/queue")

        # Test
        msg_id = publisher.publish_diagram_metadata(
            "path/to/diagram.png",
            "test-bucket",
            "test@example.com",
            "Analyze for security",
        )

        # Verify
        assert msg_id == "msg-123"
        mock_sqs.send_message.assert_called_once()

        # Check message content
        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["s3_key"] == "path/to/diagram.png"
        assert message_body["email"] == "test@example.com"

    @patch("sqs_publisher.boto3.client")
    def test_publish_sqs_failure(self, mock_boto3_client):
        """Test handling SQS publish failure."""
        # Setup
        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = Exception("SQS error")
        mock_boto3_client.return_value = mock_sqs

        publisher = SQSPublisher("https://sqs.region.amazonaws.com/queue")

        with pytest.raises(Exception, match="Failed to publish"):
            publisher.publish_diagram_metadata("key", "bucket")


class TestAnalyzeOrchestrator:
    """Tests for AnalyzeOrchestrator."""

    @patch("orchestrator.S3DiagramUploader")
    @patch("orchestrator.SQSPublisher")
    def test_process_analyze_request_success(self, mock_sqs_class, mock_s3_class):
        """Test successful end-to-end processing."""
        # Setup
        mock_s3 = MagicMock()
        mock_s3.upload_diagram.return_value = "email/123-diagram.png"
        mock_s3_class.return_value = mock_s3

        mock_sqs = MagicMock()
        mock_sqs.publish_diagram_metadata.return_value = "msg-456"
        mock_sqs_class.return_value = mock_sqs

        orchestrator = AnalyzeOrchestrator("bucket", "queue-url")

        # Test
        event = {
            "diagram": base64.b64encode(b"test").decode(),
            "email": "test@example.com",
            "prompt": "Analyze",
        }
        result = orchestrator.process_analyze_request(event)

        # Verify
        assert result["s3_key"] == "email/123-diagram.png"
        assert result["message_id"] == "msg-456"
        assert result["email"] == "test@example.com"
        mock_s3.upload_diagram.assert_called_once()
        mock_sqs.publish_diagram_metadata.assert_called_once()


# Integration test example
@patch("orchestrator.S3DiagramUploader")
@patch("orchestrator.SQSPublisher")
def test_analyze_handler_integration(mock_sqs_class, mock_s3_class):
    """Integration test of complete handler flow."""
    # This would test the full flow from handler to response
    pass

"""
Unit tests for file_validator Lambda components.

These tests demonstrate how each component can be tested in isolation.
Run with: python -m pytest src/test/test_file_validator.py
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from lambdas.file_validator.errors import FILE_NOT_FOUND, INVALID_FORMAT
from lambdas.file_validator.handler import lambda_handler
from lambdas.file_validator.models import FileValidationRequest
from lambdas.file_validator.orchestrator import FileValidatorOrchestrator
from lambdas.file_validator.request_parser import RequestParser
from lambdas.file_validator.s3_validator import MAX_FILE_SIZE_BYTES, S3FileValidator


class TestFileValidationRequest:
    """Tests for FileValidationRequest model."""

    def test_valid_request_with_all_fields(self):
        """Test creating a valid request with all fields."""
        req = FileValidationRequest(
            s3_file_path="s3://bucket/diagram.png",
            email="test@example.com",
            prompt="Analyze this",
        )
        assert req.s3_file_path == "s3://bucket/diagram.png"
        assert req.email == "test@example.com"
        assert req.prompt == "Analyze this"

    def test_valid_request_only_required_fields(self):
        """Test creating a valid request with only required fields."""
        req = FileValidationRequest(s3_file_path="s3://bucket/diagram.png")
        assert req.s3_file_path == "s3://bucket/diagram.png"
        assert req.email is None
        assert req.prompt is None

    def test_missing_s3_file_path_raises_error(self):
        """Test that missing s3_file_path raises ValueError."""
        with pytest.raises(ValueError, match="s3_file_path field is required"):
            FileValidationRequest(s3_file_path=None)

    def test_empty_s3_file_path_raises_error(self):
        """Test that empty s3_file_path raises ValueError."""
        with pytest.raises(ValueError, match="s3_file_path must be a non-empty string"):
            FileValidationRequest(s3_file_path="")

    def test_invalid_email_type_raises_error(self):
        """Test that invalid email type raises ValueError."""
        with pytest.raises(ValueError, match="email must be a string"):
            FileValidationRequest(s3_file_path="s3://bucket/diagram.png", email=123)

    def test_invalid_prompt_type_raises_error(self):
        """Test that invalid prompt type raises ValueError."""
        with pytest.raises(ValueError, match="prompt must be a string"):
            FileValidationRequest(
                s3_file_path="s3://bucket/diagram.png", prompt={"not": "string"}
            )


class TestRequestParser:
    """Tests for RequestParser."""

    def test_parse_direct_invocation_event(self):
        """Test parsing a direct Lambda invocation event."""
        direct_event = {
            "s3_file_path": "s3://bucket/file.png",
            "email": "test@example.com",
            "prompt": "Analyze",
        }
        payload = RequestParser.parse_event(direct_event)
        assert payload["s3_file_path"] == "s3://bucket/file.png"
        assert payload["email"] == "test@example.com"

    def test_parse_direct_invocation_event_with_bucket_and_key(self):
        """Test parsing a direct Lambda invocation event with bucket/key input."""
        direct_event = {
            "s3_bucket": "auto-arch-analyzer-diagram-upload-dev",
            "s3_key": "voce/73e05b72-diagram.png",
            "email": "voce@exemplo.com",
            "prompt": "Analise a arquitetura",
        }

        payload = RequestParser.parse_event(direct_event)

        assert payload["s3_file_path"] == (
            "s3://auto-arch-analyzer-diagram-upload-dev/voce/73e05b72-diagram.png"
        )
        assert payload["s3_bucket"] == "auto-arch-analyzer-diagram-upload-dev"
        assert payload["s3_key"] == "voce/73e05b72-diagram.png"
        assert payload["email"] == "voce@exemplo.com"
        assert payload["prompt"] == "Analise a arquitetura"

    def test_parse_api_gateway_event(self):
        """Test parsing an API Gateway event."""
        api_gw_event = {
            "body": json.dumps(
                {"s3_file_path": "s3://bucket/file.png", "email": "test@example.com"}
            )
        }
        payload = RequestParser.parse_event(api_gw_event)
        assert payload["s3_file_path"] == "s3://bucket/file.png"

    def test_parse_api_gateway_event_body_as_dict(self):
        """Test parsing API Gateway event when body is already a dict."""
        event = {"body": {"s3_file_path": "s3://bucket/file.png"}}
        payload = RequestParser.parse_event(event)
        assert payload["s3_file_path"] == "s3://bucket/file.png"

    def test_unsupported_event_format_raises_value_error(self):
        """Test that an unsupported event format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid event: expected object"):
            RequestParser.parse_event(["not", "a", "dict"])

    def test_invalid_body_type_raises_value_error(self):
        """Test that body with unsupported type raises ValueError."""
        with pytest.raises(
            ValueError, match="Invalid event body: expected object or JSON string"
        ):
            RequestParser.parse_event({"body": 123})

    def test_invalid_json_body_raises_json_decode_error(self):
        """Test that invalid JSON body raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            RequestParser.parse_event({"body": "{invalid-json"})

    def test_to_request_invalid_payload_raises_value_error(self):
        """Test that to_request wraps model validation errors."""
        with pytest.raises(ValueError, match="Invalid request"):
            RequestParser.to_request({"email": "test@example.com"})


class TestS3FileValidator:
    """Tests for S3FileValidator."""

    @patch("lambdas.file_validator.s3_validator.boto3.client")
    def test_validate_file_success(self, mock_boto3_client):
        """Test successful file validation."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "image/png",
        }
        mock_boto3_client.return_value = mock_s3

        validator = S3FileValidator(region="us-east-1")
        validator.validate_file("s3://bucket/diagram.png")

        mock_s3.head_object.assert_called_once_with(Bucket="bucket", Key="diagram.png")

    @patch("lambdas.file_validator.s3_validator.boto3.client")
    def test_validate_file_not_found_raises_file_not_found(self, mock_boto3_client):
        """Test that missing S3 object raises FILE_NOT_FOUND."""
        mock_s3 = MagicMock()
        mock_s3.head_object.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            operation_name="HeadObject",
        )
        mock_boto3_client.return_value = mock_s3

        validator = S3FileValidator()

        with pytest.raises(FILE_NOT_FOUND, match="File not found in S3"):
            validator.validate_file("s3://bucket/missing.png")

    @patch("lambdas.file_validator.s3_validator.boto3.client")
    def test_validate_file_size_limit_raises_invalid_format(self, mock_boto3_client):
        """Test that oversized files raise INVALID_FORMAT."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {
            "ContentLength": MAX_FILE_SIZE_BYTES + 1,
            "ContentType": "image/png",
        }
        mock_boto3_client.return_value = mock_s3

        validator = S3FileValidator()

        with pytest.raises(INVALID_FORMAT, match="exceeds 5MB limit"):
            validator.validate_file("s3://bucket/diagram.png")

    @patch("lambdas.file_validator.s3_validator.boto3.client")
    def test_validate_file_unsupported_format_raises_invalid_format(
        self, mock_boto3_client
    ):
        """Test that unsupported file formats raise INVALID_FORMAT."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "application/pdf",
        }
        mock_boto3_client.return_value = mock_s3

        validator = S3FileValidator()

        with pytest.raises(INVALID_FORMAT, match="Unsupported file format"):
            validator.validate_file("s3://bucket/diagram.pdf")

    @patch("lambdas.file_validator.s3_validator.boto3.client")
    def test_validate_file_invalid_s3_uri_raises_invalid_format(
        self, mock_boto3_client
    ):
        """Test that malformed S3 URI raises INVALID_FORMAT."""
        mock_boto3_client.return_value = MagicMock()
        validator = S3FileValidator()

        with pytest.raises(
            INVALID_FORMAT,
            match="Invalid s3_file_path. Expected format: s3://bucket/key",
        ):
            validator.validate_file("https://bucket/key")


class TestFileValidatorOrchestrator:
    """Tests for FileValidatorOrchestrator."""

    @patch("lambdas.file_validator.orchestrator.S3FileValidator")
    def test_process_validation_success(
        self,
        mock_s3_validator_class,
    ):
        """Test successful end-to-end validation orchestration."""
        payload = {
            "s3_bucket": "auto-arch-analyzer-diagram-upload-dev",
            "s3_key": "voce/73e05b72-diagram.png",
            "email": "voce@exemplo.com",
            "prompt": "Analise a arquitetura",
        }

        mock_s3_validator = MagicMock()
        mock_s3_validator_class.return_value = mock_s3_validator

        orchestrator = FileValidatorOrchestrator(region="us-east-1")
        result = orchestrator.process_validation(payload)

        assert result["s3_file_path"] == (
            "s3://auto-arch-analyzer-diagram-upload-dev/voce/73e05b72-diagram.png"
        )
        assert result["s3_bucket"] == "auto-arch-analyzer-diagram-upload-dev"
        assert result["s3_key"] == "voce/73e05b72-diagram.png"
        mock_s3_validator.validate_file.assert_called_once_with(
            "s3://auto-arch-analyzer-diagram-upload-dev/voce/73e05b72-diagram.png"
        )
        assert result["email"] == "voce@exemplo.com"
        assert result["prompt"] == "Analise a arquitetura"

    def test_process_validation_error(self):
        """Test that validation errors from RequestParser are propagated."""
        with patch(
            "lambdas.file_validator.orchestrator.RequestParser.parse_event",
            side_effect=ValueError("Invalid event"),
        ):
            orchestrator = FileValidatorOrchestrator()
            with pytest.raises(ValueError, match="Invalid event"):
                orchestrator.process_validation({"body": 123})


class TestLambdaHandler:
    """Tests for Lambda handler."""

    @patch.dict(
        "lambdas.file_validator.handler.os.environ",
        {"AWS_REGION": "us-west-2"},
        clear=False,
    )
    @patch("lambdas.file_validator.handler.FileValidatorOrchestrator")
    def test_handler_success(self, mock_orchestrator_class):
        """Test successful handler execution."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_validation.return_value = {
            "s3_file_path": "s3://bucket/file.png",
            "email": "test@example.com",
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        event = {"s3_file_path": "s3://bucket/file.png", "email": "test@example.com"}
        result = lambda_handler(event, None)

        mock_orchestrator_class.assert_called_once_with("us-west-2")
        mock_orchestrator.process_validation.assert_called_once_with(event)
        assert result["s3_file_path"] == "s3://bucket/file.png"

    @patch("lambdas.file_validator.handler.FileValidatorOrchestrator")
    def test_handler_file_not_found_is_propagated(self, mock_orchestrator_class):
        """Test that FILE_NOT_FOUND is re-raised by handler."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_validation.side_effect = FILE_NOT_FOUND("missing")
        mock_orchestrator_class.return_value = mock_orchestrator

        with pytest.raises(FILE_NOT_FOUND, match="missing"):
            lambda_handler({"s3_file_path": "s3://bucket/missing.png"}, None)

    @patch("lambdas.file_validator.handler.FileValidatorOrchestrator")
    def test_handler_invalid_format_is_propagated(self, mock_orchestrator_class):
        """Test that INVALID_FORMAT is re-raised by handler."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_validation.side_effect = INVALID_FORMAT("bad-format")
        mock_orchestrator_class.return_value = mock_orchestrator

        with pytest.raises(INVALID_FORMAT, match="bad-format"):
            lambda_handler({"s3_file_path": "s3://bucket/file.pdf"}, None)

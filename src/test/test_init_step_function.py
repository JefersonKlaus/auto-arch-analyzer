"""
Unit tests for init_step_function Lambda components.

These tests demonstrate how each component can be tested in isolation.
Run with: python -m pytest src/test/test_init_step_function.py
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from models import InitRequest
from request_parser import RequestParser
from stepfunction_service import StepFunctionTriggerService
from orchestrator import InitOrchestrator


class TestInitRequest:
    """Tests for InitRequest model."""

    def test_valid_request_with_all_fields(self):
        """Test creating a valid request with all fields."""
        req = InitRequest(
            s3_bucket="test-bucket",
            s3_key="test-key",
            email="test@example.com",
            prompt="Analyze this",
        )
        assert req.s3_bucket == "test-bucket"
        assert req.s3_key == "test-key"
        assert req.email == "test@example.com"
        assert req.prompt == "Analyze this"

    def test_valid_request_only_required_fields(self):
        """Test creating a valid request with only required fields."""
        req = InitRequest(
            s3_bucket="test-bucket", s3_key="test-key", email="test@example.com"
        )
        assert req.s3_bucket == "test-bucket"
        assert req.s3_key == "test-key"
        assert req.email == "test@example.com"
        assert req.prompt is None

    def test_missing_s3_bucket_raises_error(self):
        """Test that missing s3_bucket raises ValueError."""
        with pytest.raises(ValueError, match="s3_bucket must be a non-empty string"):
            InitRequest(s3_bucket="", s3_key="key", email="test@example.com")

    def test_missing_s3_key_raises_error(self):
        """Test that missing s3_key raises ValueError."""
        with pytest.raises(ValueError, match="s3_key must be a non-empty string"):
            InitRequest(s3_bucket="bucket", s3_key="", email="test@example.com")

    def test_missing_email_raises_error(self):
        """Test that missing email raises ValueError."""
        with pytest.raises(ValueError, match="email must be a non-empty string"):
            InitRequest(s3_bucket="bucket", s3_key="key", email="")

    def test_invalid_prompt_type_raises_error(self):
        """Test that invalid prompt type raises ValueError."""
        with pytest.raises(ValueError, match="prompt must be a string when provided"):
            InitRequest(
                s3_bucket="bucket", s3_key="key", email="test@example.com", prompt=123
            )

    def test_to_dict_method(self):
        """Test the to_dict method serialization."""
        req = InitRequest(
            s3_bucket="test-bucket",
            s3_key="test-key",
            email="test@example.com",
            prompt="Analyze this",
        )
        expected_dict = {
            "s3_bucket": "test-bucket",
            "s3_key": "test-key",
            "email": "test@example.com",
            "prompt": "Analyze this",
        }
        assert req.to_dict() == expected_dict


class TestRequestParser:
    """Tests for RequestParser."""

    def test_parse_sqs_event(self):
        """Test parsing an SQS event record."""
        sqs_event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "s3_bucket": "sqs-bucket",
                            "s3_key": "sqs-key",
                            "email": "sqs@example.com",
                            "prompt": "SQS prompt",
                        }
                    )
                }
            ]
        }
        req = RequestParser.parse_event(sqs_event)
        assert req.s3_bucket == "sqs-bucket"
        assert req.email == "sqs@example.com"

    def test_parse_api_gateway_event(self):
        """Test parsing an API Gateway event."""
        api_gw_event = {
            "body": json.dumps(
                {
                    "s3_bucket": "api-gw-bucket",
                    "s3_key": "api-gw-key",
                    "email": "api@example.com",
                }
            )
        }
        req = RequestParser.parse_event(api_gw_event)
        assert req.s3_bucket == "api-gw-bucket"
        assert req.email == "api@example.com"
        assert req.prompt is None

    def test_parse_direct_invocation_event(self):
        """Test parsing a direct Lambda invocation event."""
        direct_event = {
            "s3_bucket": "direct-bucket",
            "s3_key": "direct-key",
            "email": "direct@example.com",
            "prompt": "Direct prompt",
        }
        req = RequestParser.parse_event(direct_event)
        assert req.s3_bucket == "direct-bucket"
        assert req.email == "direct@example.com"

    def test_missing_required_field_raises_value_error(self):
        """Test that missing required fields in payload raise ValueError."""
        event = {"s3_bucket": "bucket", "s3_key": "key"}  # Missing email
        with pytest.raises(ValueError, match="Missing required field: 'email'"):
            RequestParser.parse_event(event)

    def test_invalid_json_body_raises_json_decode_error(self):
        """Test that invalid JSON in body raises JSONDecodeError."""
        event = {"body": "invalid json string"}
        with pytest.raises(json.JSONDecodeError):
            RequestParser.parse_event(event)

    def test_unsupported_event_format_raises_value_error(self):
        """Test that an unsupported event format raises ValueError."""
        event = ["not a dict"]
        with pytest.raises(ValueError, match="Unsupported event format"):
            RequestParser.parse_event(event)


class TestStepFunctionTriggerService:
    """Tests for StepFunctionTriggerService."""

    @patch(".stepfunction_service.boto3.client")
    def test_start_step_functions_success(self, mock_boto3_client):
        """Test successful Step Functions execution start."""
        mock_sfn_client = MagicMock()
        mock_sfn_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:workflow:123",
            "startDate": "2023-01-01T00:00:00Z",
        }
        mock_boto3_client.return_value = mock_sfn_client

        service = StepFunctionTriggerService(state_machine_arn="test-arn")
        payload = InitRequest(
            s3_bucket="bucket", s3_key="key", email="test@example.com"
        )
        execution_arn = service.start_step_functions(payload)

        assert (
            execution_arn
            == "arn:aws:states:us-east-1:123456789012:execution:workflow:123"
        )
        mock_sfn_client.start_execution.assert_called_once()
        args, kwargs = mock_sfn_client.start_execution.call_args
        assert kwargs["stateMachineArn"] == "test-arn"
        assert "execution-" in kwargs["name"]
        assert json.loads(kwargs["input"]) == payload.to_dict()

    @patch(".stepfunction_service.boto3.client")
    def test_start_step_functions_failure_raises_exception(self, mock_boto3_client):
        """Test that Step Functions execution failure raises an exception."""
        mock_sfn_client = MagicMock()
        mock_sfn_client.start_execution.side_effect = Exception("SFN error")
        mock_boto3_client.return_value = mock_sfn_client

        service = StepFunctionTriggerService(state_machine_arn="test-arn")
        payload = InitRequest(
            s3_bucket="bucket", s3_key="key", email="test@example.com"
        )

        with pytest.raises(Exception, match="SFN error"):
            service.start_step_functions(payload)


class TestInitOrchestrator:
    """Tests for InitOrchestrator."""

    @patch(".orchestrator.RequestParser.parse_event")
    def test_process_event_success(self, mock_parse_event):
        """Test successful end-to-end processing by the orchestrator."""
        # Mock InitRequest object returned by RequestParser
        mock_request = MagicMock(spec=InitRequest)
        mock_request.s3_bucket = "mock-bucket"
        mock_request.s3_key = "mock-key"
        mock_request.email = "mock@example.com"
        mock_request.prompt = "Mock prompt"
        mock_request.to_dict.return_value = {
            "s3_bucket": "mock-bucket",
            "s3_key": "mock-key",
            "email": "mock@example.com",
            "prompt": "Mock prompt",
        }
        mock_parse_event.return_value = mock_request

        # Mock StepFunctionTriggerService
        mock_sfn_service = MagicMock(spec=StepFunctionTriggerService)
        mock_sfn_service.start_step_functions.return_value = (
            "arn:aws:states:us-east-1:123456789012:execution:workflow:orchestrator-123"
        )

        orchestrator = InitOrchestrator(
            state_machine_arn="test-sfn-arn", stepfunction_service=mock_sfn_service
        )

        event = {"body": json.dumps({"s3_bucket": "b", "s3_key": "k", "email": "e"})}
        result = orchestrator.process_event(event)

        mock_parse_event.assert_called_once_with(event)
        mock_sfn_service.start_step_functions.assert_called_once_with(mock_request)

        assert result["status"] == "ACCEPTED"
        assert result["email"] == "mock@example.com"
        assert (
            result["execution_arn"]
            == "arn:aws:states:us-east-1:123456789012:execution:workflow:orchestrator-123"
        )

    def test_process_event_validation_error(self):
        """Test that validation errors from RequestParser are propagated."""
        with patch(
            ".orchestrator.RequestParser.parse_event",
            side_effect=ValueError("Invalid input"),
        ):
            orchestrator = InitOrchestrator(state_machine_arn="test-sfn-arn")
            event = {"body": "invalid json"}
            with pytest.raises(ValueError, match="Invalid input"):
                orchestrator.process_event(event)

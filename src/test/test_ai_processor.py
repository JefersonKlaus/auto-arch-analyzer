import os
import json
import sys
from pathlib import Path
from typing import Dict
from unittest.mock import patch, MagicMock

import pytest

# Make handler modules importable when running tests from src/.
# This adds the 'src' directory to the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lambdas.ai_processor.decorators import parse_message
from lambdas.ai_processor.handler import lambda_handler
from lambdas.ai_processor.models import ProcessImageAIDTO
from lambdas.ai_processor.orchestrator import AIProcessorOrchestrator
from lambdas.ai_processor.bedrock_service import BedrockService

test_sqs_message = {
    "Records": [
        {
            "messageId": "string-gerado-pelo-sqs",
            "receiptHandle": "string-gerado-pelo-sqs",
            "body": '{"email": "emailtest@gmail.com", "prompt": null, "s3_file_path": "voce/95490a0e-diagram.png"}',
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1678886400000",
                "SenderId": "AIDAIXMPLSPXMPL",
                "ApproximateFirstReceiveTimestamp": "1678886400000"
            },
            "messageAttributes": {},
            "md5OfBody": "md5-hash-do-body",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:my-queue",
            "awsRegion": "us-east-1"
        }
    ]
}


class TestDecorators:
    """Tests for decorator functions."""
    def test_parse_message_sqs_event(self):
        """Tests that parse_message correctly extracts and parses the body from an SQS event."""
        parsed_body = parse_message(test_sqs_message)
        assert isinstance(parsed_body, Dict)
        assert parsed_body["email"] == "emailtest@gmail.com"
        assert parsed_body["s3_file_path"] == "voce/95490a0e-diagram.png"
        assert parsed_body["prompt"] is None

    def test_parse_message_direct_payload(self):
        """Tests that parse_message handles a direct payload event."""
        direct_payload = {
            "email": "direct@example.com",
            "s3_file_path": "direct/path.png",
            "prompt": "direct"
        }
        parsed_body = parse_message(direct_payload)
        assert parsed_body == direct_payload

    def test_parse_message_api_gateway_payload(self):
        """Tests that parse_message handles an API Gateway-like event."""
        api_gw_payload = {
            "body": '{"email": "api@example.com", "s3_file_path": "api/path.png"}'
        }
        parsed_body = parse_message(api_gw_payload)
        assert parsed_body["email"] == "api@example.com"
        assert parsed_body["s3_file_path"] == "api/path.png"

    def test_parse_message_invalid_json(self):
        """Tests that parse_message raises JSONDecodeError for invalid JSON in body."""
        invalid_sqs_message = {
            "Records": [{"body": "this is not json"}]
        }
        with pytest.raises(json.JSONDecodeError):
            parse_message(invalid_sqs_message)


class TestAIProcessorHandler:
    """Tests for the main lambda_handler."""

    @patch('lambdas.ai_processor.handler.AIProcessorOrchestrator')
    @patch.dict(os.environ, {"S3_DIAGRAM_BUCKET": "test-bucket"})
    def test_lambda_handler_success(self, mock_orchestrator_cls):
        """Tests the happy path of the lambda handler."""
        # Arrange
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.process_diagram.return_value = {"status": "success"}
        mock_orchestrator_cls.return_value = mock_orchestrator_instance

        event_body = {
            "email": "test@example.com",
            "s3_file_path": "path/to/diagram.png",
            "prompt": "Analyze this"
        }
        sqs_event = {"Records": [{"body": json.dumps(event_body)}]}

        # Act
        result = lambda_handler(sqs_event, None)

        # Assert
        assert result == {"status": "success"}
        mock_orchestrator_cls.assert_called_once_with(s3_bucket_name="test-bucket")

        called_with_dto = mock_orchestrator_instance.process_diagram.call_args[0][0]
        assert isinstance(called_with_dto, ProcessImageAIDTO)
        assert called_with_dto.email == "test@example.com"
        assert called_with_dto.s3_file_path == "path/to/diagram.png"
        assert called_with_dto.prompt == "Analyze this"

    def test_lambda_handler_missing_env_var(self):
        """Tests that the handler fails fast if the S3_BUCKET env var is missing."""
        # Arrange
        if "S3_DIAGRAM_BUCKET" in os.environ:
            del os.environ["S3_DIAGRAM_BUCKET"]

        sqs_event = {"Records": [{"body": "{}"}]}

        # Act & Assert
        with pytest.raises(RuntimeError, match="Missing required environment variable: S3_DIAGRAM_BUCKET"):
            lambda_handler(sqs_event, None)

    @patch.dict(os.environ, {"S3_DIAGRAM_BUCKET": "test-bucket"})
    def test_lambda_handler_validation_error(self):
        """Tests that the handler raises ValueError for invalid input payload."""
        # Arrange
        invalid_event_body = {"email": "test@example.com"}
        sqs_event = {"Records": [{"body": json.dumps(invalid_event_body)}]}

        # Act & Assert
        with pytest.raises(ValueError):
            lambda_handler(sqs_event, None)

    @patch('lambdas.ai_processor.handler.AIProcessorOrchestrator')
    @patch.dict(os.environ, {"S3_DIAGRAM_BUCKET": "test-bucket"})
    def test_lambda_handler_orchestrator_exception(self, mock_orchestrator_cls):
        """Tests that exceptions from the orchestrator are propagated."""
        # Arrange
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.process_diagram.side_effect = Exception("Orchestrator failed")
        mock_orchestrator_cls.return_value = mock_orchestrator_instance

        event_body = {
            "email": "test@example.com",
            "s3_file_path": "path/to/diagram.png",
            "prompt": "Analyze this"
        }
        sqs_event = {"Records": [{"body": json.dumps(event_body)}]}

        # Act & Assert
        with pytest.raises(Exception, match="Orchestrator failed"):
            lambda_handler(sqs_event, None)


class TestAIProcessorOrchestrator:
    """Tests for the AIProcessorOrchestrator."""

    def test_process_diagram(self):
        """Tests that the orchestrator correctly calls the bedrock service."""
        # Arrange
        mock_bedrock_service = MagicMock()
        mock_bedrock_service.process_image.return_value = {"analysis": "done"}

        orchestrator = AIProcessorOrchestrator(
            s3_bucket_name="test-bucket",
            bedrock_service=mock_bedrock_service
        )

        dto = ProcessImageAIDTO(
            email="test@example.com",
            s3_file_path="path/to/file.png",
            prompt="test prompt"
        )

        # Act
        result = orchestrator.process_diagram(dto)

        # Assert
        assert result == {"analysis": "done"}
        mock_bedrock_service.process_image.assert_called_once_with(dto)


class TestBedrockService:
    """Tests for the BedrockService."""

    @pytest.fixture
    def dto(self):
        return ProcessImageAIDTO(
            email="test@example.com",
            s3_file_path="path/to/diagram.png",
            prompt="Analyze this"
        )

    @patch('lambdas.ai_processor.bedrock_service.boto3.client')
    @patch('lambdas.ai_processor.bedrock_service.S3Service')
    def test_process_image_success(self, mock_s3_service_cls, mock_boto_client, dto):
        """Tests successful image processing."""
        # Arrange
        mock_s3_instance = MagicMock()
        mock_s3_instance.get_image_from_s3.return_value = b'imagedata'
        mock_s3_service_cls.return_value = mock_s3_instance

        mock_bedrock_runtime = MagicMock()
        api_response = {"content": [{"type": "text", "text": '{"result": "success"}'}]}
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps(api_response).encode('utf-8')
        mock_bedrock_runtime.invoke_model.return_value = {'body': mock_response_body}

        mock_boto_client.return_value = mock_bedrock_runtime

        service = BedrockService(model="anthropic.claude-3-haiku-20240307-v1:0", s3_bucket_name="test-bucket")

        # Act
        result = service.process_image(dto)

        # Assert
        assert result == {"result": "success"}
        mock_s3_instance.get_image_from_s3.assert_called_once_with("path/to/diagram.png")
        mock_bedrock_runtime.invoke_model.assert_called_once()

        invoke_model_args = mock_bedrock_runtime.invoke_model.call_args[1]
        assert invoke_model_args['modelId'] == "anthropic.claude-3-haiku-20240307-v1:0"
        body = json.loads(invoke_model_args['body'])
        assert body['messages'][0]['content'][0]['source']['media_type'] == 'image/png'

    @patch('lambdas.ai_processor.bedrock_service.boto3.client')
    @patch('lambdas.ai_processor.bedrock_service.S3Service')
    def test_process_image_invalid_json_response(self, mock_s3_service_cls, mock_boto_client, dto):
        """Tests handling of a non-JSON response from the model."""
        # Arrange
        mock_s3_instance = MagicMock()
        mock_s3_instance.get_image_from_s3.return_value = b'imagedata'
        mock_s3_service_cls.return_value = mock_s3_instance

        mock_bedrock_runtime = MagicMock()
        api_response = {"content": [{"type": "text", "text": 'this is not valid json'}]}
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps(api_response).encode('utf-8')
        mock_bedrock_runtime.invoke_model.return_value = {'body': mock_response_body}

        mock_boto_client.return_value = mock_bedrock_runtime

        service = BedrockService(model="anthropic.claude-3-haiku-20240307-v1:0", s3_bucket_name="test-bucket")

        # Act & Assert
        with pytest.raises(ValueError, match="Resposta do modelo não é um JSON válido."):
            service.process_image(dto)

    @patch('lambdas.ai_processor.bedrock_service.boto3.client')
    @patch('lambdas.ai_processor.bedrock_service.S3Service')
    def test_process_image_unsupported_model(self, mock_s3_service_cls, mock_boto_client, dto):
        """Tests that an error is raised for an unsupported model."""
        # Arrange
        mock_s3_instance = MagicMock()
        mock_s3_instance.get_image_from_s3.return_value = b'imagedata'
        mock_s3_service_cls.return_value = mock_s3_instance
        mock_boto_client.return_value = MagicMock()

        service = BedrockService(model="unsupported-model", s3_bucket_name="test-bucket")

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported model"):
            service.process_image(dto)

    @patch('lambdas.ai_processor.bedrock_service.S3Service')
    def test_get_image_success(self, mock_s3_service_cls):
        """Tests successful image retrieval and media type detection."""
        # Arrange
        mock_s3_instance = MagicMock()
        mock_s3_instance.get_image_from_s3.return_value = b'imagedata'
        mock_s3_service_cls.return_value = mock_s3_instance

        service = BedrockService(model="any-model", s3_bucket_name="test-bucket")

        test_cases = {
            "test.png": "image/png",
            "test.jpeg": "image/jpeg",
            "test.jpg": "image/jpeg",
            "test.gif": "image/gif",
            "test.unknown": "image/jpeg"  # Default case
        }

        for s3_key, expected_media_type in test_cases.items():
            # Act
            image_bytes, media_type = service.get_image(s3_key)

            # Assert
            assert image_bytes == b'imagedata'
            assert media_type == expected_media_type
            mock_s3_instance.get_image_from_s3.assert_called_with(s3_key)

    @patch('lambdas.ai_processor.bedrock_service.S3Service')
    def test_get_image_no_s3_key(self, mock_s3_service_cls):
        """Tests that an error is raised if the S3 key is empty."""
        # Arrange
        service = BedrockService(model="any-model", s3_bucket_name="test-bucket")

        # Act & Assert
        with pytest.raises(ValueError, match="Nenhuma chave S3 fornecida no evento."):
            service.get_image("")

    @patch('lambdas.ai_processor.bedrock_service.uuid.uuid4', return_value='test-uuid')
    @patch('lambdas.ai_processor.bedrock_service.datetime')
    def test_get_prompt_text(self, mock_datetime, mock_uuid):
        """Tests the generation of the prompt text."""
        # Arrange
        mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        service = BedrockService(model="any-model", s3_bucket_name="test-bucket")
        user_context = "This is a test context."

        # Act
        prompt = service.get_prompt_text(user_context)

        # Assert
        assert "You are a cloud architect expert." in prompt
        assert f"User Context: {user_context}" in prompt
        assert 'For the \'execution_id\' field, use this value: test-uuid' in prompt
        assert 'For the \'analysis_date\' field, use this value: 2024-01-01T12:00:00Z' in prompt
        assert 'Set \'processing_status\' as "ANALYZED".' in prompt
        assert '"type": "object"' in prompt  # Check if schema is included

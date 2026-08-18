"""Unit tests for the IA consumer Lambda components."""

import json
from unittest.mock import MagicMock, patch

import pytest

from lambdas.ia_consumer.handler import lambda_handler
from lambdas.ia_consumer.http_service import IAConsumerApiClient
from lambdas.ia_consumer.models import IAConsumerRequest
from lambdas.ia_consumer.orchestrator import IAConsumerOrchestrator
from lambdas.ia_consumer.request_parser import RequestParser
from lambdas.ia_consumer.s3_service import S3UrlSigner


class TestIAConsumerRequest:
    def test_valid_request_with_s3_file_path(self):
        request = IAConsumerRequest(
            prompt="Analyze", s3_file_path="s3://bucket/key.png"
        )
        assert request.prompt == "Analyze"
        assert request.s3_file_path == "s3://bucket/key.png"

    def test_valid_request_with_imagem_url(self):
        request = IAConsumerRequest(
            prompt="Analyze", imagem_url="https://example.com/image"
        )
        assert request.imagem_url == "https://example.com/image"

    def test_missing_image_reference_raises(self):
        with pytest.raises(ValueError, match="imagem_url or s3_file_path is required"):
            IAConsumerRequest(prompt="Analyze")


class TestRequestParser:
    def test_parse_event_from_direct_payload(self):
        payload = RequestParser.parse_event(
            {"prompt": "Analyze", "s3_file_path": "s3://bucket/key.png"}
        )
        assert payload["prompt"] == "Analyze"
        assert payload["s3_file_path"] == "s3://bucket/key.png"

    def test_parse_event_with_bucket_and_key(self):
        payload = RequestParser.parse_event(
            {
                "prompt": "Analyze",
                "s3_bucket": "bucket",
                "s3_key": "folder/key.png",
            }
        )
        assert payload["s3_file_path"] == "s3://bucket/folder/key.png"


class TestS3UrlSigner:
    @patch("lambdas.ia_consumer.s3_service.boto3.client")
    def test_create_presigned_url(self, mock_boto3_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://signed-url"
        mock_boto3_client.return_value = mock_s3

        signer = S3UrlSigner()
        url = signer.create_presigned_url("s3://bucket/key.png")

        assert url == "https://signed-url"
        mock_s3.generate_presigned_url.assert_called_once()


class TestIAConsumerApiClient:
    @patch("lambdas.ia_consumer.http_service.urlopen")
    def test_analyze_posts_payload_and_parses_json(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
        mock_urlopen.return_value = response

        client = IAConsumerApiClient("https://example.com/analisar", "secret")
        result = client.analyze("Prompt", "https://signed-url")

        assert result == {"status": "ok"}
        request = mock_urlopen.call_args[0][0]
        assert request.get_header("X-api-key") == "secret"


class TestIAConsumerOrchestrator:
    def test_process_signs_image_and_calls_api(self):
        mock_signer = MagicMock()
        mock_signer.create_presigned_url.return_value = "https://signed-url"

        mock_api_client = MagicMock()
        mock_api_client.analyze.return_value = {"analysis": "done"}

        orchestrator = IAConsumerOrchestrator(
            api_url="https://example.com/analisar",
            api_key="secret",
            signer=mock_signer,
            api_client=mock_api_client,
        )

        result = orchestrator.process(
            {
                "prompt": "Analyze",
                "s3_file_path": "s3://bucket/key.png",
                "email": "user@example.com",
            }
        )

        assert result["imagem_url"] == "https://signed-url"
        assert result["technical_analysis"] == {"analysis": "done"}
        mock_signer.create_presigned_url.assert_called_once_with(
            "s3://bucket/key.png", expiration_seconds=300
        )
        mock_api_client.analyze.assert_called_once_with("Analyze", "https://signed-url")


class TestLambdaHandler:
    @patch.dict(
        "lambdas.ia_consumer.handler.os.environ",
        {
            "IA_CONSUMER_API_URL": "https://example.com/analisar",
            "IA_CONSUMER_API_KEY": "secret",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("lambdas.ia_consumer.handler.IAConsumerOrchestrator")
    def test_handler_success(self, mock_orchestrator_class):
        mock_orchestrator = MagicMock()
        mock_orchestrator.process.return_value = {"status": "ok"}
        mock_orchestrator_class.return_value = mock_orchestrator

        result = lambda_handler(
            {"prompt": "Analyze", "s3_file_path": "s3://bucket/key.png"}, None
        )

        assert result == {"status": "ok"}
        mock_orchestrator_class.assert_called_once_with(
            api_url="https://example.com/analisar",
            api_key="secret",
            region="us-east-1",
        )

"""Orchestration layer for the IA consumer lambda."""

from typing import Any, Dict, Optional

from http_service import IAConsumerApiClient
from models import IAConsumerRequest
from request_parser import RequestParser
from s3_service import S3UrlSigner


class IAConsumerOrchestrator:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        region: str = "us-east-1",
        timeout_seconds: int = 300,
        signer: Optional[S3UrlSigner] = None,
        api_client: Optional[IAConsumerApiClient] = None,
    ):
        self.signer = signer or S3UrlSigner(region)
        self.api_client = api_client or IAConsumerApiClient(
            api_url, api_key, timeout_seconds=timeout_seconds
        )

    def process(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = RequestParser.parse_event(event)
        request: IAConsumerRequest = RequestParser.to_request(payload)

        imagem_url = request.imagem_url
        if not imagem_url or imagem_url.startswith("s3://"):
            source_path = imagem_url or request.s3_file_path
            imagem_url = self.signer.create_presigned_url(
                source_path, expiration_seconds=300
            )

        analysis = self.api_client.analyze(request.prompt, imagem_url)

        result = dict(payload)
        result["imagem_url"] = imagem_url
        result["technical_analysis"] = analysis
        return result

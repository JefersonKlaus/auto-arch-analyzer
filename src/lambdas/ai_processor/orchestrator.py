"""
Orchestration layer for the AI processing workflow.
Single Responsibility: Coordinate the AI analysis of a diagram.
"""

from typing import Any, Dict, Optional
import logging

from bedrock_service import BedrockService
from models import ProcessImageAIDTO

logger = logging.getLogger(__name__)


class AIProcessorOrchestrator:
    """Orchestrates the analysis of a diagram image using an AI model."""

    def __init__(
        self,
        s3_bucket_name: str,
        bedrock_service: Optional[BedrockService] = None,
    ):
        """
        Initialize orchestrator dependencies.

        Args:
            s3_bucket_name: The name of the S3 bucket where diagrams are stored.
            bedrock_service: Optional injected service for testing.
        """
        self.bedrock_service = bedrock_service or BedrockService(
            model="anthropic.claude-3-haiku-20240307-v1:0",
            s3_bucket_name=s3_bucket_name,
        )

    def process_diagram(self, process_image_dto: ProcessImageAIDTO) -> Dict[str, Any]:
        """
        Process a diagram analysis request.

        Args:
            process_image_dto: A DTO containing the data needed for processing.

        Returns:
            A dictionary containing the technical analysis from the AI model.
        """
        logger.info(
            "Starting diagram analysis for s3_path: %s", process_image_dto.s3_file_path
        )
        analysis_result = self.bedrock_service.process_image(process_image_dto)
        logger.info("Successfully completed diagram analysis.")
        return analysis_result

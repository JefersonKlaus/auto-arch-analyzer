import json
import boto3
import base64
import logging
import uuid
from datetime import datetime
from s3_service import S3Service
from typing import Any, Dict, Optional
from models import ProcessImageAIDTO
from botocore.config import Config


class BedrockService():
    def __init__(self, model: str, s3_bucket_name: str):
        self.region = 'us-east-1'
        retry_config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 5,  
                'mode': 'adaptive'  
            }
        )
        self.bedrock_runtime_client = boto3.client('bedrock-runtime', config=retry_config)
        self.bedrock_management_client = boto3.client(
            'bedrock', config=retry_config)
        self.model = model
        self.s3_service = S3Service(bucket_name=s3_bucket_name)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"BedrockClient initialized with model: {self.model}")

    def list_models(self):
        """
        Lista os modelos de fundação disponíveis no AWS Bedrock.
        """
        self.logger.info("Listando modelos de fundação do Bedrock...")
        response = self.bedrock_management_client.list_foundation_models()
        models = response.get('modelSummaries', [])
        return models

    def get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "execution_id": {"type": "string", "description": "Unique identifier for this analysis execution."},
                "analysis_date": {"type": "string", "description": "Date and time of the analysis in ISO 8601 format."},
                "processing_status": {"type": "string", "description": "Status of the analysis (e.g., ANALYZED, FAILED)."},
                "technical_analysis": {
                    "type": "object",
                    "properties": {
                        "architecture_summary": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "A high-level description of the architecture."},
                                "architectural_style": {"type": "string", "description": "Identified architectural style (e.g., Serverless, Microservices)."},
                                "cloud_provider": {"type": "string", "description": "The cloud provider used (e.g., AWS, Azure, GCP)."},
                            },
                            "required": ["description", "architectural_style", "cloud_provider"]
                        },
                        "service_inventory": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Name of the service/component."},
                                    "category": {"type": "string", "description": "Category of the service (e.g., Compute, Database, Networking)."},
                                    "quantity": {"type": "number", "description": "Number of instances or occurrences of this service."},
                                },
                                "required": ["name", "category", "quantity"]
                            }
                        },
                        "architecture_findings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "description": "Type of finding (e.g., Security, Bottleneck, Cost, Scalability)."},
                                    "description": {"type": "string", "description": "Detailed description of the finding."},
                                    "criticality": {"type": "string", "description": "Criticality level (e.g., High, Medium, Low)."},
                                },
                                "required": ["type", "description", "criticality"]
                            }
                        },
                    },
                    "required": ["architecture_summary", "service_inventory", "architecture_findings"]
                },
            },
            "required": ["execution_id", "analysis_date", "processing_status", "technical_analysis"]
        }

    def process_image(self, process_image_dto: ProcessImageAIDTO) -> Dict[str, Any]:
        """
        Processa uma imagem de um bucket S3 usando a API AWS Bedrock (Claude 3 Vision)
        e retorna uma análise estruturada em JSON.

        :param process_image_dto: DTO com os dados para processamento.
        :return: Um dicionário contendo a resposta do modelo Bedrock em JSON.
        :raises ValueError: Se o modelo não for suportado ou a resposta do modelo for inválida.
        :raises Exception: Para erros na recuperação de imagem ou chamada da API Bedrock.
        """
        try:
            image_bytes, media_type = self.get_image(process_image_dto.s3_file_path)
        except Exception as e:
            self.logger.error(f"Falha ao recuperar imagem para processamento: {e}")
            raise

        prompt_text = self.get_prompt_text(
            user_context=process_image_dto.prompt)

        if self.model.startswith("anthropic.claude-3"):
            request_body = self._build_request(image_bytes=image_bytes, media_type=media_type, prompt_text=prompt_text)
        else:
            raise ValueError(f"Unsupported model: {self.model}. Please use a supported multimodal model (e.g., Claude 3).")

        self.logger.info(f"Invoking Bedrock model: {self.model}")
        self.logger.debug(
            f"Request body for {self.model}: {json.dumps(request_body, indent=2)}")

        try:
            response = self.bedrock_runtime_client.invoke_model(
                body=json.dumps(request_body),
                modelId=self.model,
                accept='application/json',
                contentType='application/json'
            )

            response_body = json.loads(response.get('body').read())

            bedrock_response_text = response_body['content'][0]['text']
            try:
                # A resposta do modelo deve ser um JSON, então fazemos o parse e retornamos o dicionário
                return json.loads(bedrock_response_text)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Resposta do modelo não é um JSON válido: {bedrock_response_text}")
                raise ValueError("Resposta do modelo não é um JSON válido.")

        except Exception as e:
            self.logger.error(f"Erro durante a chamada da API Bedrock: {e}")
            raise

    def get_image(self, s3_key: str):
        """
        Recupera os bytes da imagem e o tipo de mídia (mime_type) de um caminho S3.
        Retorna uma tupla (image_bytes, media_type) ou levanta uma exceção em caso de erro.
        """
        if not s3_key:
            raise ValueError("Nenhuma chave S3 fornecida no evento.")

        try:
            self.logger.info(f"Recuperando imagem do S3: {s3_key}")
            image_bytes = self.s3_service.get_image_from_s3(s3_key)

            s3_key_lower = s3_key.lower()
            if s3_key_lower.endswith('.png'):
                media_type = "image/png"
            elif s3_key_lower.endswith('.gif'):
                media_type = "image/gif"
            elif s3_key_lower.endswith(('.jpeg', '.jpg')):
                media_type = "image/jpeg"
            else:
                media_type = "image/jpeg"  # Default
                self.logger.warning(f"Tipo de mídia não reconhecido para S3 key: {s3_key}. Usando default: {media_type}")

            return image_bytes, media_type
        except Exception as e:
            self.logger.error(f"Erro ao recuperar imagem: {e}")
            raise

    def get_prompt_text(self, user_context: str):
        response_schema_dict = self.get_response_schema()
        execution_id = str(uuid.uuid4())
        analysis_date = datetime.utcnow().isoformat() + "Z"
        return f"""
                            You are a cloud architect expert. Your task is to analyze the provided architecture diagram.
                            Based on the diagram and the following user context, provide a detailed technical analysis.
                            The analysis must be returned in JSON format, strictly adhering to the provided JSON schema.
                            Ensure that all required fields in the schema are accurately filled based on your analysis of the diagram and the context.

                            User Context: {user_context if user_context else "No additional context provided."}

                            Diagram Analysis Requirements:

                            Architecture Summary: Provide a high-level description, identify the architectural style, and the cloud provider.
                            Service Inventory: List all identified services, their categories (e.g., Compute, Database, Networking) and their quantities.
                            Architecture Findings: Identify possible issues or areas for improvement. Categorize them by type (e.g., Security, Bottleneck, Cost, Scalability), provide a description, and assign a criticality (High, Medium, Low).

                            For the 'execution_id' field, use this value: {execution_id}
                            For the 'analysis_date' field, use this value: {analysis_date}
                            Set 'processing_status' as "ANALYZED".

                            Here is the JSON schema you MUST adhere to:
                            ```json
                            {json.dumps(response_schema_dict, indent=2)}
                            ```
                            Please provide only the JSON output, no conversational text before or after.
                            """

    def _build_request(self, image_bytes: bytes, media_type: str, prompt_text: str) -> Dict[str, Any]:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    }
                ],
                "max_tokens": 4000,  
                "temperature": 0.0,  
                "top_p": 1  
            }

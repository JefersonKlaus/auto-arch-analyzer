import json
import os
from io import BytesIO

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from PIL import Image

from machine import analyze_architecture, extract_response, load_vision_model
from models import PayloadRequisicao

# Carrega o modelo de visão multimodal Qwen2-VL-7B-Instruct na VRAM
model, tokenizer = load_vision_model()


load_dotenv()
API_SECRET = os.environ.get("API_SECRET")

# Inicia a aplicação FastAPI com o título "Especialista Cloud - Motor de Visão"
app = FastAPI(title="Especialista Cloud - Motor de Visão")
header_chave_api = APIKeyHeader(name="X-API-Key", auto_error=True)


def validar_api_key(chave_enviada: str = Security(header_chave_api)):
    if chave_enviada != API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: API Key inválida",
        )
    return chave_enviada


# Endpoint para receber o diagrama arquitetural e o prompt do usuário
@app.post("/analisar", dependencies=[Security(validar_api_key)])
async def receber_diagrama(dados: PayloadRequisicao):
    try:
        # Extrai os dados do JSON recebido
        prompt = dados.prompt
        imagem_url = dados.imagem_url

        # Carregando a imagem a partir da URL S3 fornecida
        resp = requests.get(imagem_url, timeout=10)
        resp.raise_for_status()
        imagem_arquitetura = Image.open(BytesIO(resp.content)).convert("RGB")

        # Instrução detalhada para o modelo de visão multimodal
        resposta_bruta = analyze_architecture(
            model, tokenizer, prompt, imagem_arquitetura
        )
        # Extraindo a resposta do modelo e validando o JSON final
        resposta_util = extract_response(resposta_bruta, tokenizer)

        return json.loads(resposta_util)

    except Exception as e:
        # Tratamento de erro rigoroso para não derrubar o servidor se uma imagem quebrar
        return {"status": "erro", "detalhe": str(e)}

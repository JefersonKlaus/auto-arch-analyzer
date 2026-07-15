from pydantic import BaseModel


class PayloadRequisicao(BaseModel):
    prompt: str
    imagem_url: str

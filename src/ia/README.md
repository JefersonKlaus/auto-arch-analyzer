# API FastAPI local

Este diretório contém a API em FastAPI definida em [main.py](main.py).

## Pré-requisitos

- Python 3.11+
- Ambiente virtual criado em `.venv`
- Dependências instaladas a partir de [requirements.txt](requirements.txt)

## 1. Instalar dependências

Ative o ambiente virtual e instale as dependências:

```bash
cd /home/klaus/code/auto-arch-model/src/api
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Instalar o cloudflared no Linux

Se o `cloudflared` ainda não estiver instalado, faça o download do pacote oficial e instale com:

```bash
# 1. Faz o download do executável oficial da Cloudflare para Linux
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# 2. Instala o executável no sistema
sudo dpkg -i cloudflared.deb
```

## 3. Rodar a API localmente

Inicie a API a partir desta pasta:

```bash
cd /home/klaus/code/auto-arch-model/src/api
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Para reiniciar automaticamente ao alterar o código, use:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Expor a API com cloudflared

Com a API rodando localmente, abra o túnel público com:

```bash
cloudflared tunnel --url http://127.0.0.1:8000 --metrics localhost:45678
```

## 5. Acessar a API

- Documentação interativa: http://127.0.0.1:8000/docs
- Endpoint principal: `POST /analisar`

## Exemplo de chamada

Depois de subir a API, você pode testar com `curl` usando uma imagem real do workspace:

```bash
curl -X POST "http://127.0.0.1:8000/analisar" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Você é um Arquiteto Cloud. Extraia um JSON com as falhas dessa arquitetura.",
           "imagem_url": "https://d2908q01vomqb2.cloudfront.net/d435a6cdd786300dff204ee7c2ef942d3e9034e2/2020/07/24/Slide4.png"
         }'
```

O campo `imagem` precisa apontar para um arquivo existente no seu computador. Se usar um caminho inválido, o `curl` retorna erro de leitura local do arquivo.

## Observações

- O modelo é carregado no startup da aplicação, então a primeira inicialização pode demorar.
- O endpoint espera um formulário com `prompt` e um upload de imagem em `imagem`.
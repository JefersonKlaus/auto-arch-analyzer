import re

from unsloth import FastVisionModel

# Preparando a instrução para o modelo de visão
INSTRUCAO = """Você é um Arquiteto Cloud especialista em AWS.
Analise a imagem deste diagrama de arquitetura focado em resiliência e alta disponibilidade.

Regras absolutas para a sua análise:
1. Não proponha mudanças ou alterações no diagrama arquitetural existente.
2. Sua análise deve se limitar estritamente a sugerir a adição de componentes que estejam faltando para melhorar a resiliência.
3. Seja direto, técnico e utilize o vocabulário oficial da AWS.
4. Responda SOMENTE com um texto em formato JSON válido. Não inclua formatação markdown (como blocos ```json), não inclua introduções ou explicações fora do JSON. O primeiro caractere da sua resposta deve ser "{" e o último deve ser "}".
5. O JSON gerado deve ter sintaxe estritamente válida. Preste muita atenção para escapar corretamente quaisquer aspas duplas dentro dos valores de texto (use \") e nunca deixe vírgulas sobrando no final de objetos ou listas (trailing commas).
6. O JSON deve seguir exatamente a estrutura abaixo, preenchendo os valores dinamicamente com base na imagem e no contexto fornecido:

{
  "analysis_date": "[INSERIR TIMESTAMP ATUAL NO FORMATO ISO 8601]",
  "technical_analysis": {
    "architecture_summary": {
      "description": "...",
      "architectural_style": "...",
      "cloud_provider": "AWS"
    },
    "service_inventory": [
      {
        "name": "...",
        "category": "...",
        "quantity": 1
      }
    ],
    "architecture_findings": [
      {
        "type": "...",
        "description": "...",
        "criticality": "High"
      }
    ],
    "dynamic_context_response": {
      "focus_area_or_question": "[INSERIR O TEMA OU PERGUNTA FEITA NO CONTEXTO ADICIONAL]",
      "analysis": "..."
    }
  }
}

Utilize as informações fornecidas após a tag [CONTEXTO ADICIONAL] para focar sua análise ou responder a perguntas específicas dentro da chave "dynamic_context_response".

[CONTEXTO ADICIONAL]:
"""


def load_vision_model():
    # Iniciamos o modelo de visão Qwen2-VL-7B-Instruct na GPU (VRAM)
    print("Carregando Qwen2-VL-7B-Instruct na VRAM...")

    model, tokenizer = FastVisionModel.from_pretrained(
        model_name="unsloth/Qwen2-VL-7B-Instruct-bnb-4bit",
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth",
    )

    # Ligamos o "Modo Turbo" do Unsloth para inferência em tempo real
    FastVisionModel.for_inference(model)

    return model, tokenizer


def analyze_architecture(model, tokenizer, prompt, imagem_arquitetura):
    instrucao_final = INSTRUCAO + prompt

    # Criando a mensagem para o modelo de visão multimodal
    mensagens = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": imagem_arquitetura},
                {"type": "text", "text": instrucao_final},
            ],
        }
    ]

    # O Tokenizer do Qwen transforma o texto e a imagem em tensores matemáticos
    texto_processado = tokenizer.apply_chat_template(
        mensagens, add_generation_prompt=True
    )
    inputs = tokenizer(
        text=[texto_processado],
        images=[imagem_arquitetura],
        padding=True,
        return_tensors="pt",
    ).to(
        "cuda"
    )  # Despacha o cálculo pesado para a RTX 5060 Ti

    # Gerando a resposta do modelo de visão multimodal
    print("\nAnalisando a arquitetura... Isso pode levar alguns segundos.")
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,  # Tamanho máximo da resposta
        use_cache=True,
        do_sample=False,
    )

    return outputs


def extract_response(outputs, tokenizer):
    # Decodificando a resposta do robô para texto humano legível
    resposta_bruta = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    resposta_util = resposta_bruta.split("assistant\n")[-1].strip()

    # Remove blocos de código, caso o modelo ainda tente formatar a saída
    resposta_util = re.sub(r"^```(?:json)?\s*", "", resposta_util)
    resposta_util = re.sub(r"\s*```$", "", resposta_util)

    # Extrai e valida o JSON final antes de imprimir
    inicio_json = resposta_util.find("{")
    fim_json = resposta_util.rfind("}")
    if inicio_json == -1 or fim_json == -1 or fim_json <= inicio_json:
        raise ValueError(
            f"A resposta do modelo não contém um JSON válido:\n{resposta_bruta}"
        )
    return resposta_util[inicio_json : fim_json + 1]

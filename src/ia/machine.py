import re

from unsloth import FastVisionModel

# Preparando a instrução para o modelo de visão
INSTRUCAO = """Você é um Arquiteto Cloud especialista em AWS.
Analise a imagem deste diagrama de arquitetura focado em resiliência e alta disponibilidade.

Regras absolutas para a sua análise:
1. Não proponha mudanças ou alterações no diagrama arquitetural existente.
2. Sua análise deve se limitar estritamente a sugerir a adição de componentes que estejam faltando para melhorar a resiliência.
3. Seja direto, técnico e utilize o vocabulário oficial da AWS.
4. Responda SOMENTE com um JSON válido, sem markdown, sem blocos de código e sem explicações fora do JSON.
5. Use exatamente esta estrutura de saída:
{
"analysis_date": "2026-03-11T23:45:00Z",
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
    ]
}
}
6. Mantenha as chaves exatamente como descritas e preencha os valores com base na imagem.
Utilize o conteudo a seguir como informações adicionais para a análise ou contexto do diagrama.

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

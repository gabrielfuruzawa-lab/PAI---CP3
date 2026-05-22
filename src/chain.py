import json
from src.llm_client import LLMClient
from src.schemas import ClassificacaoSchema, ProcessamentoSchema, RespostaSchema
from src.prompts import (
    PROMPT_CLASSIFICAR,
    PROMPT_PROCESSAR_RECLAMACAO,
    PROMPT_PROCESSAR_DUVIDA,
    PROMPT_PROCESSAR_ELOGIO,
    PROMPT_PROCESSAR_SUGESTAO,
    PROMPT_RESPONDER,
)
from pydantic import ValidationError


def _carregar_system_prompt() -> str:
    try:
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Você é um assistente de suporte ao cliente da TechStore."


def _parsear_json(texto: str) -> dict:
    # às vezes o modelo retorna texto antes do JSON, então tenta achar o { }
    texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    if inicio != -1 and fim > inicio:
        try:
            return json.loads(texto[inicio:fim])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"JSON não encontrado na resposta: {texto[:200]}")


class AssistantChain:
    def __init__(self):
        self.client = LLMClient()
        self.system_prompt = _carregar_system_prompt()

    def etapa1_classificar(self, texto: str) -> ClassificacaoSchema:
        prompt = PROMPT_CLASSIFICAR.format(solicitacao=texto)

        for tentativa in range(3):
            try:
                resposta = self.client.chat(
                    system_prompt=self.system_prompt,
                    user_message=prompt,
                    expect_json=True,
                )
                dados = _parsear_json(resposta)
                return ClassificacaoSchema(**dados)
            except (ValidationError, ValueError):
                if tentativa == 2:
                    return ClassificacaoSchema(
                        tipo="duvida",
                        urgencia="media",
                        tema="não identificado",
                    )

    def etapa2_processar(
        self, classificacao: ClassificacaoSchema, texto_original: str
    ) -> ProcessamentoSchema:
        # aqui muda o prompt dependendo do tipo — isso é o chaining condicional
        classificacao_str = classificacao.model_dump_json()

        if classificacao.tipo == "reclamacao":
            prompt = PROMPT_PROCESSAR_RECLAMACAO.format(
                classificacao=classificacao_str, texto=texto_original
            )
        elif classificacao.tipo == "duvida":
            prompt = PROMPT_PROCESSAR_DUVIDA.format(
                classificacao=classificacao_str, texto=texto_original
            )
        elif classificacao.tipo == "elogio":
            prompt = PROMPT_PROCESSAR_ELOGIO.format(
                classificacao=classificacao_str, texto=texto_original
            )
        else:
            prompt = PROMPT_PROCESSAR_SUGESTAO.format(
                classificacao=classificacao_str, texto=texto_original
            )

        for tentativa in range(3):
            try:
                resposta = self.client.chat(
                    system_prompt=self.system_prompt,
                    user_message=prompt,
                    expect_json=True,
                )
                dados = _parsear_json(resposta)
                return ProcessamentoSchema(**dados)
            except (ValidationError, ValueError):
                if tentativa == 2:
                    return ProcessamentoSchema(
                        dados_extraidos={"erro": "falha ao processar"},
                        analise="Não foi possível processar a solicitação.",
                        sentimento="neutro",
                    )

    def etapa3_responder(
        self, processamento: ProcessamentoSchema, tipo: str
    ) -> RespostaSchema:
        prompt = PROMPT_RESPONDER.format(
            processamento=processamento.model_dump_json(),
            tipo=tipo,
        )

        for tentativa in range(3):
            try:
                resposta = self.client.chat(
                    system_prompt=self.system_prompt,
                    user_message=prompt,
                    expect_json=True,
                )
                dados = _parsear_json(resposta)
                return RespostaSchema(**dados)
            except (ValidationError, ValueError):
                if tentativa == 2:
                    return RespostaSchema(
                        resposta="Olá! Recebemos sua mensagem e em breve entraremos em contato.",
                        confianca="baixa",
                        acao_sugerida="encaminhar para atendente humano",
                    )

    def processar(self, texto: str) -> dict:
        etapa1 = self.etapa1_classificar(texto)
        etapa2 = self.etapa2_processar(etapa1, texto)
        etapa3 = self.etapa3_responder(etapa2, etapa1.tipo)

        return {
            "input": texto,
            "classificacao": etapa1.model_dump(),
            "processamento": etapa2.model_dump(),
            "resposta_final": etapa3.model_dump(),
        }

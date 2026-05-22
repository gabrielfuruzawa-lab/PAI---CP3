from pydantic import BaseModel, Field
from typing import Optional


class ClassificacaoSchema(BaseModel):
    tipo: str = Field(description="reclamacao|duvida|elogio|sugestao")
    urgencia: str = Field(description="alta|media|baixa")
    tema: str = Field(description="Tema principal da solicitacao")


class ProcessamentoSchema(BaseModel):
    dados_extraidos: dict = Field(description="Dados relevantes extraidos do texto")
    analise: str = Field(description="Analise detalhada da solicitacao")
    sentimento: Optional[str] = Field(default=None, description="positivo|negativo|neutro")


class RespostaSchema(BaseModel):
    resposta: str = Field(description="Resposta final ao cliente")
    confianca: str = Field(description="alta|media|baixa")
    acao_sugerida: str = Field(description="Proxima acao recomendada")

import re
import json
from typing import Tuple


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|anterior|above|instruc)",
    r"forget\s+(all\s+)?(rules|instruc|previous)",
    r"(you are now|agora você é|novo papel|new role)",
    r"(DAN|jailbreak|modo desenvolvedor|developer mode)",
    r"(reveal|mostrar?|print|exib[ae])\s+(your\s+)?(prompt|instru[cç])",
    r"(system\s*prompt|instrução\s*do\s*sistema)",
    r"(act as|aja como|pretend to be|finja ser)",
    r"(override|sobrescrever|bypass|contornar)\s+(rules|regras|filters|filtros)",
]

SYSTEM_KEYWORDS = [
    "você é a alexandra",
    "system prompt",
    "instrução interna",
    "regra interna",
    "techstore smart support",
    "nunca revele",
]


class GuardrailSystem:
    MAX_INPUT_LENGTH = 500
    FORBIDDEN_CHARS = re.compile(r"[<>{}\[\]\\]")

    def validar_input(self, texto: str) -> Tuple[bool, str]:
        if not texto or not texto.strip():
            return False, "Mensagem vazia."

        if len(texto) > self.MAX_INPUT_LENGTH:
            return False, (
                f"Mensagem muito longa ({len(texto)} caracteres). "
                f"Máximo: {self.MAX_INPUT_LENGTH}."
            )

        if self.FORBIDDEN_CHARS.search(texto):
            return False, "Mensagem contém caracteres não permitidos."

        texto_lower = texto.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, texto_lower, re.IGNORECASE):
                return False, (
                    "Sua mensagem parece conter uma tentativa de manipulação. "
                    "Por favor, envie uma solicitação normal."
                )

        return True, "ok"

    def validar_output(self, resposta: str) -> Tuple[bool, str]:
        if not resposta or not resposta.strip():
            return False, "Resposta vazia."

        resposta_lower = resposta.lower()
        for keyword in SYSTEM_KEYWORDS:
            if keyword in resposta_lower:
                return False, "Vazamento de dados internos detectado na resposta."

        if resposta.strip().startswith("{"):
            try:
                json.loads(resposta)
            except json.JSONDecodeError:
                return False, "JSON malformado."

        return True, "ok"

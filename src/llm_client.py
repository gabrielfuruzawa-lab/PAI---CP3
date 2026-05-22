import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "gpt-oss:120b")


class LLMClient:
    def __init__(self):
        self.url = OLLAMA_URL
        self.model = MODEL

    def chat(self, system_prompt: str, user_message: str, expect_json: bool = False) -> str:
        """
        Envia uma mensagem ao modelo via Ollama API e retorna a resposta como string.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }

        if expect_json:
            payload["format"] = "json"

        try:
            response = requests.post(
                f"{self.url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Nao foi possivel conectar ao Ollama em {self.url}. "
                "Verifique se o Ollama esta rodando com: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("O modelo demorou demais para responder. Tente novamente.")
        except Exception as e:
            raise RuntimeError(f"Erro na chamada ao LLM: {e}")

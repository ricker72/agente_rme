import logging
from typing import Callable

import requests

try:
    from ollama import Ollama
except ImportError:
    Ollama = None

logger = logging.getLogger(__name__)


class OllamaClient:
    """Local Ollama client wrapper with SDK or HTTP fallback."""

    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host
        self.client = Ollama() if Ollama is not None else None

    def check_ollama_alive(self) -> tuple[bool, str]:
        if self.client is not None:
            try:
                self.client.models()
                return True, "Ollama conectado"
            except Exception as exc:
                logger.warning("Ollama SDK no disponible: %s", exc)
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=2)
            if response.ok:
                return True, "Ollama HTTP conectado"
            return False, f"Ollama respondió con HTTP {response.status_code}"
        except Exception as exc:
            return False, str(exc)

    def list_models(self) -> list[str]:
        if self.client is not None:
            try:
                return [model.name for model in self.client.models()]
            except Exception:
                pass
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=3)
            if response.ok:
                return [model["name"] for model in response.json().get("models", [])]
        except Exception as exc:
            logger.error("Error listando modelos Ollama: %s", exc)
        return []

    def generate_stream(
        self,
        model: str,
        prompt: str,
        on_chunk: Callable[[str], None],
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        if self.client is not None:
            try:
                stream = self.client.generate(model=model, prompt=prompt, stream=True)
                full_text = ""
                for event in stream:
                    token = event.get("response", "")
                    if token:
                        full_text += token
                        on_chunk(token)
                on_complete(full_text)
                return
            except Exception as exc:
                logger.warning("Error en Ollama SDK: %s", exc)

        try:
            response = requests.post(
                f"{self.host}/v1/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            if response.ok:
                text = response.json().get("completion", "")
                on_chunk(text)
                on_complete(text)
            else:
                on_error(f"Ollama HTTP error {response.status_code}")
        except Exception as exc:
            on_error(str(exc))

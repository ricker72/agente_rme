"""
ollama_client.py
Comunicación con Ollama para generar scripts Lua válidos para OpenTibiaBR RME.
"""
import json
from typing import Callable, Optional

# Try official SDK first
try:
    import ollama as _ollama_sdk
    _SDK = True
except ImportError:
    _SDK = False

import requests

OLLAMA_BASE = "http://localhost:11434"
TIMEOUT = 10

RME_SYSTEM_PROMPT = """Genera exclusivamente scripts Lua compatibles con OpenTibiaBR Remere's Map Editor.

Usa únicamente:

app.transaction()
app.hasMap()

local map = app.map

map:getOrCreateTile()

tile.ground
tile:addItem()
tile:borderize()
tile:setSpawn()
tile:setCreature()

No utilices nunca:

Map.addItem
Map.addCreature
Map.addNpc
Map.setTile
Position
Game.createTile

Responde únicamente con el script Lua, sin explicaciones adicionales y sin bloques markdown.
"""


class OllamaClient:
    def __init__(self):
        self.client = _ollama_sdk if _SDK else None

    def check_ollama_alive(self) -> tuple[bool, str]:
        if self.client is not None:
            try:
                self.client.list()
                return True, "Ollama SDK activo."
            except Exception as exc:
                return False, f"SDK error: {exc}"

        try:
            response = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=TIMEOUT)
            if response.status_code == 200:
                return True, "Ollama HTTP activo."
            return False, f"Ollama respondió HTTP {response.status_code}"
        except requests.ConnectionError:
            return False, "No se pudo conectar a Ollama en localhost:11434. ¿Está iniciado?"
        except Exception as exc:
            return False, f"Error: {exc}"

    def list_models(self) -> list[str]:
        if self.client is not None:
            try:
                response = self.client.list()
                models = response.get("models", []) if isinstance(response, dict) else []
                return [m.get("name", "") for m in models if m.get("name")]
            except Exception:
                pass

        try:
            response = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def build_user_message(
        self,
        user_prompt: str,
        rag_context: str,
        knowledge_context: dict,
        monster_names: list[str],
        npc_names: list[str],
    ) -> str:
        monsters_str = ", ".join(monster_names[:20]) if monster_names else "Ninguno disponible"
        npcs_str = ", ".join(npc_names[:10]) if npc_names else "Ninguno disponible"
        knowledge_json = json.dumps(knowledge_context, ensure_ascii=False, indent=2)
        return (
            f"CONTEXTO DE DATOS DISPONIBLES:\n{rag_context}\n\n"
            f"CONTEXTO DE CONOCIMIENTO EXPERTO:\n{knowledge_json}\n\n"
            f"MONSTRUOS DISPONIBLES (usa estos nombres exactos):\n{monsters_str}\n\n"
            f"NPCs DISPONIBLES (usa estos nombres exactos):\n{npcs_str}\n\n"
            f"SOLICITUD DEL USUARIO:\n{user_prompt}\n\n"
            f"Genera un script Lua válido para OpenTibiaBR RME con esta información."
        )

    def generate_stream(
        self,
        model: str,
        user_message: str,
        on_chunk: Callable[[str], None],
        on_done: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        messages = [
            {"role": "system", "content": RME_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        if self.client is not None:
            self._stream_sdk(model, messages, on_chunk, on_done, on_error)
        else:
            self._stream_http(model, messages, on_chunk, on_done, on_error)

    def _stream_sdk(self, model, messages, on_chunk, on_done, on_error):
        try:
            full_text = []
            stream = _ollama_sdk.chat(
                model=model,
                messages=messages,
                stream=True,
                options={"temperature": 0.7, "num_predict": 2048},
            )
            for chunk in stream:
                if isinstance(chunk, dict):
                    delta = chunk.get("message", {}).get("content", "")
                else:
                    delta = getattr(getattr(chunk, "message", None), "content", "") or ""
                if delta:
                    full_text.append(delta)
                    on_chunk(delta)
            on_done("".join(full_text))
        except Exception as exc:
            on_error(f"SDK error: {exc}")

    def _stream_http(self, model, messages, on_chunk, on_done, on_error):
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.7, "num_predict": 2048},
        }
        try:
            with requests.post(
                f"{OLLAMA_BASE}/api/chat", json=payload, stream=True, timeout=120
            ) as response:
                if response.status_code != 200:
                    on_error(f"Error de Ollama: HTTP {response.status_code} — {response.text[:200]}")
                    return
                full_text = []
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            full_text.append(delta)
                            on_chunk(delta)
                        if chunk.get("done"):
                            on_done("".join(full_text))
                            return
                    except json.JSONDecodeError:
                        continue
        except requests.ConnectionError:
            on_error("Conexión perdida con Ollama. ¿Sigue en ejecución?")
        except requests.Timeout:
            on_error("Tiempo de espera agotado. El modelo tardó demasiado.")
        except Exception as exc:
            on_error(f"Error inesperado: {exc}")

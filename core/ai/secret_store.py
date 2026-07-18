"""Current-user encrypted credentials for optional AI providers on Windows."""

from __future__ import annotations

import base64
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Any


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


class AISecretStore:
    """Store API keys with Windows DPAPI; environment variables take precedence."""

    ENV_NAMES = {
        "paxsenix": "PAXSENIX_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "custom": "RME_CUSTOM_AI_API_KEY",
        "ollama": "OLLAMA_API_KEY",
    }

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("LOCALAPPDATA", Path.home())) / "AgenteRME"
        self.path = Path(path) if path is not None else base / "ai_credentials.json"

    def get(self, provider: str) -> str:
        env_name = self.ENV_NAMES.get(provider, "")
        if env_name and os.getenv(env_name, "").strip():
            return os.environ[env_name].strip()
        if os.name != "nt" or not self.path.is_file():
            return ""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            encrypted = base64.b64decode(str(payload.get(provider, "")), validate=True)
            return self._unprotect(encrypted).decode("utf-8")
        except (OSError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return ""

    def set(self, provider: str, secret: str) -> None:
        if provider not in self.ENV_NAMES:
            raise ValueError("unsupported provider")
        value = str(secret).strip()
        if len(value) < 12:
            raise ValueError("credential is too short")
        if os.name != "nt":
            raise OSError("persistent credentials require Windows DPAPI; use an environment variable")
        payload = self._load()
        payload[provider] = base64.b64encode(self._protect(value.encode("utf-8"))).decode("ascii")
        self._write(payload)

    def delete(self, provider: str) -> None:
        payload = self._load()
        if provider in payload:
            del payload[provider]
            self._write(payload)

    def configured(self, provider: str) -> bool:
        return bool(self.get(provider))

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.path)

    @staticmethod
    def _blob(data: bytes) -> tuple[_DataBlob, Any]:
        buffer = ctypes.create_string_buffer(data)
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer

    @classmethod
    def _protect(cls, data: bytes) -> bytes:
        source, source_buffer = cls._blob(data)
        output = _DataBlob()
        crypt32 = ctypes.windll.crypt32
        if not crypt32.CryptProtectData(ctypes.byref(source), "Agente RME AI", None, None, None, 0x1, ctypes.byref(output)):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(output.pbData)
            del source_buffer

    @classmethod
    def _unprotect(cls, data: bytes) -> bytes:
        source, source_buffer = cls._blob(data)
        output = _DataBlob()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0x1, ctypes.byref(output)):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(output.pbData)
            del source_buffer


__all__ = ["AISecretStore"]

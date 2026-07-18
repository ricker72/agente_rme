"""
core/config_manager.py

ConfigManager — centralized configuration for Agente RME v1.0.0 GA.

Features:
  - Hot reload from disk
  - Validation against schema
  - Environment profiles (default, development, production)
  - Environment variable overrides (RME_*)
  - Singleton access via ConfigManager.instance()

Usage:
    from core.config_manager import ConfigManager
    cm = ConfigManager(profile="production")
    val = cm.get("generation.max_tiles")
    cm.set("ollama.model", "qwen3:14b")
    cm.reload()
    cm.export("config/runtime.yaml")
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore

    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False


# Schema — minimal validation for top-level keys
_SCHEMA_KEYS = {
    "environment": str,
    "debug": bool,
    "log_level": str,
    "profile": str,
    "generation": dict,
    "lua": dict,
    "otbm": dict,
    "quality": dict,
    "ai": dict,
    "ollama": dict,
    "paths": dict,
    "cache": dict,
    "benchmark": dict,
    "observability": dict,
    "recovery": dict,
}

_VALID_PROFILES = ("default", "development", "production")


class ConfigError(Exception):
    pass


class ConfigManager:
    """Centralized configuration manager."""

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __init__(self, profile: str = "default", config_dir: str = "config") -> None:
        if profile not in _VALID_PROFILES:
            raise ConfigError(f"invalid profile: {profile!r}")
        self._profile = profile
        self._config_dir = Path(config_dir)
        self._data: Dict[str, Any] = {}
        self._mtime: Dict[str, float] = {}
        self._watchers: List[Path] = []
        self._load_all()

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def instance(cls, profile: Optional[str] = None) -> "ConfigManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(profile=profile or "default")
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        # 1. default
        default_path = self._config_dir / "default.yaml"
        self._data = self._load_yaml(default_path) if default_path.exists() else {}
        # 2. environment profile
        profile_path = self._config_dir / f"{self._profile}.yaml"
        if profile_path.exists():
            merged = self._load_yaml(profile_path)
            self._data = _deep_merge(self._data, merged)
        # 3. environment variables
        self._apply_env_overrides()
        # 4. validate
        self._validate()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not _HAVE_YAML:
            raise ConfigError("PyYAML is not installed; cannot load YAML config")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            raise ConfigError(f"failed to load {path}: {e}")
        if not isinstance(data, dict):
            raise ConfigError(f"invalid YAML in {path}: top-level must be a mapping")
        self._mtime[str(path)] = path.stat().st_mtime
        return data

    def _apply_env_overrides(self) -> None:
        prefix = "RME_"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            upper = key.upper()
            if upper.endswith(("_API_KEY", "_TOKEN", "_SECRET", "_PASSWORD")):
                continue
            sub = key[len(prefix) :].lower()
            self._set_by_path(self._data, sub, _coerce_env(value))

    @staticmethod
    def _set_by_path(data: Dict[str, Any], dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        cur = data
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        for k, expected in _SCHEMA_KEYS.items():
            if k in self._data and not isinstance(self._data[k], expected):
                raise ConfigError(
                    f"config key '{k}' has wrong type: expected {expected.__name__}, got {type(self._data[k]).__name__}"
                )

    def validate(self) -> List[str]:
        """Return a list of human-readable issues (empty if valid)."""
        issues: List[str] = []
        for k, expected in _SCHEMA_KEYS.items():
            if k in self._data and not isinstance(self._data[k], expected):
                issues.append(
                    f"key '{k}' expected {expected.__name__}, got {type(self._data[k]).__name__}"
                )
        if self._data.get("log_level", "INFO") not in (
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
        ):
            issues.append("log_level must be one of DEBUG/INFO/WARNING/ERROR")
        gen = self._data.get("generation", {})
        if isinstance(gen, dict):
            if "max_tiles" in gen and not isinstance(gen["max_tiles"], int):
                issues.append("generation.max_tiles must be int")
            if "min_level" in gen and "max_level" in gen:
                if gen["min_level"] >= gen["max_level"]:
                    issues.append("generation.min_level must be < max_level")
        return issues

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get(self, dotted: str, default: Any = None) -> Any:
        parts = dotted.split(".")
        cur: Any = self._data
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return default
        return cur

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        cur = self._data
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value

    def all(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._data, default=str))

    def profile(self) -> str:
        return self._profile

    # ------------------------------------------------------------------
    # Hot reload
    # ------------------------------------------------------------------

    def reload(self) -> bool:
        """Reload from disk; returns True if anything changed."""
        default_path = self._config_dir / "default.yaml"
        profile_path = self._config_dir / f"{self._profile}.yaml"
        changed = False
        for p in (default_path, profile_path):
            if not p.exists():
                continue
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if self._mtime.get(str(p)) != m:
                self._load_all()
                changed = True
                break
        return changed

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, path: str) -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if _HAVE_YAML and out.suffix.lower() in (".yaml", ".yml"):
            with open(out, "w", encoding="utf-8") as f:
                yaml.safe_dump(self._data, f, sort_keys=False, allow_unicode=True)
        else:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        return str(out)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _coerce_env(value: str) -> Any:
    """Best-effort env var coercion (bool, int, float, str)."""
    low = value.strip().lower()
    if low in ("true", "yes", "1", "on"):
        return True
    if low in ("false", "no", "0", "off"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value

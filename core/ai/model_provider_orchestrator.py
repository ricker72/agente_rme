"""Bounded cloud/local model proposals for the deterministic Mapper Planner."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from core.config_manager import ConfigManager
from core.ai.secret_store import AISecretStore


_ALLOWED_KEYS = {
    "city_scale",
    "hunt_scale",
    "route_width",
    "water_margin",
    "nature_density",
    "terrain_irregularity",
    "verticality",
}
_BOUNDS = {
    "city_scale": (0.75, 1.25),
    "hunt_scale": (0.75, 1.25),
    "route_width": (2.0, 4.0),
    "water_margin": (18.0, 40.0),
    "nature_density": (0.10, 0.90),
    "terrain_irregularity": (0.10, 0.90),
    "verticality": (0.0, 1.0),
}
_SYSTEM_PROMPT = """You are the semantic planning layer of an OpenTibia RME map generator.
Return one JSON object only. The certified_material_brief is a read-only allowlist built
from the installed Canary/RME materials database. Its item and border IDs are technical
evidence only. Never return IDs, source coordinates, Lua, SQL, paths, OTBM nodes, or
copied map geometry. Select only exact material keys present in allowed_material_keys.
The deterministic RME Brush Engine resolves item chance, AutoBorder orientation, wall
parts, doors, windows, neighbor post-processing, draw order and final OTBM writes.
certified_rme_grammar describes the exact neighbor bit contract and certified operation
pipeline extracted from RME brush_tables.cpp and brush source. Use it to reason about
topology and sequencing, but never emulate raw item placement or override the Brush Engine.
The certified_reference_brief contains measured, coordinate-free facts from world.otbm
and reference maps. Learn density, transitions, floor usage and structural proportions,
but create new topology and never reconstruct any source footprint.
validated_experience_rules contains lessons from maps that passed every automatic gate
and human Canary validation. Apply relevant positive rules and avoid negative constraints.
planner_feedback is a bounded correction from the deterministic Planner. Address every
listed issue in the next response and use its coordinate-free reference facts as measured
style evidence, never as geometry to reproduce. Keep all preserve_zone_roles and
preserve_rules while correcting the rejected parts.

Schema:
{
  "summary": "short original design intent",
  "parameters": {
    "city_scale": 0.75..1.25,
    "hunt_scale": 0.75..1.25,
    "route_width": 2..4,
    "water_margin": 18..40,
    "nature_density": 0.10..0.90,
    "terrain_irregularity": 0.10..0.90,
    "verticality": 0..1
  },
  "architecture_rules": ["abstract rule", "..."],
  "biome_rules": ["abstract rule", "..."],
  "material_intents": [
    {
      "zone_role": "city|hunt|coast|interior|mountain|road|nature",
      "ground_key": "exact allowed ground key or empty",
      "wall_key": "exact allowed wall key or empty",
      "doodad_keys": ["exact allowed doodad key"],
      "density": 0.0..1.0,
      "reason": "short contextual reason"
    }
  ],
  "negative_constraints": ["abstract constraint", "..."],
  "qa_intent": ["check", "..."]
}
All lists contain at most 12 concise strings. The layout must be original."""

_VIEWPORT_SYSTEM_PROMPT = """You review a live OpenTibia RME viewport for the Mapper Planner.
The deterministic viewport_observations are authoritative and contain no image pixels or
source geometry. Return one JSON object only. Do not invent item IDs, coordinates, assets,
brushes, OTBM data or implementation details. Refer only to supplied issue_id values and
exact keys in allowed_material_keys. Prefer an alert when intent is ambiguous. A repair is
only a staged proposal; it is never applied automatically.

Schema:
{
  "assessment": "short visual/structural assessment",
  "repairs": [{"issue_id": "supplied id", "repair_kind": "REORDER_STACK|REAPPLY_GROUND_BRUSH|REBUILD_AUTOBORDER|REBUILD_WALL_NEIGHBORS|RECONNECT_PATH|REPAIR_VERTICAL_LINK|NONE", "material_key": "allowed key or empty", "reason": "short reason"}],
  "alerts": [{"issue_id": "supplied id", "message": "short user-facing alert"}],
  "prompt_adjustments": ["concise suggested prompt constraint"]
}
At most 16 repairs, 16 alerts and 8 prompt adjustments."""


@dataclass(frozen=True)
class _Provider:
    name: str
    base_url: str
    model: str
    api_key_env: str = ""
    kind: str = "openai"
    enabled: bool = True


class ModelProviderOrchestrator:
    """Fail over across PaxSenix, OpenRouter, custom OpenAI APIs and Ollama."""

    _circuit_lock = threading.Lock()
    _failures: dict[str, int] = {}
    _open_until: dict[str, float] = {}

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        try:
            self.config = ConfigManager(profile=os.getenv("RME_PROFILE", "default"), config_dir=str(self.root / "config"))
        except (OSError, ValueError, RuntimeError):
            self.config = None
        self.enabled = self._get("ai.enabled", True)
        self.timeout = max(3.0, min(120.0, float(self._get("ai.timeout_seconds", 35))))
        self.max_input_chars = max(512, min(50000, int(self._get("ai.max_input_chars", 12000))))
        self.max_output_tokens = max(256, min(8192, int(self._get("ai.max_output_tokens", 1800))))
        self.secret_store = AISecretStore()
        self.providers = self._providers()
        self.last_result: dict[str, Any] = {"status": "NOT_RUN"}

    def _get(self, key: str, default: Any) -> Any:
        return self.config.get(key, default) if self.config is not None else default

    def _providers(self) -> list[_Provider]:
        ollama_direct = self.secret_store.configured("ollama")
        ollama_base = (
            str(self._get("ai.providers.ollama.cloud_base_url", "https://ollama.com")).rstrip("/")
            if ollama_direct
            else os.getenv("OLLAMA_HOST", str(self._get("ai.providers.ollama.base_url", self._get("ollama.host", "http://127.0.0.1:11434")))).rstrip("/")
        )
        ollama_model = (
            os.getenv("OLLAMA_CLOUD_MODEL", str(self._get("ai.providers.ollama.cloud_model", "glm-5.2")))
            if ollama_direct
            else os.getenv("OLLAMA_MODEL", str(self._get("ai.providers.ollama.model", self._get("ollama.model", "qwen3:8b"))))
        )
        definitions = {
            "paxsenix": _Provider(
                "paxsenix",
                str(self._get("ai.providers.paxsenix.base_url", "https://api.paxsenix.org/v1")).rstrip("/"),
                os.getenv("PAXSENIX_MODEL", str(self._get("ai.providers.paxsenix.model", "gpt-5-nano"))),
                "PAXSENIX_API_KEY",
            ),
            "openrouter": _Provider(
                "openrouter",
                str(self._get("ai.providers.openrouter.base_url", "https://openrouter.ai/api/v1")).rstrip("/"),
                os.getenv("OPENROUTER_MODEL", str(self._get("ai.providers.openrouter.model", ""))),
                "OPENROUTER_API_KEY",
            ),
            "custom": _Provider(
                "custom",
                os.getenv("RME_CUSTOM_AI_BASE_URL", str(self._get("ai.providers.custom.base_url", ""))).rstrip("/"),
                os.getenv("RME_CUSTOM_AI_MODEL", str(self._get("ai.providers.custom.model", ""))),
                "RME_CUSTOM_AI_API_KEY",
            ),
            "ollama": _Provider(
                "ollama",
                ollama_base,
                ollama_model,
                "OLLAMA_API_KEY" if ollama_direct else "",
                kind="ollama",
            ),
        }
        raw_order = os.getenv("RME_AI_PROVIDER_ORDER", "")
        order = [part.strip().lower() for part in raw_order.split(",") if part.strip()]
        if not order:
            configured_order = self._get("ai.provider_order", ["paxsenix", "openrouter", "custom", "ollama"])
            if isinstance(configured_order, str):
                order = [part.strip().lower() for part in configured_order.split(",") if part.strip()]
            else:
                order = [str(part).strip().lower() for part in configured_order]
        return [definitions[name] for name in order if name in definitions]

    def propose(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return self._finish("DISABLED", errors=[])
        objective_text = str(objective)[: self.max_input_chars]
        context_budget = max(0, self.max_input_chars - len(objective_text) - 256)
        user_payload = {
            "objective": objective_text,
            "abstract_context": _fit_context_budget(_safe_context(context or {}), context_budget),
        }
        selected_mode = str(mode or self._get("ai.default_mode", "auto")).strip().lower()
        if selected_mode in {"triple", "triple_consensus"}:
            return self._propose_consensus(user_payload)
        if selected_mode in {"paxsenix", "openrouter", "custom", "ollama"}:
            selected = [provider for provider in self.providers if provider.name == selected_mode]
            if not selected:
                return self._finish("DETERMINISTIC_FALLBACK", errors=[{"provider": selected_mode, "code": "NOT_AVAILABLE"}])
            return self._propose_sequence(selected, user_payload)
        return self._propose_sequence(self.providers, user_payload)

    def review_viewport(
        self,
        observations: list[dict[str, Any]],
        *,
        context: dict[str, Any] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return self._finish("DISABLED", errors=[])
        bounded = [
            {
                key: item.get(key)
                for key in ("issue_id", "code", "severity", "category", "message", "evidence", "repair_kind", "auto_repairable", "prompt_hint")
            }
            for item in observations[:64] if isinstance(item, dict)
        ]
        safe = _safe_context(context or {})
        user_payload = {"viewport_observations": bounded, "abstract_context": safe}
        selected_mode = str(mode or self._get("ai.default_mode", "auto")).strip().lower()
        providers = self.providers
        if selected_mode in {"triple", "triple_consensus"}:
            return self._review_viewport_consensus(user_payload)
        if selected_mode in {"paxsenix", "openrouter", "custom", "ollama"}:
            providers = [provider for provider in providers if provider.name == selected_mode]
        errors: list[dict[str, str]] = []
        for provider in providers:
            review, error, actual_model = self._attempt_viewport_provider(provider, user_payload)
            if error:
                errors.append(error)
                continue
            return self._finish("PASS", provider=provider.name, model=actual_model or provider.model, guidance=review, errors=errors)
        return self._finish("DETERMINISTIC_FALLBACK", errors=errors)

    def _review_viewport_consensus(self, user_payload: dict[str, Any]) -> dict[str, Any]:
        candidates = [provider for provider in self.providers if provider.name in {"paxsenix", "openrouter", "ollama"}]
        successes: list[tuple[_Provider, dict[str, Any], str]] = []
        errors: list[dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="RMEViewportAI") as executor:
            futures = {executor.submit(self._attempt_viewport_provider, provider, user_payload): provider for provider in candidates}
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    review, error, model = future.result()
                except Exception as exc:  # noqa: BLE001
                    review, error, model = None, {"provider": provider.name, "code": type(exc).__name__}, ""
                if review is not None:
                    successes.append((provider, review, model or provider.model))
                elif error:
                    errors.append(error)
        if not successes:
            return self._finish("DETERMINISTIC_FALLBACK", errors=errors)
        result = self._finish(
            "MULTI_MODEL_CONSENSUS" if len(successes) >= 2 else "PARTIAL_CONSENSUS",
            provider="triple_consensus",
            model=" + ".join(item[2] for item in successes),
            guidance=_merge_viewport_reviews([item[1] for item in successes]),
            errors=errors,
        )
        result["contributors"] = [item[0].name for item in successes]
        return result

    def _attempt_viewport_provider(
        self, provider: _Provider, user_payload: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, str] | None, str]:
        if not self._configured(provider):
            return None, {"provider": provider.name, "code": "NOT_CONFIGURED"}, ""
        if self._circuit_is_open(provider.name):
            return None, {"provider": provider.name, "code": "CIRCUIT_OPEN"}, ""
        try:
            raw, actual_model = self._request(provider, user_payload, system_prompt=_VIEWPORT_SYSTEM_PROMPT)
            issue_ids = {str(item.get("issue_id", "")) for item in user_payload["viewport_observations"]}
            repair_permissions = {
                str(item.get("issue_id", "")): (
                    str(item.get("repair_kind", "NONE")) if item.get("auto_repairable") else "NONE"
                )
                for item in user_payload["viewport_observations"]
            }
            allowed_keys = set(
                user_payload.get("abstract_context", {}).get("certified_material_brief", {}).get("allowed_material_keys", ())
            )
            review = _validate_viewport_review(
                _extract_json(raw), issue_ids=issue_ids,
                allowed_material_keys=allowed_keys, repair_permissions=repair_permissions,
            )
        except (requests.RequestException, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._record_failure(provider.name)
            return None, {"provider": provider.name, "code": type(exc).__name__}, ""
        self._record_success(provider.name)
        return review, None, actual_model

    def _propose_sequence(self, providers: list[_Provider], user_payload: dict[str, Any]) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        for provider in providers:
            guidance, error, actual_model = self._attempt_provider(provider, user_payload)
            if error is not None:
                errors.append(error)
                continue
            return self._finish(
                "PASS",
                provider=provider.name,
                model=actual_model or provider.model,
                guidance=guidance,
                errors=errors,
            )
        return self._finish("DETERMINISTIC_FALLBACK", errors=errors)

    def _propose_consensus(self, user_payload: dict[str, Any]) -> dict[str, Any]:
        candidates = [
            provider for provider in self.providers
            if provider.name in {"paxsenix", "openrouter", "ollama"}
        ]
        successes: list[tuple[_Provider, dict[str, Any], str]] = []
        errors: list[dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="RMEAI") as executor:
            futures = {executor.submit(self._attempt_provider, provider, user_payload): provider for provider in candidates}
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    guidance, error, actual_model = future.result()
                except Exception as exc:  # noqa: BLE001 - provider boundary is isolated.
                    guidance, error, actual_model = None, {"provider": provider.name, "code": type(exc).__name__}, ""
                if guidance is not None:
                    successes.append((provider, guidance, actual_model or provider.model))
                elif error is not None:
                    errors.append(error)
        if not successes:
            return self._finish("DETERMINISTIC_FALLBACK", errors=errors)
        guidance = _merge_consensus([item[1] for item in successes])
        minimum = max(2, min(3, int(self._get("ai.triple_min_success", 2))))
        status = "MULTI_MODEL_CONSENSUS" if len(successes) >= minimum else "PARTIAL_CONSENSUS"
        result = self._finish(
            status,
            provider="triple_consensus",
            model=" + ".join(item[2] for item in successes),
            guidance=guidance,
            errors=errors,
        )
        result["contributors"] = [item[0].name for item in successes]
        result["agreement"] = {"successful": len(successes), "requested": len(candidates), "minimum": minimum}
        self.last_result = dict(result)
        return result

    def _attempt_provider(
        self,
        provider: _Provider,
        user_payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, str] | None, str]:
        if not self._configured(provider):
            return None, {"provider": provider.name, "code": "NOT_CONFIGURED"}, ""
        if self._circuit_is_open(provider.name):
            return None, {"provider": provider.name, "code": "CIRCUIT_OPEN"}, ""
        try:
            raw, actual_model = self._request(provider, user_payload)
            allowed_keys = set(
                user_payload.get("abstract_context", {})
                .get("certified_material_brief", {})
                .get("allowed_material_keys", ())
            )
            try:
                guidance = _validate_guidance(_extract_json(raw), allowed_material_keys=allowed_keys)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as validation_error:
                retry_payload = json.loads(json.dumps(user_payload, ensure_ascii=True, default=str))
                retry_payload.setdefault("abstract_context", {})["planner_feedback"] = {
                    "round": 0,
                    "issues": [{
                        "code": "MODEL_RESPONSE_INVALID",
                        "message": "The previous response failed the certified contract.",
                        "correction": str(validation_error)[:240],
                    }],
                    "reference_facts": [],
                    "instruction": "Return a corrected JSON object using only the certified allowlist.",
                }
                raw, actual_model = self._request(provider, retry_payload)
                guidance = _validate_guidance(_extract_json(raw), allowed_material_keys=allowed_keys)
        except (requests.RequestException, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._record_failure(provider.name)
            return None, {"provider": provider.name, "code": type(exc).__name__}, ""
        self._record_success(provider.name)
        return guidance, None, actual_model

    def _configured(self, provider: _Provider) -> bool:
        if not provider.enabled or not provider.base_url or not provider.model:
            return False
        return provider.kind == "ollama" or self.secret_store.configured(provider.name)

    def _request(
        self, provider: _Provider, user_payload: dict[str, Any], *, system_prompt: str = _SYSTEM_PROMPT
    ) -> tuple[str, str]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True, separators=(",", ":"))},
        ]
        if provider.kind == "ollama":
            headers: dict[str, str] = {}
            api_key = self.secret_store.get("ollama")
            if provider.base_url.startswith("https://ollama.com"):
                if not api_key:
                    raise ValueError("Ollama cloud credential is unavailable")
                headers["Authorization"] = f"Bearer {api_key}"
            direct_cloud = provider.base_url.startswith("https://ollama.com")
            fallback_key = "ai.providers.ollama.cloud_fallback_models" if direct_cloud else "ai.providers.ollama.fallback_models"
            configured_fallbacks = self._get(fallback_key, ["nemotron-3-super"] if direct_cloud else ["nemotron-3-super:cloud"])
            if isinstance(configured_fallbacks, str):
                fallback_models = [item.strip() for item in configured_fallbacks.split(",") if item.strip()]
            else:
                fallback_models = [str(item).strip() for item in configured_fallbacks if str(item).strip()]
            last_error: requests.HTTPError | None = None
            for model in dict.fromkeys([provider.model, *fallback_models]):
                response = requests.post(
                    f"{provider.base_url}/api/chat",
                    headers=headers,
                    json={"model": model, "messages": messages, "stream": False, "format": "json", "options": {"temperature": 0.35, "num_predict": self.max_output_tokens}},
                    timeout=self.timeout,
                )
                try:
                    response.raise_for_status()
                except requests.HTTPError as exc:
                    last_error = exc
                    continue
                return str(response.json()["message"]["content"]), model
            if last_error is not None:
                raise last_error
            raise ValueError("Ollama model list is empty")
        api_key = self.secret_store.get(provider.name)
        if not api_key:
            raise ValueError("provider credential is unavailable")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider.name == "openrouter":
            headers["X-OpenRouter-Title"] = "Agente RME"
        payload = {
            "model": provider.model,
            "messages": messages,
            "temperature": 0.35,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(f"{provider.base_url}/chat/completions", headers=headers, json=payload, timeout=self.timeout)
        if response.status_code in {400, 404, 422}:
            # Some OpenAI-compatible services do not implement response_format.
            payload.pop("response_format", None)
            response = requests.post(f"{provider.base_url}/chat/completions", headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]), provider.model

    @classmethod
    def _circuit_is_open(cls, name: str) -> bool:
        with cls._circuit_lock:
            return cls._open_until.get(name, 0.0) > time.monotonic()

    @classmethod
    def _record_failure(cls, name: str) -> None:
        with cls._circuit_lock:
            failures = cls._failures.get(name, 0) + 1
            cls._failures[name] = failures
            if failures >= 3:
                cls._open_until[name] = time.monotonic() + 60.0

    @classmethod
    def _record_success(cls, name: str) -> None:
        with cls._circuit_lock:
            cls._failures.pop(name, None)
            cls._open_until.pop(name, None)

    def _finish(self, status: str, *, errors: list[dict[str, str]], provider: str = "", model: str = "", guidance: dict[str, Any] | None = None) -> dict[str, Any]:
        result = {
            "status": status,
            "provider": provider,
            "model": model,
            "guidance": guidance or {},
            "errors": errors,
            "secrets_exposed": False,
            "writes_tiles_directly": False,
        }
        self.last_result = result
        return dict(result)

    def audit(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "provider_order": [provider.name for provider in self.providers],
            "configured": {provider.name: self._configured(provider) for provider in self.providers},
            "ollama_transport": next(("CLOUD_API" if provider.base_url.startswith("https://ollama.com") else "LOCAL_API" for provider in self.providers if provider.name == "ollama"), "UNAVAILABLE"),
            "last_status": self.last_result.get("status", "NOT_RUN"),
            "last_provider": self.last_result.get("provider", ""),
            "last_contributors": self.last_result.get("contributors", []),
            "secrets_in_config": False,
            "semantic_only": True,
        }


def _safe_context(context: dict[str, Any]) -> dict[str, Any]:
    allowed = {"positive_rule_count", "negative_constraint_count", "reference_names", "town_names", "visual_tags"}
    result = {key: value for key, value in context.items() if key in allowed}
    brief = context.get("certified_material_brief")
    if isinstance(brief, dict) and brief.get("status") == "CERTIFIED" and brief.get("all_ids_certified") is True:
        result["certified_material_brief"] = _safe_material_brief(brief)
    reference_brief = context.get("certified_reference_brief")
    if isinstance(reference_brief, dict) and reference_brief.get("status") == "CERTIFIED":
        result["certified_reference_brief"] = _safe_reference_brief(reference_brief)
    technical_grammar = context.get("certified_rme_grammar")
    if isinstance(technical_grammar, dict) and technical_grammar.get("status") == "CERTIFIED":
        result["certified_rme_grammar"] = _safe_rme_grammar(technical_grammar)
    experience = context.get("validated_experience_rules")
    if isinstance(experience, dict) and experience.get("requires_human_validation_for_positive_learning") is True:
        result["validated_experience_rules"] = {
            "positive_rules": _safe_learned_rules(experience.get("positive_rules", ())),
            "negative_constraints": _safe_learned_rules(experience.get("negative_constraints", ())),
            "human_validated": True,
        }
    for key, item_limit in (
        ("editor_runtime_rules", 16),
        ("parsed_brush_grammar", 8),
        ("tileset_knowledge", 8),
    ):
        value = context.get(key)
        if isinstance(value, (list, tuple)):
            result[key] = [_safe_bounded_value(item) for item in list(value)[:item_limit]]
    feedback = context.get("planner_feedback")
    if isinstance(feedback, dict):
        result["planner_feedback"] = {
            "round": max(0, min(3, int(feedback.get("round", 0)))),
            "issues": [
                {
                    "code": str(item.get("code", ""))[:80],
                    "message": str(item.get("message", ""))[:300],
                    "correction": str(item.get("correction", ""))[:300],
                }
                for item in list(feedback.get("issues", ()))[:8] if isinstance(item, dict)
            ],
            "reference_facts": [str(item)[:400] for item in list(feedback.get("reference_facts", ()))[:8]],
            "instruction": str(feedback.get("instruction", ""))[:300],
            "preserve_zone_roles": [str(item)[:80] for item in list(feedback.get("preserve_zone_roles", ()))[:12]],
            "preserve_rules": [str(item)[:240] for item in list(feedback.get("preserve_rules", ()))[:12]],
        }
    return result


def _safe_bounded_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 4:
        return str(value)[:240]
    if isinstance(value, dict):
        return {
            str(key)[:80]: _safe_bounded_value(item, depth=depth + 1)
            for key, item in list(value.items())[:32]
            if not any(secret in str(key).casefold() for secret in ("token", "secret", "api_key", "password"))
        }
    if isinstance(value, (list, tuple)):
        return [_safe_bounded_value(item, depth=depth + 1) for item in list(value)[:32]]
    if isinstance(value, str):
        return value[:600]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:240]


def _fit_context_budget(context: dict[str, Any], budget: int) -> dict[str, Any]:
    if budget <= 2:
        return {}
    priority = (
        "certified_material_brief",
        "certified_rme_grammar",
        "parsed_brush_grammar",
        "tileset_knowledge",
        "editor_runtime_rules",
        "validated_experience_rules",
        "certified_reference_brief",
        "planner_feedback",
        "positive_rule_count",
        "negative_constraint_count",
        "reference_names",
        "town_names",
        "visual_tags",
    )
    fitted: dict[str, Any] = {}
    for key in priority:
        if key not in context:
            continue
        candidate = dict(fitted)
        candidate[key] = context[key]
        if len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":"))) <= budget:
            fitted = candidate
            continue
        remaining = budget - len(json.dumps(fitted, ensure_ascii=True, separators=(",", ":"))) - len(key) - 8
        reduced = _truncate_value_to_budget(context[key], remaining)
        if reduced not in (None, {}, []):
            candidate = dict(fitted)
            candidate[key] = reduced
            if len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":"))) <= budget:
                fitted = candidate
    return fitted


def _truncate_value_to_budget(value: Any, budget: int) -> Any:
    if budget < 16:
        return None
    if isinstance(value, list):
        result = []
        for item in value:
            candidate = result + [item]
            if len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":"))) > budget:
                break
            result = candidate
        return result
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            candidate = dict(result)
            candidate[key] = item
            if len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":"))) <= budget:
                result = candidate
                continue
            remaining = budget - len(json.dumps(result, ensure_ascii=True, separators=(",", ":"))) - len(str(key)) - 8
            nested = _truncate_value_to_budget(item, remaining)
            if nested not in (None, {}, []):
                candidate = dict(result)
                candidate[key] = nested
                if len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":"))) <= budget:
                    result = candidate
        return result
    if isinstance(value, str):
        return value[: max(0, budget - 2)]
    return value


def _safe_material_brief(brief: dict[str, Any]) -> dict[str, Any]:
    brushes = []
    allowed_keys: list[str] = []
    for raw in list(brief.get("brushes", ()))[:20]:
        if not isinstance(raw, dict):
            continue
        key = str(raw.get("key", ""))[:120]
        if not key or not re.fullmatch(r"[a-z]+/[a-z0-9-]+", key):
            continue
        allowed_keys.append(key)
        entry = {
            "key": key,
            "name": str(raw.get("name", ""))[:120],
            "type": str(raw.get("type", ""))[:24],
            "look_id": int(raw.get("look_id", 0)),
            "z_order": int(raw.get("z_order", 0)),
            "items": [
                {"id": int(item.get("id", 0)), "chance": int(item.get("chance", 0))}
                for item in list(raw.get("items", ()))[:8] if isinstance(item, dict)
            ],
        }
        if entry["type"] == "ground":
            entry["autoborders"] = list(raw.get("autoborders", ()))[:1]
        if entry["type"] == "wall":
            entry["neighbor_parts"] = list(raw.get("neighbor_parts", ()))[:8]
        if raw.get("placement"):
            entry["placement"] = str(raw["placement"])[:160]
        brushes.append(entry)
    return {
        "status": "CERTIFIED",
        "source": str(brief.get("source", ""))[:160],
        "catalog_version": str(brief.get("catalog_version", ""))[:64],
        "catalog_hash": str(brief.get("catalog_hash", ""))[:64],
        "all_ids_certified": True,
        "placement_authority": "RME Brush Engine",
        "allowed_material_keys": allowed_keys,
        "brushes": brushes,
        "reference_profiles": list(brief.get("reference_profiles", ()))[:3],
        "constraints": [str(item)[:240] for item in list(brief.get("constraints", ()))[:8]],
    }


def _safe_rme_grammar(grammar: dict[str, Any]) -> dict[str, Any]:
    """Bound exact engine grammar while retaining the mathematics models need."""
    operations = []
    for raw in list(grammar.get("operation_grammar", ()))[:12]:
        if not isinstance(raw, dict):
            continue
        body = raw.get("grammar", {})
        if not isinstance(body, dict):
            continue
        operations.append({
            "domain": str(raw.get("domain", ""))[:48],
            "rule": str(raw.get("rule", ""))[:96],
            "grammar": {
                key: value for key, value in body.items()
                if key in {"steps", "invariants", "door_types", "transaction"}
            },
            "confidence": float(raw.get("confidence", 0.0)),
        })
    return {
        "status": "CERTIFIED",
        "schema_version": int(grammar.get("schema_version", 0)),
        "lookup_table_cardinality": {
            str(key)[:32]: int(value)
            for key, value in dict(grammar.get("lookup_table_cardinality", {})).items()
        },
        "neighbor_bit_contract": [
            {
                "system": str(row.get("system", ""))[:32], "bit": int(row.get("bit", 0)),
                "direction": str(row.get("direction", ""))[:24],
                "dx": int(row.get("dx", 0)), "dy": int(row.get("dy", 0)), "dz": int(row.get("dz", 0)),
            }
            for row in list(grammar.get("neighbor_bit_contract", ()))[:16] if isinstance(row, dict)
        ],
        "operation_grammar": operations,
        "materialization_authority": "RME Brush Engine",
        "geometry_copying_allowed": False,
    }


def _safe_reference_brief(brief: dict[str, Any]) -> dict[str, Any]:
    """The server built this object; retain only bounded statistical evidence."""
    return {
        "status": "CERTIFIED",
        "source": str(brief.get("source", ""))[:160],
        "brief_hash": str(brief.get("brief_hash", ""))[:64],
        "reference_maps": [_compact_reference_map(row) for row in list(brief.get("reference_maps", ()))[:2]],
        "world_towns": [_compact_world_town(row) for row in list(brief.get("world_towns", ()))[:2]],
        "facts_are_read_only": True,
        "source_coordinates_included": False,
        "source_geometry_included": False,
        "learning_policy": "derive proportions and grammar; generate new topology",
        "constraints": [str(item)[:240] for item in list(brief.get("constraints", ()))[:8]],
    }


def _compact_reference_map(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    floors = []
    for floor in list(row.get("floor_profiles", ()))[:2]:
        if not isinstance(floor, dict):
            continue
        floors.append({
            "floor": floor.get("floor"), "tile_count": floor.get("tile_count"),
            "item_density": floor.get("item_density"), "ground_diversity": floor.get("ground_diversity"),
            "top_materials": list(floor.get("top_materials", ()))[:4],
        })
    return {
        "name": str(row.get("name", ""))[:120],
        "tile_count": row.get("tile_count", 0),
        "floor_range": list(row.get("floor_range", ()))[:2],
        "floor_profiles": floors,
        "dominant_brushes": list(row.get("dominant_brushes", ()))[:6],
        "ground_transitions": list(row.get("ground_transitions", ()))[:4],
        "ground_border_mixes": list(row.get("ground_border_mixes", ()))[:4],
        "coordinates_included": False,
    }


def _compact_world_town(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    material_floors = []
    for floor in list(row.get("floor_material_usage", ()))[:2]:
        if isinstance(floor, dict):
            material_floors.append({"z": floor.get("z"), "top_materials": list(floor.get("top_materials", ()))[:4]})
    return {
        "town": str(row.get("town", ""))[:120],
        "content_floors": list(row.get("content_floors", ()))[:16],
        "structure_counts": row.get("structure_counts", {}),
        "floor_environment": list(row.get("floor_environment", ()))[:8],
        "structure_dimensions": list(row.get("structure_dimensions", ()))[:6],
        "floor_material_usage": material_floors,
        "coordinates_included": False,
    }


def _safe_learned_rules(rows: Any) -> list[dict[str, Any]]:
    output = []
    for row in list(rows)[:24]:
        if not isinstance(row, dict):
            continue
        rule = row.get("rule", {})
        if not isinstance(rule, dict):
            continue
        output.append({
            "category": str(row.get("category", ""))[:120],
            "confidence": round(max(0.0, min(1.0, float(row.get("confidence", 0.0)))), 4),
            "instruction": str(rule.get("instruction", ""))[:500],
        })
    return output


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model response contains no JSON object")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value


def _validate_guidance(value: dict[str, Any], *, allowed_material_keys: set[str] | None = None) -> dict[str, Any]:
    serialized = json.dumps(value, ensure_ascii=True)
    if len(serialized) > 30000:
        raise ValueError("model response is too large")
    forbidden = re.compile(r"(?:item|sprite|client|server)[_-]?id|(?:[A-Za-z]:\\|/home/)|\b(?:SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
    if forbidden.search(serialized):
        raise ValueError("model response contains forbidden implementation data")
    parameters: dict[str, float | int] = {}
    source_parameters = value.get("parameters", {})
    if not isinstance(source_parameters, dict):
        raise ValueError("parameters must be an object")
    for key in _ALLOWED_KEYS:
        if key not in source_parameters:
            continue
        number = float(source_parameters[key])
        low, high = _BOUNDS[key]
        number = max(low, min(high, number))
        parameters[key] = int(round(number)) if key in {"route_width", "water_margin"} else round(number, 3)
    result: dict[str, Any] = {"summary": str(value.get("summary", ""))[:500], "parameters": parameters}
    for key in ("architecture_rules", "biome_rules", "negative_constraints", "qa_intent"):
        raw = value.get(key, [])
        if not isinstance(raw, list):
            raise ValueError(f"{key} must be a list")
        result[key] = [str(item)[:240] for item in raw[:12] if str(item).strip()]
    allowed_material_keys = allowed_material_keys or set()
    intents = value.get("material_intents", [])
    if not isinstance(intents, list):
        raise ValueError("material_intents must be a list")
    validated_intents = []
    for raw in intents[:16]:
        if not isinstance(raw, dict):
            raise ValueError("material intent must be an object")
        ground_key = str(raw.get("ground_key", "")).strip()
        wall_key = str(raw.get("wall_key", "")).strip()
        doodad_keys = raw.get("doodad_keys", [])
        if not isinstance(doodad_keys, list):
            raise ValueError("doodad_keys must be a list")
        selected = [key for key in (ground_key, wall_key, *(str(item).strip() for item in doodad_keys[:8])) if key]
        if any(key not in allowed_material_keys for key in selected):
            raise ValueError("model selected a material outside the certified allowlist")
        if ground_key and not ground_key.startswith("ground/"):
            raise ValueError("ground_key must select a certified GroundBrush")
        if wall_key and not wall_key.startswith("wall/"):
            raise ValueError("wall_key must select a certified WallBrush")
        if any(not str(key).startswith(("doodad/", "carpet/", "table/")) for key in doodad_keys if str(key).strip()):
            raise ValueError("doodad_keys must select certified decoration brushes")
        validated_intents.append({
            "zone_role": str(raw.get("zone_role", ""))[:80],
            "ground_key": ground_key,
            "wall_key": wall_key,
            "doodad_keys": [str(item).strip() for item in doodad_keys[:8] if str(item).strip()],
            "density": round(max(0.0, min(1.0, float(raw.get("density", 0.5)))), 3),
            "reason": str(raw.get("reason", ""))[:240],
        })
    result["material_intents"] = validated_intents
    return result


def _validate_viewport_review(
    value: dict[str, Any], *, issue_ids: set[str], allowed_material_keys: set[str],
    repair_permissions: dict[str, str],
) -> dict[str, Any]:
    allowed_repairs = {
        "REORDER_STACK", "REAPPLY_GROUND_BRUSH", "REBUILD_AUTOBORDER",
        "REBUILD_WALL_NEIGHBORS", "RECONNECT_PATH", "REPAIR_VERTICAL_LINK", "NONE",
    }
    result: dict[str, Any] = {"assessment": str(value.get("assessment", ""))[:500]}
    repairs = []
    for raw in value.get("repairs", [])[:16]:
        if not isinstance(raw, dict):
            continue
        issue_id = str(raw.get("issue_id", ""))
        kind = str(raw.get("repair_kind", "NONE")).upper()
        material_key = str(raw.get("material_key", "")).strip()
        if issue_id not in issue_ids or kind not in allowed_repairs:
            raise ValueError("viewport review references an unknown issue or repair")
        permitted = repair_permissions.get(issue_id, "NONE")
        if permitted == "NONE":
            kind, material_key = "NONE", ""
        elif kind != permitted:
            raise ValueError("viewport repair exceeds deterministic permission")
        if material_key and material_key not in allowed_material_keys:
            raise ValueError("viewport review selected material outside certified allowlist")
        repairs.append({
            "issue_id": issue_id, "repair_kind": kind, "material_key": material_key,
            "reason": str(raw.get("reason", ""))[:240],
        })
    alerts = []
    for raw in value.get("alerts", [])[:16]:
        if not isinstance(raw, dict) or str(raw.get("issue_id", "")) not in issue_ids:
            continue
        alerts.append({"issue_id": str(raw["issue_id"]), "message": str(raw.get("message", ""))[:300]})
    result["repairs"] = repairs
    result["alerts"] = alerts
    result["prompt_adjustments"] = [str(item)[:300] for item in value.get("prompt_adjustments", [])[:8] if str(item).strip()]
    return result


def _merge_consensus(guidances: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge validated proposals without exposing chain-of-thought or source geometry."""
    parameter_keys = sorted({key for guidance in guidances for key in guidance.get("parameters", {})})
    parameters: dict[str, float | int] = {}
    for key in parameter_keys:
        values = sorted(float(guidance["parameters"][key]) for guidance in guidances if key in guidance.get("parameters", {}))
        if not values:
            continue
        middle = values[len(values) // 2] if len(values) % 2 else (values[len(values) // 2 - 1] + values[len(values) // 2]) / 2
        parameters[key] = int(round(middle)) if key in {"route_width", "water_margin"} else round(middle, 3)
    merged: dict[str, Any] = {
        "summary": "Multi-model semantic consensus for an original, brush-materialized RME map.",
        "parameters": parameters,
    }
    for key in ("architecture_rules", "biome_rules", "negative_constraints", "qa_intent"):
        seen: set[str] = set()
        values: list[str] = []
        for guidance in guidances:
            for item in guidance.get(key, ()):
                normalized = " ".join(str(item).split())
                marker = normalized.casefold()
                if normalized and marker not in seen:
                    seen.add(marker)
                    values.append(normalized[:240])
        merged[key] = values[:12]
    intent_seen: set[tuple[str, str, str, tuple[str, ...]]] = set()
    material_intents: list[dict[str, Any]] = []
    for guidance in guidances:
        for intent in guidance.get("material_intents", ()):
            marker = (
                str(intent.get("zone_role", "")).casefold(),
                str(intent.get("ground_key", "")),
                str(intent.get("wall_key", "")),
                tuple(intent.get("doodad_keys", ())),
            )
            if marker in intent_seen:
                continue
            intent_seen.add(marker)
            material_intents.append(dict(intent))
    merged["material_intents"] = material_intents[:16]
    return merged


def _merge_viewport_reviews(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    repairs: dict[tuple[str, str, str], dict[str, Any]] = {}
    alerts: dict[tuple[str, str], dict[str, Any]] = {}
    hints: list[str] = []
    for review in reviews:
        for repair in review.get("repairs", ()):
            repairs.setdefault((repair["issue_id"], repair["repair_kind"], repair.get("material_key", "")), repair)
        for alert in review.get("alerts", ()):
            alerts.setdefault((alert["issue_id"], alert["message"].casefold()), alert)
        for hint in review.get("prompt_adjustments", ()):
            if hint.casefold() not in {item.casefold() for item in hints}:
                hints.append(hint)
    return {
        "assessment": "Consensus de modelos sobre incidencias certificadas del viewport.",
        "repairs": list(repairs.values())[:16],
        "alerts": list(alerts.values())[:16],
        "prompt_adjustments": hints[:8],
    }


__all__ = ["ModelProviderOrchestrator"]

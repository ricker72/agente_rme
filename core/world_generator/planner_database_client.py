"""Autostarting local client for the shared Planner databases."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from core.world_generator.planner_database_server import HOST, PORT, PROTOCOL_VERSION


class PlannerDatabaseClient:
    _startup_lock = threading.Lock()

    def __init__(self, root: str | Path = ".", *, port: int = PORT, autostart: bool = True) -> None:
        self.root = Path(root).resolve()
        self.port = int(port)
        self.base_url = f"http://{HOST}:{self.port}"
        self.token_path = self.root / "exports" / "planner_knowledge" / ".local_server_token"
        self._process: subprocess.Popen[bytes] | None = None
        if autostart:
            self.ensure_server()

    def ensure_server(self, *, timeout: float = 30.0) -> dict[str, Any]:
        with self._startup_lock:
            health = self.health()
            if health.get("status") == "PASS":
                return health
            if health.get("status") == "WRONG_PROTOCOL":
                self._stop_stale_server(health)
            if health.get("status") == "WRONG_ROOT":
                raise RuntimeError(
                    "Planner server port is owned by a different agent root: "
                    f"{health.get('actual', 'unknown')}"
                )
            self._spawn_hidden()
            deadline = time.monotonic() + max(1.0, timeout)
            while time.monotonic() < deadline:
                time.sleep(0.1)
                health = self.health()
                if health.get("status") == "PASS":
                    return health
                if health.get("status") == "WRONG_ROOT":
                    raise RuntimeError(
                        "Planner server root changed during startup: "
                        f"{health.get('actual', 'unknown')}"
                    )
                if self._process is not None and self._process.poll() is not None:
                    break
        raise RuntimeError("RME Planner database server did not become ready")

    def health(self) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=0.6) as response:
                payload = json.loads(response.read().decode("utf-8"))
            expected = str(self.root / "exports" / "planner_knowledge" / "RME_PLANNER_EXPERIENCE.sqlite3")
            actual = str(payload.get("experience_database", {}).get("database", ""))
            if Path(actual).resolve() != Path(expected).resolve():
                return {"status": "WRONG_ROOT", "expected": expected, "actual": actual}
            actual_protocol = int(payload.get("protocol_version", 0))
            if actual_protocol != PROTOCOL_VERSION:
                return {
                    "status": "WRONG_PROTOCOL",
                    "expected": PROTOCOL_VERSION,
                    "actual": actual_protocol,
                    "process_id": int(payload.get("process_id", 0)),
                }
            return payload
        except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
            return {"status": "OFFLINE"}

    def request(self, route: str, payload: Mapping[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
        prepared = dict(payload)
        prepared.setdefault("_request_id", str(uuid.uuid4()))
        body = json.dumps(prepared, ensure_ascii=True, default=str).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(3):
            request = urllib.request.Request(
                f"{self.base_url}{route}", data=body, method="POST",
                headers={"Content-Type": "application/json", "X-RME-Token": self._token()},
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    value = json.loads(response.read().decode("utf-8"))
                if not isinstance(value, dict):
                    raise ValueError("Planner server response must be an object")
                return value
            except urllib.error.HTTPError:
                raise
            except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt == 0:
                    self.ensure_server()
                if attempt < 2:
                    time.sleep(0.15 * (2 ** attempt))
        raise RuntimeError(f"Planner server request failed after retries: {type(last_error).__name__}")

    def guidance(self, objective: str, *, limit: int = 16) -> dict[str, Any]:
        return self.request("/v1/guidance", {"objective": objective, "limit": limit})

    def planner_context(self, objective: str) -> dict[str, Any]:
        return self.request("/v1/planner/context", {"objective": objective})

    def search_materials(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return list(self.request("/v1/materials/search", {"query": query, "limit": limit}).get("results", ()))

    def brush_grammar(self, query: str, limit: int = 16) -> list[dict[str, Any]]:
        """Read exact cached RME brush trees from the local Planner service."""
        return list(self.request(
            "/v1/materials/brush-grammar", {"query": query, "limit": limit}
        ).get("results", ()))

    def tileset_knowledge(self, query: str = "", limit: int = 32) -> list[dict[str, Any]]:
        return list(self.request(
            "/v1/materials/tilesets", {"query": query, "limit": limit}
        ).get("results", ()))

    def material_brief(self, objective: str) -> dict[str, Any]:
        return self.request("/v1/planner/material-brief", {"objective": objective})

    def rme_grammar(self, objective: str = "") -> dict[str, Any]:
        return self.request("/v1/rme/grammar", {"objective": objective})

    def rme_neighbor_lookup(self, system: str, mask: int | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"system": system}
        if mask is not None:
            payload["mask"] = int(mask)
        return list(self.request("/v1/rme/neighbor-lookup", payload).get("results", ()))

    def reference_brief(self, objective: str) -> dict[str, Any]:
        return self.request("/v1/planner/reference-brief", {"objective": objective})

    def knowledge_status(self) -> dict[str, Any]:
        return self.request("/v1/knowledge/status", {})

    def refresh_reference_corpus(
        self, *, wait: bool = True, timeout: float = 600.0
    ) -> dict[str, Any]:
        return self.request(
            "/v1/knowledge/reference-refresh",
            {"wait": bool(wait), "timeout": float(timeout)},
            timeout=max(30.0, float(timeout) + 5.0) if wait else 30.0,
        )

    def ai_plan(
        self,
        objective: str,
        *,
        context: Mapping[str, Any] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"objective": objective, "context": dict(context or {})}
        if mode:
            payload["mode"] = mode
        return self.request("/v1/ai/plan", payload, timeout=150.0)

    def analyze_viewport(
        self,
        snapshot: Mapping[str, Any],
        *,
        ask_model: bool = False,
        mode: str | None = None,
        objective: str = "",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"snapshot": dict(snapshot), "ask_model": bool(ask_model)}
        if mode:
            payload["mode"] = mode
        if objective.strip():
            payload["objective"] = objective[:2_000]
        return self.request("/v1/viewport/analyze", payload, timeout=150.0 if ask_model else 20.0)

    def review_visual_feedback(
        self,
        report: Mapping[str, Any],
        *,
        mode: str | None = None,
        objective: str = "",
    ) -> dict[str, Any]:
        """Return a bounded pre-commit repair mask to the Planner/model bridge."""
        payload: dict[str, Any] = {"report": dict(report)}
        if mode:
            payload["mode"] = mode
        if objective.strip():
            payload["objective"] = objective[:2_000]
        return self.request("/v1/viewport/feedback", payload, timeout=150.0)

    def ai_preferences(self) -> dict[str, Any]:
        return self.request("/v1/ai/preferences/get", {})

    def set_ai_mode(self, mode: str) -> dict[str, Any]:
        return self.request("/v1/ai/preferences/set", {"mode": mode})

    def start_experience(self, objective: str, **kwargs: Any) -> str:
        payload = {"objective": objective, **kwargs}
        return str(self.request("/v1/experience/start", payload)["experience_id"])

    def record_qa(self, experience_id: str, gate: str, status: str, *, evidence: Any = None, score: float | None = None) -> dict[str, Any]:
        return self.request("/v1/experience/qa", {
            "experience_id": experience_id, "gate": gate, "status": status,
            "evidence": evidence or {}, "score": score,
        })

    def attach_artifact(self, experience_id: str, artifact_path: str | Path) -> None:
        self.request("/v1/experience/artifact", {"experience_id": experience_id, "artifact_path": str(artifact_path)})

    def mark_failed(self, experience_id: str, error: BaseException | str) -> None:
        self.request("/v1/experience/fail", {"experience_id": experience_id, "error": str(error)})

    def record_human_validation(
        self,
        experience_id: str,
        verdict: str,
        *,
        validator: str = "human",
        notes: str = "",
        canary_console_errors: int = 0,
        observations: Iterable[Mapping[str, Any]] = (),
        gate: str = "canary_manual",
    ) -> dict[str, Any]:
        return self.request("/v1/experience/human", {
            "experience_id": experience_id, "verdict": verdict, "validator": validator,
            "notes": notes, "canary_console_errors": canary_console_errors,
            "observations": list(observations), "gate": gate,
        })

    def evaluate_promotion(self, experience_id: str) -> dict[str, Any]:
        return self.request("/v1/experience/evaluate", {"experience_id": experience_id})

    def experience(self, experience_id: str) -> dict[str, Any]:
        return self.request("/v1/experience/get", {"experience_id": experience_id})

    def audit(self) -> dict[str, Any]:
        return self.request("/v1/audit", {})

    def _spawn_hidden(self) -> None:
        if getattr(sys, "frozen", False):
            from core.world_generator.planner_database_server import serve

            thread = threading.Thread(
                target=serve,
                args=(self.root,),
                kwargs={"port": self.port},
                name="RMEPlannerDatabaseServer",
                daemon=True,
            )
            thread.start()
            return
        executable = _python_without_console()
        command = [
            str(executable), "-m", "core.world_generator.planner_database_server",
            "--root", str(self.root), "--port", str(self.port),
        ]
        kwargs: dict[str, Any] = {
            "cwd": str(self.root),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            kwargs["startupinfo"] = startupinfo
        self._process = subprocess.Popen(command, **kwargs)

    @staticmethod
    def _stop_stale_server(health: Mapping[str, Any]) -> None:
        process_id = int(health.get("process_id", 0))
        if process_id <= 0 or process_id == os.getpid():
            raise RuntimeError("Stale Planner server has no safe process identity")
        os.kill(process_id, signal.SIGTERM)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                os.kill(process_id, 0)
            except OSError:
                return
            time.sleep(0.05)
        raise RuntimeError("Stale Planner server did not stop")

    def _token(self) -> str:
        if not self.token_path.is_file():
            self.ensure_server()
        token = self.token_path.read_text(encoding="ascii").strip()
        if len(token) < 32:
            raise RuntimeError("Invalid local Planner server token")
        return token


def _python_without_console() -> Path:
    executable = Path(sys.executable).resolve()
    if os.name == "nt" and executable.name.casefold() == "python.exe":
        candidate = executable.with_name("pythonw.exe")
        if candidate.is_file():
            return candidate
    return executable


__all__ = ["PlannerDatabaseClient"]

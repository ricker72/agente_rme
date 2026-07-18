"""Loopback-only database service shared by Agente RME and Workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HOST = "127.0.0.1"
PORT = 8776
MAX_BODY_BYTES = 2_200_000


class _ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    allow_reuse_port = False


class PlannerDatabaseApplication:
    def __init__(self, root: str | Path) -> None:
        from core.world_generator.experience_learning_loop import ExperienceLearningLoop
        from core.world_generator.planner_knowledge_database import PlannerKnowledgeDatabase
        from core.world_generator.planner_material_brief import CertifiedMaterialBriefBuilder
        from core.world_generator.planner_reference_brief import CertifiedReferenceBriefBuilder
        from core.ai.model_provider_orchestrator import ModelProviderOrchestrator
        from core.ai.planner_model_bridge import PlannerModelBridge
        from core.editor.viewport_observer import ViewportObserver

        self.root = Path(root).resolve()
        self.resource_root = _resource_root()
        writable_knowledge = self.root / "exports" / "planner_knowledge" / "RME_PLANNER_KNOWLEDGE.sqlite3"
        bundled_knowledge = self.resource_root / "exports" / "planner_knowledge" / "RME_PLANNER_KNOWLEDGE.sqlite3"
        self.knowledge_path = writable_knowledge if writable_knowledge.is_file() else bundled_knowledge
        self.experience_path = self.root / "exports" / "planner_knowledge" / "RME_PLANNER_EXPERIENCE.sqlite3"
        self.token_path = self.root / "exports" / "planner_knowledge" / ".local_server_token"
        self.ai_preferences_path = self.root / "exports" / "planner_knowledge" / "AI_PROVIDER_PREFERENCES.json"
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token = self._load_token()
        self.knowledge = PlannerKnowledgeDatabase(self.knowledge_path)
        self.material_briefs = CertifiedMaterialBriefBuilder(self.knowledge_path)
        self.reference_briefs = CertifiedReferenceBriefBuilder(self.knowledge_path)
        self.experience = ExperienceLearningLoop(self.experience_path)
        self.models = ModelProviderOrchestrator(self.resource_root)
        self.ai_bridge = PlannerModelBridge(self.models, self.experience)
        self.viewport_observer = ViewportObserver(self.resource_root)
        self._preferences_lock = threading.Lock()
        self._request_lock = threading.Lock()
        self._request_cache: dict[str, dict[str, Any]] = {}
        self._requests_inflight: dict[str, threading.Event] = {}

    def dispatch_idempotent(
        self, route: str, payload: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        if not request_id or len(request_id) > 64:
            raise ValueError("valid _request_id is required")
        with self._request_lock:
            cached = self._request_cache.get(request_id)
            if cached is not None:
                return dict(cached)
            event = self._requests_inflight.get(request_id)
            owner = event is None
            if owner:
                event = threading.Event()
                self._requests_inflight[request_id] = event
        if not owner:
            if not event.wait(timeout=180.0):
                raise RuntimeError("duplicate request is still running")
            with self._request_lock:
                cached = self._request_cache.get(request_id)
            if cached is None:
                raise RuntimeError("original request failed before producing a response")
            return dict(cached)
        try:
            result = self.dispatch(route, payload)
            with self._request_lock:
                self._request_cache[request_id] = dict(result)
                while len(self._request_cache) > 512:
                    self._request_cache.pop(next(iter(self._request_cache)))
            return result
        finally:
            with self._request_lock:
                completed = self._requests_inflight.pop(request_id, None)
                if completed is not None:
                    completed.set()

    def dispatch(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        if route == "/v1/viewport/feedback":
            report = payload.get("report", {})
            if not isinstance(report, dict):
                raise ValueError("report must be an object")
            forbidden_payload_keys = {"image", "images", "pixels", "png", "frame", "frames", "base64", "data_url"}
            if forbidden_payload_keys & {str(key).lower() for key in report}:
                raise ValueError("visual feedback accepts semantic masks only")
            allowed_codes = {
                "MISSING_GROUND", "MISSING_RENDER", "MISSING_SPRITE", "EMPTY_ALPHA",
                "BLACK_TILE", "PLACEHOLDER_COLOR", "UNKNOWN_GROUND", "NON_GROUND_AS_GROUND",
                "UNKNOWN_ITEM", "DRAW_ORDER_MISMATCH", "ISOLATED_WALL", "ORPHAN_BORDER",
            }
            allowed_repairs = {
                "REAPPLY_GROUND_BRUSH", "REBUILD_AUTOBORDER", "REBUILD_WALL_NEIGHBORS",
                "REORDER_STACK", "RESELECT_SPRITE_BACKED_MATERIAL",
            }
            raw_mask = report.get("repair_mask", ())
            if not isinstance(raw_mask, list) or len(raw_mask) > 4096:
                raise ValueError("repair_mask must be a list with at most 4096 entries")
            observations = []
            repair_mask = []
            for entry in raw_mask:
                if not isinstance(entry, dict):
                    continue
                x, y, z = int(entry.get("x", -1)), int(entry.get("y", -1)), int(entry.get("z", -1))
                code = str(entry.get("defect_code", ""))
                repair = str(entry.get("repair_kind", ""))
                if not (0 <= x <= 65535 and 0 <= y <= 65535 and 0 <= z <= 15):
                    raise ValueError("repair mask coordinate is out of OTBM bounds")
                if code not in allowed_codes or repair not in allowed_repairs:
                    raise ValueError("repair mask contains an unsupported action")
                repair_mask.append({"x": x, "y": y, "z": z, "defect_code": code, "repair_kind": repair})
                issue_id = hashlib.sha256(f"{code}:{x}:{y}:{z}:{repair}".encode("ascii")).hexdigest()[:20]
                observations.append({
                    "issue_id": issue_id,
                    "code": code, "severity": "error", "category": "visual_precommit",
                    "x": x, "y": y, "z": z, "repair_kind": repair,
                    "message": "Pre-commit visual gate requested a certified repair.",
                    "auto_repairable": False,
                })
            objective = str(payload.get("objective", "")).strip()[:2_000] or "Repair pre-commit viewport defects"
            context = {
                "certified_material_brief": self.material_briefs.build(objective),
                "certified_reference_brief": self.reference_briefs.build(objective),
                "certified_rme_grammar": self.knowledge.rme_technical_grammar(objective),
                "validated_experience_rules": self.experience.guidance(objective),
                "contract": {
                    "allowed_repair_kinds": sorted(allowed_repairs),
                    "raw_item_ids_forbidden": True,
                    "planner_owns_materialization": True,
                },
            }
            mode = str(payload.get("mode") or self._ai_preferences()["mode"]).strip().lower()
            if mode not in {"auto", "ollama", "openrouter", "paxsenix", "triple", "triple_consensus"}:
                raise ValueError("unsupported AI provider mode")
            model_review = self.models.review_viewport(observations, context=context, mode=mode) if observations else {}
            response = {
                "status": "REPAIR_REQUIRED" if repair_mask else "PASS",
                "source": "viewport_visual_feedback_loop",
                "repair_mask": repair_mask,
                "counts": {"error": len(repair_mask), "warning": 0},
                "model_review": model_review,
                "pixels_received": False,
            }
            try:
                self.experience.record_ai_bridge_event(
                    session_id=hashlib.sha256(json.dumps(repair_mask, sort_keys=True).encode("utf-8")).hexdigest()[:64],
                    phase="visual_precommit_feedback",
                    round_index=1,
                    provider=str(model_review.get("provider", "")),
                    model=str(model_review.get("model", "")),
                    status=str(model_review.get("status", response["status"])),
                    objective_hash=hashlib.sha256(objective.encode("utf-8")).hexdigest(),
                    critique={
                        "issue_codes": sorted({item["defect_code"] for item in repair_mask}),
                        "counts": response["counts"],
                        "coordinates_stored": False,
                    },
                    response_hash=hashlib.sha256(
                        json.dumps(model_review.get("guidance", {}), sort_keys=True, default=str).encode("utf-8")
                    ).hexdigest(),
                )
            except Exception:
                pass
            return response
        if route == "/v1/viewport/analyze":
            snapshot = payload.get("snapshot", {})
            if not isinstance(snapshot, dict):
                raise ValueError("snapshot must be an object")
            report = self.viewport_observer.analyze(snapshot)
            report["model_review"] = {}
            if payload.get("ask_model") and report["observations"]:
                objective = str(payload.get("objective", "")).strip()[:2_000] or (
                    "Review live viewport: " + ", ".join(
                        sorted({str(item.get("category", "")) for item in report["observations"]})
                    )
                )
                context = {
                    "certified_material_brief": self.material_briefs.build(objective),
                    "certified_reference_brief": self.reference_briefs.build(objective),
                    "certified_rme_grammar": self.knowledge.rme_technical_grammar(objective),
                    "validated_experience_rules": self.experience.guidance(objective),
                }
                mode = str(payload.get("mode") or self._ai_preferences()["mode"]).strip().lower()
                report["model_review"] = self.models.review_viewport(
                    report["observations"], context=context, mode=mode
                )
                review = report["model_review"]
                try:
                    self.experience.record_ai_bridge_event(
                        session_id=str(report.get("snapshot_hash", ""))[:64],
                        phase="viewport_review",
                        round_index=1,
                        provider=str(review.get("provider", "")),
                        model=str(review.get("model", "")),
                        status=str(review.get("status", "")),
                        objective_hash=hashlib.sha256(objective.encode("utf-8")).hexdigest(),
                        critique={
                            "issue_codes": sorted({str(item.get("code", "")) for item in report["observations"]}),
                            "counts": report.get("counts", {}),
                            "coordinates_stored": False,
                        },
                        response_hash=hashlib.sha256(
                            json.dumps(review.get("guidance", {}), sort_keys=True, default=str).encode("utf-8")
                        ).hexdigest(),
                    )
                except Exception:
                    pass
            return report
        if route == "/v1/guidance":
            return self.experience.guidance(str(payload.get("objective", "")), limit=int(payload.get("limit", 16)))
        if route == "/v1/planner/context":
            objective = str(payload.get("objective", ""))
            return {
                "status": "PASS",
                "reference_archetypes": self.knowledge.reference_archetypes(objective) if self.knowledge_path.is_file() else [],
                "reference_scans": self.knowledge.reference_scans(objective) if self.knowledge_path.is_file() else [],
                "world_town_scans": self.knowledge.world_town_scans(objective) if self.knowledge_path.is_file() else [],
                "quest_script_patterns": self.knowledge.quest_script_patterns(objective) if self.knowledge_path.is_file() else [],
                "editor_runtime_rules": self.knowledge.editor_runtime_rules(objective) if self.knowledge_path.is_file() else [],
                "certified_rme_grammar": self.knowledge.rme_technical_grammar(objective) if self.knowledge_path.is_file() else {},
                "parsed_brush_grammar": self.knowledge.brush_grammar(objective, 8) if self.knowledge_path.is_file() else [],
                "tileset_knowledge": self.knowledge.tileset_knowledge(objective, 8) if self.knowledge_path.is_file() else [],
                "experience_guidance": self.experience.guidance(objective),
            }
        if route == "/v1/materials/search":
            query = str(payload.get("query", ""))
            limit = max(1, min(500, int(payload.get("limit", 50))))
            return {
                "status": "PASS",
                "results": self.knowledge.search_materials(query, limit) if query and self.knowledge_path.is_file() else [],
            }
        if route == "/v1/rme/grammar":
            objective = str(payload.get("objective", ""))
            return self.knowledge.rme_technical_grammar(objective)
        if route == "/v1/materials/brush-grammar":
            query = str(payload.get("query", ""))
            if not query.strip():
                raise ValueError("query is required")
            return {
                "status": "PASS",
                "results": self.knowledge.brush_grammar(query, int(payload.get("limit", 16))),
            }
        if route == "/v1/materials/tilesets":
            return {
                "status": "PASS",
                "results": self.knowledge.tileset_knowledge(
                    str(payload.get("query", "")), int(payload.get("limit", 32))
                ),
            }
        if route == "/v1/rme/neighbor-lookup":
            system = str(payload.get("system", ""))
            raw_mask = payload.get("mask")
            mask = None if raw_mask is None else int(raw_mask)
            return {
                "status": "PASS",
                "results": self.knowledge.rme_neighbor_lookup(system, mask, int(payload.get("limit", 256))),
            }
        if route == "/v1/planner/material-brief":
            objective = str(payload.get("objective", ""))
            if not objective.strip():
                raise ValueError("objective is required")
            return self.material_briefs.build(objective)
        if route == "/v1/planner/reference-brief":
            objective = str(payload.get("objective", ""))
            if not objective.strip():
                raise ValueError("objective is required")
            return self.reference_briefs.build(objective)
        if route == "/v1/ai/plan":
            objective = str(payload.get("objective", ""))
            if not objective.strip():
                raise ValueError("objective is required")
            preferences = self._ai_preferences()
            mode = str(payload.get("mode") or preferences["mode"]).strip().lower()
            if mode not in {"auto", "ollama", "openrouter", "paxsenix", "triple", "triple_consensus"}:
                raise ValueError("unsupported AI provider mode")
            context = payload.get("context", {})
            if not isinstance(context, dict):
                raise ValueError("context must be an object")
            context = dict(context)
            # This field is always rebuilt server-side. Clients cannot inject IDs or
            # expand the allowlist seen by a model.
            context["certified_material_brief"] = self.material_briefs.build(objective)
            context["certified_reference_brief"] = self.reference_briefs.build(objective)
            context["certified_rme_grammar"] = self.knowledge.rme_technical_grammar(objective)
            context["parsed_brush_grammar"] = self.knowledge.brush_grammar(objective, 8)
            context["tileset_knowledge"] = self.knowledge.tileset_knowledge(objective, 8)
            context["editor_runtime_rules"] = self.knowledge.editor_runtime_rules(objective, 16)
            context["validated_experience_rules"] = self.experience.guidance(objective)
            result = self.ai_bridge.plan(objective, context=context, mode=mode)
            proposal_id = ""
            if result.get("guidance") and result.get("status") not in {"DETERMINISTIC_FALLBACK", "DISABLED"}:
                proposal_id = self.experience.record_ai_proposal(
                    objective,
                    provider=str(result.get("provider", "")),
                    model=str(result.get("model", "")),
                    status=str(result.get("status", "")),
                    guidance=result.get("guidance", {}),
                    material_catalog_hash=str(context["certified_material_brief"].get("catalog_hash", "")),
                    reference_brief_hash=str(context["certified_reference_brief"].get("brief_hash", "")),
                )
            result["proposal_id"] = proposal_id
            return result
        if route == "/v1/ai/preferences/get":
            return {"status": "PASS", **self._ai_preferences()}
        if route == "/v1/ai/preferences/set":
            mode = str(payload.get("mode", "auto")).strip().lower()
            if mode not in {"auto", "ollama", "openrouter", "paxsenix", "triple_consensus"}:
                raise ValueError("unsupported AI provider mode")
            preferences = {"mode": mode}
            self._write_ai_preferences(preferences)
            return {"status": "PASS", **preferences}
        if route == "/v1/experience/start":
            experience_id = self.experience.start_experience(
                str(payload.get("objective", "")),
                planner_snapshot=payload.get("planner_snapshot", {}),
                context=payload.get("context", {}),
                source_kind=str(payload.get("source_kind", "generated_map")),
                artifact_path=payload.get("artifact_path") or None,
                experience_id=payload.get("experience_id") or None,
            )
            return {"status": "PASS", "experience_id": experience_id}
        if route == "/v1/experience/qa":
            return self.experience.record_qa(
                str(payload["experience_id"]),
                str(payload["gate"]),
                str(payload["status"]),
                evidence=payload.get("evidence", {}),
                score=payload.get("score"),
            )
        if route == "/v1/experience/human":
            return self.experience.record_human_validation(
                str(payload["experience_id"]),
                str(payload["verdict"]),
                validator=str(payload.get("validator", "human")),
                notes=str(payload.get("notes", "")),
                canary_console_errors=int(payload.get("canary_console_errors", 0)),
                observations=payload.get("observations", ()),
                gate=str(payload.get("gate", "canary_manual")),
            )
        if route == "/v1/experience/artifact":
            self.experience.attach_artifact(str(payload["experience_id"]), str(payload["artifact_path"]))
            return {"status": "PASS"}
        if route == "/v1/experience/fail":
            self.experience.mark_failed(str(payload["experience_id"]), str(payload.get("error", "unknown failure")))
            return {"status": "PASS"}
        if route == "/v1/experience/evaluate":
            return self.experience.evaluate_promotion(str(payload["experience_id"]))
        if route == "/v1/experience/get":
            return self.experience.experience(str(payload["experience_id"]))
        if route == "/v1/audit":
            return self.audit()
        raise KeyError(f"Unknown route: {route}")

    def audit(self) -> dict[str, Any]:
        return {
            "status": "PASS",
            "service": "RME Planner Database Server",
            "host": HOST,
            "knowledge_database": {"path": str(self.knowledge_path), "available": self.knowledge_path.is_file()},
            "certified_material_grounding": {
                "available": self.knowledge_path.is_file(),
                "source": "Canary/RME materials database",
                "server_authoritative": True,
                "model_writes_ids": False,
            },
            "certified_reference_grounding": {
                "available": self.knowledge_path.is_file(),
                "sources": ["world.otbm scans", "reference OTBM scans"],
                "source_geometry_exposed": False,
                "server_authoritative": True,
            },
            "experience_database": self.experience.audit(),
            "ai_gateway": {
                **self.models.audit(),
                "preferences": self._ai_preferences(),
                "process_owner": "LOCAL_SERVER",
                "bidirectional_planner_bridge": True,
                "max_correction_rounds": self.ai_bridge.max_rounds,
            },
            "viewport_observer": {
                "available": True,
                "pixels_persisted": False,
                "mutates_map": False,
                "model_repairs_require_visual_diff": True,
            },
            "browser_opened": False,
            "loopback_only": True,
        }

    def _ai_preferences(self) -> dict[str, str]:
        default = str(self.models._get("ai.default_mode", "auto")).strip().lower()  # noqa: SLF001
        if not self.ai_preferences_path.is_file():
            return {"mode": default if default else "auto"}
        try:
            payload = json.loads(self.ai_preferences_path.read_text(encoding="utf-8"))
            mode = str(payload.get("mode", default)).strip().lower()
            if mode in {"auto", "ollama", "openrouter", "paxsenix", "triple_consensus"}:
                return {"mode": mode}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        return {"mode": "auto"}

    def _write_ai_preferences(self, preferences: dict[str, str]) -> None:
        with self._preferences_lock:
            self.ai_preferences_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.ai_preferences_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(preferences, sort_keys=True), encoding="utf-8")
            os.replace(temporary, self.ai_preferences_path)

    def _load_token(self) -> str:
        if self.token_path.is_file():
            token = self.token_path.read_text(encoding="ascii").strip()
            if len(token) >= 32:
                return token
            raise RuntimeError(f"Invalid local server token: {self.token_path}")
        token = secrets.token_urlsafe(48)
        try:
            with self.token_path.open("x", encoding="ascii") as handle:
                handle.write(token)
            return token
        except FileExistsError:
            shared = self.token_path.read_text(encoding="ascii").strip()
            if len(shared) < 32:
                raise RuntimeError(f"Invalid local server token after concurrent startup: {self.token_path}")
            return shared


def handler_for(application: PlannerDatabaseApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "RMEPlannerDB/1.0"

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(20.0)

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/health":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._send(application.audit())

        def do_POST(self) -> None:  # noqa: N802
            if not secrets.compare_digest(self.headers.get("X-RME-Token", ""), application.token):
                self._send({"status": "ERROR", "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY_BYTES:
                    raise ValueError("invalid request size")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON object required")
                request_id = str(payload.pop("_request_id", ""))
                self._send(application.dispatch_idempotent(urlparse(self.path).path, payload, request_id))
            except KeyError as exc:
                self._send({"status": "ERROR", "error": str(exc)}, HTTPStatus.NOT_FOUND)
            except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                self._send({"status": "ERROR", "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # noqa: BLE001 - service boundary returns sanitized diagnostics.
                self._send({"status": "ERROR", "error": type(exc).__name__}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _send(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=True, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(encoded)

    return Handler


def serve(root: str | Path, *, host: str = HOST, port: int = PORT) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Planner database service may only bind to loopback")
    application = PlannerDatabaseApplication(root)
    server = _ExclusiveThreadingHTTPServer((HOST, int(port)), handler_for(application))
    server.daemon_threads = True
    server.serve_forever(poll_interval=0.5)


def _resource_root() -> Path:
    explicit = os.environ.get("RME_AGENT_CORE_PATH")
    if explicit:
        return Path(explicit).expanduser().resolve(strict=False)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    serve(args.root, port=args.port)


if __name__ == "__main__":
    main()

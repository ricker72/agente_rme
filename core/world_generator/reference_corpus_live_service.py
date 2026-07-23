"""Live, persistent refresh service for the coordinate-free reference corpus."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.world_generator.planner_knowledge_database import (
    PlannerKnowledgeDatabase,
    ReferenceCorpusChangedError,
)


class ReferenceCorpusLiveService:
    """Watch reference maps and atomically publish rebuilt Planner knowledge."""

    def __init__(
        self,
        root: str | Path,
        knowledge: PlannerKnowledgeDatabase,
        *,
        poll_seconds: float = 2.0,
        debounce_seconds: float = 1.0,
    ) -> None:
        self.root = Path(root).resolve()
        self.corpus_root = self.root / "projects" / "Mapas Referencia"
        self.knowledge = knowledge
        self.manifest_path = self.knowledge.path.parent / "reference_corpus_state.json"
        self.poll_seconds = max(0.5, float(poll_seconds))
        self.debounce_seconds = max(0.25, float(debounce_seconds))
        self._stop = threading.Event()
        self._requested = threading.Event()
        self._completed = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._validator_thread: threading.Thread | None = None
        self._generation = 0
        self._last_snapshot: tuple[tuple[str, int, int], ...] = ()
        self._state: dict[str, Any] = {
            "status": "IDLE",
            "watching": str(self.corpus_root),
            "map_count": 0,
            "generation": 0,
            "last_started_utc": "",
            "last_completed_utc": "",
            "last_error": "",
            "last_result": {},
        }

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._last_snapshot = self._snapshot()
        with self._lock:
            self._state["map_count"] = self._map_count(self._last_snapshot)
        self._thread = threading.Thread(
            target=self._run,
            name="RMEReferenceCorpusLiveRefresh",
            daemon=True,
        )
        self._thread.start()
        if self._manifest_matches(self._last_snapshot):
            return
        with self._lock:
            self._state["status"] = "VALIDATING"
        self._validator_thread = threading.Thread(
            target=self._validate_initial_database,
            args=(self._last_snapshot,),
            name="RMEReferenceCorpusInitialValidation",
            daemon=True,
        )
        self._validator_thread.start()

    def close(self) -> None:
        self._stop.set()
        self._requested.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self._validator_thread is not None:
            self._validator_thread.join(timeout=5.0)

    def trigger(self, *, wait: bool = False, timeout: float = 600.0) -> dict[str, Any]:
        with self._lock:
            target_generation = self._generation + 1
            self._completed.clear()
        self._requested.set()
        if not wait:
            return self.status()
        deadline = time.monotonic() + max(1.0, min(float(timeout), 1_800.0))
        while time.monotonic() < deadline:
            with self._lock:
                completed = self._generation >= target_generation
                running = self._state["status"] in {"SCANNING", "PUBLISHING"}
            if completed and not running:
                return self.status()
            self._completed.wait(timeout=min(0.25, max(0.0, deadline - time.monotonic())))
        raise TimeoutError("Reference corpus refresh did not finish before timeout")

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                **self._state,
                "last_result": dict(self._state.get("last_result", {})),
                "live_reads_available": True,
                "source_geometry_persisted": False,
            }

    def _run(self) -> None:
        changed_at: float | None = None
        while not self._stop.is_set():
            snapshot = self._snapshot()
            if snapshot != self._last_snapshot:
                self._last_snapshot = snapshot
                changed_at = time.monotonic()
                with self._lock:
                    self._state["map_count"] = self._map_count(snapshot)
            if changed_at is not None and time.monotonic() - changed_at >= self.debounce_seconds:
                self._requested.set()
                changed_at = None
            if self._requested.wait(timeout=self.poll_seconds):
                self._requested.clear()
                if self._stop.is_set():
                    break
                self._refresh()

    def _refresh(self) -> None:
        with self._lock:
            self._state.update({
                "status": "SCANNING",
                "last_started_utc": self._utc_now(),
                "last_error": "",
            })
        try:
            result = self.knowledge.refresh_reference_corpus(self.root)
            snapshot = self._snapshot()
            self._last_snapshot = snapshot
            if result.get("status") == "PASS":
                self._write_manifest(snapshot)
            with self._lock:
                self._state["map_count"] = self._map_count(snapshot)
                self._state["status"] = "PASS" if result.get("status") == "PASS" else "BLOCKED"
                self._state["last_result"] = {
                    "status": result.get("status"),
                    "integrity": result.get("integrity"),
                    "elapsed_seconds": result.get("elapsed_seconds"),
                    "reference_maps": result.get("counts", {}).get("reference_maps", 0),
                    "readers_remained_available": result.get("readers_remained_available", False),
                }
                self._state["last_completed_utc"] = self._utc_now()
        except Exception as exc:  # Service boundary stores only the exception class.
            with self._lock:
                self._state.update({
                    "status": "ERROR",
                    "last_error": type(exc).__name__,
                    "last_completed_utc": self._utc_now(),
                    "last_result": {},
                })
            if isinstance(exc, ReferenceCorpusChangedError):
                self._requested.set()
        finally:
            with self._lock:
                self._generation += 1
                self._state["generation"] = self._generation
            self._completed.set()

    def _validate_initial_database(
        self,
        expected_snapshot: tuple[tuple[str, int, int], ...],
    ) -> None:
        matches = self._database_matches_corpus()
        if self._stop.is_set():
            return
        current_snapshot = self._snapshot()
        if matches and current_snapshot == expected_snapshot:
            self._write_manifest(current_snapshot)
            with self._lock:
                if self._state["status"] == "VALIDATING":
                    self._state["status"] = "IDLE"
            return
        self._requested.set()

    def _snapshot(self) -> tuple[tuple[str, int, int], ...]:
        if not self.corpus_root.is_dir():
            return ()
        records = []
        for path in self.corpus_root.rglob("*"):
            if not path.is_file() or path.suffix.casefold() not in {".otbm", ".xml"}:
                continue
            stat = path.stat()
            records.append((
                path.relative_to(self.corpus_root).as_posix(),
                int(stat.st_mtime_ns),
                int(stat.st_size),
            ))
        return tuple(sorted(records))

    def _database_matches_corpus(self) -> bool:
        maps = sorted(self.corpus_root.rglob("*.otbm")) if self.corpus_root.is_dir() else []
        try:
            with self.knowledge.connect(read_only=True) as connection:
                rows = connection.execute(
                    "SELECT source,source_sha256 FROM reference_maps"
                ).fetchall()
            expected = {str(row["source"]).replace("\\", "/"): str(row["source_sha256"]) for row in rows}
        except Exception:
            return False
        if len(expected) != len(maps):
            return False
        for path in maps:
            relative = path.relative_to(self.root).as_posix()
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
            if expected.get(relative) != digest.hexdigest():
                return False
        return True

    def _manifest_matches(self, snapshot: tuple[tuple[str, int, int], ...]) -> bool:
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return False
        if payload.get("schema") != 1:
            return False
        records = payload.get("records")
        if not isinstance(records, list):
            return False
        expected = tuple(
            (str(record[0]), int(record[1]), int(record[2]))
            for record in records
            if isinstance(record, list) and len(record) == 3
        )
        return expected == snapshot and int(payload.get("map_count", -1)) == self._map_count(snapshot)

    def _write_manifest(self, snapshot: tuple[tuple[str, int, int], ...]) -> None:
        payload = {
            "schema": 1,
            "map_count": self._map_count(snapshot),
            "records": [list(record) for record in snapshot],
        }
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(self.manifest_path)

    @staticmethod
    def _map_count(snapshot: tuple[tuple[str, int, int], ...]) -> int:
        return sum(name.casefold().endswith(".otbm") for name, _, _ in snapshot)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = ["ReferenceCorpusLiveService"]

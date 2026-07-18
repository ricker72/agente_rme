"""Persistent, gated learning for generated maps and human Canary validation.

The experience store is intentionally separate from the rebuildable planner
knowledge database.  It stores outcomes and abstract lessons, never reference
map chunks or screenshots.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


SCHEMA_VERSION = 3
REQUIRED_PROMOTION_GATES = (
    "otbm_roundtrip",
    "material_safety",
    "visual_qa",
    "playability",
    "canary_manual",
)
POSITIVE_GATE_STATES = frozenset({"PASS", "CERTIFIED"})
HARD_FAILURE_STATES = frozenset({"FAIL", "BLOCKED", "ERROR"})
HUMAN_VERDICTS = frozenset({"PASS", "FAIL", "NEEDS_REPAIR"})
MAX_JSON_BYTES = 2_000_000


def default_experience_database(root: str | Path = ".") -> Path:
    return Path(root).resolve() / "exports" / "planner_knowledge" / "RME_PLANNER_EXPERIENCE.sqlite3"


class ExperienceLearningLoop:
    """Record, evaluate and retrieve map-generation experience safely."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @classmethod
    def for_root(cls, root: str | Path = ".") -> "ExperienceLearningLoop":
        return cls(default_experience_database(root))

    def start_experience(
        self,
        objective: str,
        *,
        planner_snapshot: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        source_kind: str = "generated_map",
        artifact_path: str | Path | None = None,
        experience_id: str | None = None,
    ) -> str:
        objective = _clean_text(objective, 8_000)
        if not objective:
            raise ValueError("Experience objective cannot be empty")
        identifier = experience_id or str(uuid.uuid4())
        now = _utc_now()
        artifact = str(Path(artifact_path).resolve()) if artifact_path else ""
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO experiences(
                    id, created_at, updated_at, objective, source_kind, status,
                    planner_snapshot_json, context_json, artifact_path, artifact_sha256
                ) VALUES(?, ?, ?, ?, ?, 'RUNNING', ?, ?, ?, '')
                """,
                (
                    identifier,
                    now,
                    now,
                    objective,
                    _identifier(source_kind),
                    _json(planner_snapshot or {}),
                    _json(context or {}),
                    artifact,
                ),
            )
        return identifier

    def record_ai_proposal(
        self,
        objective: str,
        *,
        provider: str,
        model: str,
        status: str,
        guidance: Mapping[str, Any] | None,
        material_catalog_hash: str,
        reference_brief_hash: str,
    ) -> str:
        """Persist a quarantined model proposal; it is not learned until map QA passes."""
        proposal_id = str(uuid.uuid4())
        now = _utc_now()
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO ai_planning_proposals(
                    id,created_at,updated_at,objective,provider,model,provider_status,
                    learning_status,guidance_json,material_catalog_hash,
                    reference_brief_hash,linked_experience_id
                ) VALUES(?,?,?,?,?,?,?,'CANDIDATE',?,?,?,'')
                """,
                (
                    proposal_id, now, now, _clean_text(objective, 8_000),
                    _identifier(provider), _clean_text(model, 500), _identifier(status),
                    _json(guidance or {}), _clean_text(material_catalog_hash, 64),
                    _clean_text(reference_brief_hash, 64),
                ),
            )
        return proposal_id

    def record_ai_bridge_event(
        self,
        *,
        session_id: str,
        phase: str,
        round_index: int,
        provider: str,
        model: str,
        status: str,
        objective_hash: str,
        critique: Mapping[str, Any],
        response_hash: str,
    ) -> str:
        """Store bounded dialogue telemetry, never prompts, coordinates or model reasoning."""
        event_id = str(uuid.uuid4())
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO ai_bridge_events(
                    id,created_at,session_id,phase,round_index,provider,model,status,
                    objective_hash,critique_json,response_hash
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event_id, _utc_now(), _clean_text(session_id, 64), _identifier(phase),
                    max(0, min(10, int(round_index))), _identifier(provider),
                    _clean_text(model, 500), _identifier(status), _clean_text(objective_hash, 64),
                    _json(critique), _clean_text(response_hash, 64),
                ),
            )
        return event_id

    def record_qa(
        self,
        experience_id: str,
        gate: str,
        status: str,
        *,
        evidence: Mapping[str, Any] | Sequence[Any] | None = None,
        score: float | None = None,
    ) -> dict[str, Any]:
        gate = _identifier(gate)
        status = _identifier(status).upper()
        if not gate or not status:
            raise ValueError("QA gate and status are required")
        numeric_score = None if score is None else max(0.0, min(1.0, float(score)))
        with self._transaction() as connection:
            self._require_experience(connection, experience_id)
            connection.execute(
                """
                INSERT INTO qa_results(experience_id, gate, status, score, evidence_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(experience_id, gate) DO UPDATE SET
                    status=excluded.status, score=excluded.score,
                    evidence_json=excluded.evidence_json, created_at=excluded.created_at
                """,
                (experience_id, gate, status, numeric_score, _json(evidence or {}), _utc_now()),
            )
            connection.execute(
                "UPDATE experiences SET status='QA_RECORDED', updated_at=? WHERE id=?",
                (_utc_now(), experience_id),
            )
        return self.evaluate_promotion(experience_id)

    def attach_artifact(self, experience_id: str, artifact_path: str | Path) -> None:
        path = Path(artifact_path).resolve()
        digest = _sha256(path) if path.is_file() else ""
        with self._transaction() as connection:
            self._require_experience(connection, experience_id)
            connection.execute(
                """UPDATE experiences
                   SET artifact_path=?, artifact_sha256=?, updated_at=? WHERE id=?""",
                (str(path), digest, _utc_now(), experience_id),
            )

    def mark_failed(self, experience_id: str, error: BaseException | str) -> None:
        message = _clean_text(str(error), 4_000)
        with self._transaction() as connection:
            self._require_experience(connection, experience_id)
            connection.execute(
                "UPDATE experiences SET status='FAILED', failure_reason=?, updated_at=? WHERE id=?",
                (message, _utc_now(), experience_id),
            )
            self._set_linked_proposal_status(connection, self._require_experience(connection, experience_id), "REJECTED")

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
        verdict = verdict.strip().upper()
        if verdict not in HUMAN_VERDICTS:
            raise ValueError(f"Unsupported human verdict: {verdict}")
        errors = max(0, int(canary_console_errors))
        gate = _identifier(gate)
        if not gate:
            raise ValueError("Human validation gate cannot be empty")
        feedback_id = str(uuid.uuid4())
        prepared = tuple(_normalize_observation(item) for item in observations)
        with self._transaction() as connection:
            self._require_experience(connection, experience_id)
            connection.execute(
                """
                INSERT INTO human_feedback(
                    id, experience_id, verdict, validator, notes,
                    canary_console_errors, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    experience_id,
                    verdict,
                    _clean_text(validator, 200) or "human",
                    _clean_text(notes, 8_000),
                    errors,
                    _utc_now(),
                ),
            )
            for observation in prepared:
                connection.execute(
                    """
                    INSERT INTO spatial_observations(
                        id, feedback_id, experience_id, x, y, z, category,
                        verdict, severity, message, lesson, details_json, created_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        feedback_id,
                        experience_id,
                        observation["x"],
                        observation["y"],
                        observation["z"],
                        observation["category"],
                        observation["verdict"],
                        observation["severity"],
                        observation["message"],
                        observation["lesson"],
                        _json(observation["details"]),
                        _utc_now(),
                    ),
                )
            gate_status = "PASS" if verdict == "PASS" and errors == 0 else "FAIL"
            connection.execute(
                """
                INSERT INTO qa_results(experience_id, gate, status, score, evidence_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(experience_id, gate) DO UPDATE SET
                    status=excluded.status, score=excluded.score,
                    evidence_json=excluded.evidence_json, created_at=excluded.created_at
                """,
                (
                    experience_id,
                    gate,
                    gate_status,
                    1.0 if gate_status == "PASS" else 0.0,
                    _json({"feedback_id": feedback_id, "verdict": verdict, "console_errors": errors}),
                    _utc_now(),
                ),
            )
        return self.evaluate_promotion(experience_id)

    def evaluate_promotion(self, experience_id: str) -> dict[str, Any]:
        with self._transaction() as connection:
            experience = self._require_experience(connection, experience_id)
            gates = {
                row["gate"]: row["status"]
                for row in connection.execute(
                    "SELECT gate, status FROM qa_results WHERE experience_id=?",
                    (experience_id,),
                )
            }
            missing = [gate for gate in REQUIRED_PROMOTION_GATES if gate not in gates]
            failed = [
                gate
                for gate in REQUIRED_PROMOTION_GATES
                if gate in gates and gates[gate] not in POSITIVE_GATE_STATES
            ]
            failed.extend(
                gate
                for gate, gate_status in gates.items()
                if gate not in failed and gate_status in HARD_FAILURE_STATES
            )
            if failed:
                status = "REJECTED"
            elif missing:
                status = "AWAITING_GATES"
            else:
                status = "PROMOTED"
            connection.execute(
                "UPDATE experiences SET status=?, updated_at=? WHERE id=?",
                (status, _utc_now(), experience_id),
            )
            if status == "PROMOTED":
                self._promote_lessons(connection, experience)
                self._set_linked_proposal_status(connection, experience, "PROMOTED")
            elif status == "REJECTED":
                self._promote_negative_lessons(connection, experience)
                self._set_linked_proposal_status(connection, experience, "REJECTED")
        return {
            "experience_id": experience_id,
            "status": status,
            "missing_gates": missing,
            "failed_gates": failed,
            "gates": dict(sorted(gates.items())),
        }

    def guidance(self, objective: str, *, limit: int = 16) -> dict[str, Any]:
        tokens = _tokens(objective)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, category, polarity, rule_json, confidence, objective_tokens
                FROM learned_rules WHERE active=1 ORDER BY confidence DESC, created_at DESC
                LIMIT 1000
                """
            ).fetchall()
        ranked: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            rule_tokens = set(str(row["objective_tokens"]).split())
            overlap = len(tokens & rule_tokens)
            if tokens and rule_tokens and not overlap:
                continue
            score = float(row["confidence"]) * (1.0 + overlap * 0.35)
            ranked.append((score, row))
        ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
        selected = ranked[: max(1, min(100, int(limit)))]
        rules = [
            {
                "id": row["id"],
                "category": row["category"],
                "polarity": row["polarity"],
                "confidence": round(score, 6),
                "rule": json.loads(row["rule_json"]),
            }
            for score, row in selected
        ]
        return {
            "status": "READY",
            "source": str(self.database_path),
            "objective_tokens": sorted(tokens),
            "positive_rules": [rule for rule in rules if rule["polarity"] == "positive"],
            "negative_constraints": [rule for rule in rules if rule["polarity"] == "negative"],
            "stores_source_geometry": False,
            "requires_human_validation_for_positive_learning": True,
        }

    def experience(self, experience_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = self._require_experience(connection, experience_id)
            gates = [dict(item) for item in connection.execute(
                "SELECT gate, status, score, evidence_json, created_at FROM qa_results WHERE experience_id=? ORDER BY gate",
                (experience_id,),
            )]
            observations = [dict(item) for item in connection.execute(
                """SELECT x, y, z, category, verdict, severity, message, lesson, details_json
                   FROM spatial_observations WHERE experience_id=? ORDER BY created_at""",
                (experience_id,),
            )]
        payload = dict(row)
        for key in ("planner_snapshot_json", "context_json"):
            payload[key.removesuffix("_json")] = json.loads(payload.pop(key))
        for item in gates:
            item["evidence"] = json.loads(item.pop("evidence_json"))
        for item in observations:
            item["details"] = json.loads(item.pop("details_json"))
        payload["qa"] = gates
        payload["observations"] = observations
        return payload

    def ingest_canary_attestation(
        self,
        attestation_path: str | Path,
        *,
        experience_id: str | None = None,
    ) -> dict[str, Any]:
        path = Path(attestation_path).resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        evidence = payload.get("evidence", {})
        if experience_id is None:
            experience_id = f"attestation-{_sha256(path)[:24]}"
            with self._connect() as connection:
                if connection.execute("SELECT 1 FROM experiences WHERE id=?", (experience_id,)).fetchone():
                    return self.evaluate_promotion(experience_id)
            experience_id = self.start_experience(
                f"Canary manual validation: {payload.get('map', path.stem)}",
                source_kind="reference_validation",
                context={"attestation": str(path), "package_sha256": payload.get("package_sha256", "")},
                artifact_path=payload.get("map", "") or None,
                experience_id=experience_id,
            )
        map_opened = bool(evidence.get("map_opened", evidence.get("map_opened_successfully", False)))
        verdict = "PASS" if payload.get("status") == "PASS" and map_opened else "FAIL"
        return self.record_human_validation(
            experience_id,
            verdict,
            validator=str(payload.get("validator", "Canary/RME manual attestation")),
            notes="Imported signed local validation evidence.",
            canary_console_errors=int(evidence.get("console_error_count", 0)),
        )

    def audit(self) -> dict[str, Any]:
        with self._connect() as connection:
            counts = {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("experiences", "qa_results", "human_feedback", "spatial_observations", "learned_rules", "ai_planning_proposals", "ai_bridge_events")
            }
            statuses = dict(connection.execute(
                "SELECT status, COUNT(*) FROM experiences GROUP BY status ORDER BY status"
            ).fetchall())
        return {
            "status": "PASS",
            "schema_version": SCHEMA_VERSION,
            "database": str(self.database_path),
            "required_promotion_gates": list(REQUIRED_PROMOTION_GATES),
            "counts": counts,
            "experience_statuses": statuses,
            "raw_reference_geometry_stored": False,
        }

    def _promote_lessons(self, connection: sqlite3.Connection, experience: sqlite3.Row) -> None:
        observations = connection.execute(
            """SELECT category, verdict, lesson, message FROM spatial_observations
               WHERE experience_id=? AND verdict='PASS'""",
            (experience["id"],),
        ).fetchall()
        rules = [
            (row["category"], row["lesson"] or row["message"], "positive", 1.0)
            for row in observations
            if row["lesson"] or row["message"]
        ]
        if not rules:
            rules.append(("validated_plan", "Preserve the validated abstract planner policies for similar objectives.", "positive", 0.75))
        proposal = self._linked_proposal(connection, experience)
        if proposal is not None:
            guidance = json.loads(proposal["guidance_json"])
            for category in ("architecture_rules", "biome_rules"):
                rules.extend(
                    (f"ai_{category}", str(instruction), "positive", 0.7)
                    for instruction in list(guidance.get(category, ()))[:12]
                    if str(instruction).strip()
                )
            rules.extend(
                (
                    "ai_material_intent",
                    f"For {intent.get('zone_role', 'zone')}, prefer certified brushes "
                    f"{intent.get('ground_key', '')} {intent.get('wall_key', '')} "
                    f"after contextual validation.",
                    "positive",
                    0.72,
                )
                for intent in list(guidance.get("material_intents", ()))[:16]
                if isinstance(intent, Mapping)
            )
        self._insert_rules(connection, experience, rules)

    @staticmethod
    def _linked_proposal(connection: sqlite3.Connection, experience: sqlite3.Row) -> sqlite3.Row | None:
        try:
            snapshot = json.loads(experience["planner_snapshot_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        proposal_id = str(
            snapshot.get("reference_style", {}).get("semantic_ai", {}).get("proposal_id", "")
        )
        if not proposal_id:
            return None
        return connection.execute("SELECT * FROM ai_planning_proposals WHERE id=?", (proposal_id,)).fetchone()

    def _set_linked_proposal_status(
        self, connection: sqlite3.Connection, experience: sqlite3.Row, status: str
    ) -> None:
        proposal = self._linked_proposal(connection, experience)
        if proposal is None:
            return
        connection.execute(
            "UPDATE ai_planning_proposals SET learning_status=?,linked_experience_id=?,updated_at=? WHERE id=?",
            (status, experience["id"], _utc_now(), proposal["id"]),
        )

    def _promote_negative_lessons(self, connection: sqlite3.Connection, experience: sqlite3.Row) -> None:
        observations = connection.execute(
            """SELECT category, lesson, message, severity FROM spatial_observations
               WHERE experience_id=? AND verdict IN ('FAIL', 'NEEDS_REPAIR')""",
            (experience["id"],),
        ).fetchall()
        rules = [
            (
                row["category"],
                row["lesson"] or row["message"],
                "negative",
                {"low": 0.55, "medium": 0.7, "high": 0.9, "critical": 1.0}.get(row["severity"], 0.7),
            )
            for row in observations
            if row["lesson"] or row["message"]
        ]
        self._insert_rules(connection, experience, rules)

    def _insert_rules(
        self,
        connection: sqlite3.Connection,
        experience: sqlite3.Row,
        rules: Iterable[tuple[str, str, str, float]],
    ) -> None:
        objective_tokens = " ".join(sorted(_tokens(experience["objective"])))
        for category, lesson, polarity, confidence in rules:
            lesson = _clean_text(lesson, 2_000)
            if not lesson:
                continue
            signature = hashlib.sha256(
                f"{category}\0{polarity}\0{lesson.casefold()}".encode("utf-8")
            ).hexdigest()
            connection.execute(
                """
                INSERT INTO learned_rules(
                    id, experience_id, category, polarity, rule_json, confidence,
                    objective_tokens, active, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    confidence=MAX(confidence, excluded.confidence), active=1
                """,
                (
                    signature,
                    experience["id"],
                    _identifier(category),
                    polarity,
                    _json({"instruction": lesson, "abstract_only": True}),
                    max(0.0, min(1.0, confidence)),
                    objective_tokens,
                    _utc_now(),
                ),
            )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS experiences(
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    planner_snapshot_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    failure_reason TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS qa_results(
                    experience_id TEXT NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
                    gate TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(experience_id, gate)
                );
                CREATE TABLE IF NOT EXISTS human_feedback(
                    id TEXT PRIMARY KEY,
                    experience_id TEXT NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
                    verdict TEXT NOT NULL,
                    validator TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    canary_console_errors INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS spatial_observations(
                    id TEXT PRIMARY KEY,
                    feedback_id TEXT NOT NULL REFERENCES human_feedback(id) ON DELETE CASCADE,
                    experience_id TEXT NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
                    x INTEGER, y INTEGER, z INTEGER,
                    category TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_observations_experience
                    ON spatial_observations(experience_id, category);
                CREATE TABLE IF NOT EXISTS learned_rules(
                    id TEXT PRIMARY KEY,
                    experience_id TEXT NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
                    category TEXT NOT NULL,
                    polarity TEXT NOT NULL,
                    rule_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    objective_tokens TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_rules_active
                    ON learned_rules(active, polarity, category);
                CREATE TABLE IF NOT EXISTS ai_planning_proposals(
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider_status TEXT NOT NULL,
                    learning_status TEXT NOT NULL,
                    guidance_json TEXT NOT NULL,
                    material_catalog_hash TEXT NOT NULL,
                    reference_brief_hash TEXT NOT NULL,
                    linked_experience_id TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ai_proposals_learning
                    ON ai_planning_proposals(learning_status, created_at);
                CREATE TABLE IF NOT EXISTS ai_bridge_events(
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    round_index INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    objective_hash TEXT NOT NULL,
                    critique_json TEXT NOT NULL,
                    response_hash TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ai_bridge_session
                    ON ai_bridge_events(session_id, round_index);
                """
            )
            connection.execute(
                """INSERT INTO schema_meta(key, value) VALUES('schema_version', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (str(SCHEMA_VERSION),),
            )
            connection.commit()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=15.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=15000")
        connection.execute("PRAGMA journal_mode=WAL")
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _require_experience(connection: sqlite3.Connection, experience_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM experiences WHERE id=?", (experience_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown experience: {experience_id}")
        return row


def _normalize_observation(value: Mapping[str, Any]) -> dict[str, Any]:
    verdict = str(value.get("verdict", "NEEDS_REPAIR")).strip().upper()
    if verdict not in HUMAN_VERDICTS:
        raise ValueError(f"Unsupported observation verdict: {verdict}")
    severity = str(value.get("severity", "medium")).strip().lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError(f"Unsupported observation severity: {severity}")
    coordinates = []
    for key in ("x", "y", "z"):
        raw = value.get(key)
        coordinates.append(None if raw is None else int(raw))
    return {
        "x": coordinates[0],
        "y": coordinates[1],
        "z": coordinates[2],
        "category": _identifier(str(value.get("category", "visual"))) or "visual",
        "verdict": verdict,
        "severity": severity,
        "message": _clean_text(str(value.get("message", "")), 4_000),
        "lesson": _clean_text(str(value.get("lesson", "")), 2_000),
        "details": value.get("details", {}) if isinstance(value.get("details", {}), Mapping) else {},
    }


def _json(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("Experience JSON payload exceeds the 2 MB safety limit")
    return encoded


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]{3,}", value.casefold()) if token not in {"para", "with", "from", "mapa"}}


def _identifier(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip())[:120]


def _clean_text(value: str, limit: int) -> str:
    return " ".join(str(value).replace("\x00", " ").split())[:limit]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "ExperienceLearningLoop",
    "REQUIRED_PROMOTION_GATES",
    "default_experience_database",
]

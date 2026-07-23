"""Certified Mapper Planner facade consumed by the desktop Workspace."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any

from core.world_generator.color_first_map_pipeline import generate_color_first_map
from core.world_generator.experience_learning_loop import ExperienceLearningLoop
from core.world_generator.planner_database_client import PlannerDatabaseClient
from core.editor.planner_bridge import WorkspacePlannerBridge


class WorkspaceAgentService:
    """Run the modern planner/materializer while keeping the UI dependency-free."""

    def __init__(
        self,
        root: str | Path,
        asset_root: str | Path | None = None,
        material_root: str | Path | None = None,
        data_root: str | Path | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.asset_root = Path(asset_root).resolve() if asset_root else self.root / "assets"
        self.material_root = Path(material_root).resolve() if material_root else None
        self.data_root = Path(data_root).resolve() if data_root else self.root
        self.planner = WorkspacePlannerBridge(self.root)
        self._prepared_lock = RLock()
        self._prepared_objective = ""
        self._prepared_plan: Any | None = None
        self._prepared_audit: dict[str, Any] | None = None
        try:
            self.learning = PlannerDatabaseClient(self.data_root)
            self.database_server_mode = "LOCAL_SERVER"
        except (OSError, RuntimeError, ValueError):
            self.learning = ExperienceLearningLoop.for_root(self.data_root)
            self.database_server_mode = "DIRECT_FALLBACK"

    def propose(self, objective: str) -> dict[str, Any]:
        objective = " ".join(str(objective).split())
        if not objective:
            raise ValueError("Mapper objective cannot be empty")
        plan, audit = self.planner.create_plan(objective)
        with self._prepared_lock:
            self._prepared_objective = objective
            self._prepared_plan = plan
            self._prepared_audit = dict(audit)
        return audit

    def generate(
        self,
        objective: str,
        *,
        output_name: str = "workspace_generated.otbm",
    ) -> dict[str, Any]:
        objective = " ".join(str(objective).split())
        if not objective:
            raise ValueError("Mapper objective cannot be empty")
        output_name = Path(output_name).name
        if not output_name.lower().endswith(".otbm"):
            output_name += ".otbm"
        (self.root / "exports").mkdir(parents=True, exist_ok=True)
        with self._prepared_lock:
            if objective == self._prepared_objective and self._prepared_plan is not None:
                plan = self._prepared_plan
                planner_audit = dict(self._prepared_audit or {})
                self._prepared_objective = ""
                self._prepared_plan = None
                self._prepared_audit = None
                reused_certified_plan = True
            else:
                plan = None
                planner_audit = {}
                reused_certified_plan = False
        if plan is None:
            plan, planner_audit = self.planner.create_plan(objective)
        report = generate_color_first_map(
            plan,
            root=self.root,
            asset_root=self.asset_root,
            material_root=self.material_root,
            output_name=output_name,
        )
        report["workspace_agent"] = {
            "status": "PASS",
            "planner": planner_audit,
            "official_asset_root": str(self.asset_root),
            "official_material_root": str(self.material_root) if self.material_root else "auto",
            "ui_writes_tiles_directly": False,
            "reused_certified_proposal_plan": reused_certified_plan,
        }
        return report

    def validate_experience(
        self,
        experience_id: str,
        verdict: str,
        *,
        notes: str = "",
        validator: str = "Workspace user",
        canary_console_errors: int = 0,
        observations: list[dict[str, Any]] | None = None,
        gate: str = "canary_manual",
    ) -> dict[str, Any]:
        """Attach human/Canary evidence and spatial lessons to one generation."""
        return self.learning.record_human_validation(
            experience_id,
            verdict,
            notes=notes,
            validator=validator,
            canary_console_errors=canary_console_errors,
            observations=observations or (),
            gate=gate,
        )

    def experience(self, experience_id: str) -> dict[str, Any]:
        return self.learning.experience(experience_id)

    def learning_guidance(self, objective: str, *, limit: int = 16) -> dict[str, Any]:
        return self.learning.guidance(objective, limit=limit)

    def ai_preferences(self) -> dict[str, Any]:
        return self.planner.ai_preferences()

    def set_ai_mode(self, mode: str) -> dict[str, Any]:
        return self.planner.set_ai_mode(mode)

    def record_workspace_export(
        self,
        otbm_path: str | Path,
        *,
        objective: str = "",
    ) -> dict[str, Any]:
        """Register a manually edited Workspace export in the learning lifecycle."""
        path = Path(otbm_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        experience_id = self.learning.start_experience(
            objective or f"Workspace map export: {path.stem}",
            planner_snapshot={},
            context={"pipeline": "workspace_transactional_export", "manual_edit": True},
            source_kind="workspace_export",
            artifact_path=path,
        )
        self.learning.attach_artifact(experience_id, path)
        try:
            from core.editor.otbm_corpus_roundtrip import OTBMCorpusRoundtripCertifier

            roundtrip = OTBMCorpusRoundtripCertifier().certify((path,)).to_dict()
            self.learning.record_qa(
                experience_id,
                "otbm_roundtrip",
                roundtrip["status"],
                evidence=roundtrip,
                score=1.0 if roundtrip["status"] == "PASS" else 0.0,
            )
            from core.editor.item_safety_certifier import OTBMItemSafetyCertifier

            safety = OTBMItemSafetyCertifier(self.root).certify(path).to_dict()
            self.learning.record_qa(
                experience_id,
                "material_safety",
                safety["status"],
                evidence=safety,
                score=1.0 if safety["status"] == "PASS" else 0.0,
            )
        except Exception as exc:
            self.learning.mark_failed(experience_id, exc)
            raise
        return self.learning.evaluate_promotion(experience_id)

    def audit(self) -> dict[str, Any]:
        return {
            "status": "PASS",
            "root": str(self.root),
            "asset_root": str(self.asset_root),
            "material_root": str(self.material_root) if self.material_root else "auto",
            "data_root": str(self.data_root),
            "planner": self.planner.audit(),
            "experience_learning": self.learning.audit(),
            "database_server_mode": self.database_server_mode,
            "pipeline": "Mapper Planner -> color masks -> RME Brush Engine -> OTBM",
        }


__all__ = ["WorkspaceAgentService"]

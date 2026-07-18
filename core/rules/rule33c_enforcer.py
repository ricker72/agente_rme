"""
RULE-33-C — Semantic Design Before Materialization

The generation pipeline must follow:

Knowledge Extraction
→ Semantic Design
→ Architectural Realization
→ Materialization
→ OTBM Export

Forbidden order:

Knowledge Extraction
→ Direct OTBM Export

The agent must first design the city semantically and architecturally before
any OTBM generation occurs.

The semantic model remains the source of truth.

The OTBM export is only a materialized representation of the approved
architectural model.

Certification blocker:

DIRECT_EXPORT_WITHOUT_ARCHITECTURE
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pipeline phase identifiers
# ---------------------------------------------------------------------------

PHASE_KNOWLEDGE_EXTRACTION = "knowledge_extraction"
PHASE_SEMANTIC_DESIGN = "semantic_design"
PHASE_ARCHITECTURAL_REALIZATION = "architectural_realization"
PHASE_MATERIALIZATION = "materialization"
PHASE_OTBM_EXPORT = "otbm_export"

CANONICAL_PIPELINE_ORDER = [
    PHASE_KNOWLEDGE_EXTRACTION,
    PHASE_SEMANTIC_DESIGN,
    PHASE_ARCHITECTURAL_REALIZATION,
    PHASE_MATERIALIZATION,
    PHASE_OTBM_EXPORT,
]

BLOCKER_DIRECT_EXPORT = "DIRECT_EXPORT_WITHOUT_ARCHITECTURE"
BLOCKER_SEMANTIC_DESIGN_MISSING = "SEMANTIC_DESIGN_MISSING"
BLOCKER_ARCHITECTURAL_REALIZATION_MISSING = "ARCHITECTURAL_REALIZATION_MISSING"
BLOCKER_MATERIALIZATION_MISSING = "MATERIALIZATION_MISSING"

# ---------------------------------------------------------------------------
# Artifact verification helpers
# ---------------------------------------------------------------------------


@dataclass
class PhaseArtifactSet:
    """Required artifacts that prove a pipeline phase has been completed."""

    description: str
    required_files: list[str] = field(default_factory=list)
    required_json_keys: dict[str, list[str]] = field(default_factory=dict)


# Artifacts proving Semantic Design phase completed
SEMANTIC_DESIGN_ARTIFACTS = PhaseArtifactSet(
    description="WG-19A Semantic City Designer artifacts",
    required_files=[
        "roadmap/v1.1/WG19A_INPUT_AUDIT.json",
        "roadmap/v1.1/WG19A_REFERENCE_STYLE_ANALYSIS.json",
        "roadmap/v1.1/WG19A_NECRO_DESIGN_SPEC.json",
        "roadmap/v1.1/WG19A_CITY_MACRO_LAYOUT.json",
        "roadmap/v1.1/WG19A_DISTRICT_PLAN.json",
        "roadmap/v1.1/WG19A_SERVICE_PLAN.json",
        "roadmap/v1.1/WG19A_ROAD_NETWORK_PLAN.json",
        "roadmap/v1.1/WG19A_HUNT_DESIGN_PLAN.json",
        "roadmap/v1.1/WG19A_MULTIFLOOR_PLAN.json",
        "roadmap/v1.1/WG19A_SEMANTIC_PLACEMENT_RULES.json",
        "roadmap/v1.1/WG19A_UNIQUENESS_SEED.json",
        "roadmap/v1.1/WG19A_FINAL_LOCATION_PLAN.json",
        "roadmap/v1.1/WG19A_DESIGN_VALIDATION.json",
        "roadmap/v1.1/WG19A_QUALITY_REPORT.json",
        "roadmap/v1.1/WG19A_REPORT.json",
        "roadmap/v1.1/WG19A_DEPENDENCY_AUDIT.json",
        "roadmap/v1.1/WG19A_CERTIFICATION.json",
    ],
    required_json_keys={
        "roadmap/v1.1/WG19A_CERTIFICATION.json": ["status", "checks"],
    },
)

# Artifacts proving Architectural Realization phase completed
ARCHITECTURAL_REALIZATION_ARTIFACTS = PhaseArtifactSet(
    description="WG-19H Architectural Realization Engine artifacts",
    required_files=[
        "roadmap/v1.1/WG19H_ARCHITECTURAL_REFERENCE_AUDIT.json",
        "roadmap/v1.1/WG19H_STYLE_PROFILE_VENORE.json",
        "roadmap/v1.1/WG19H_STYLE_PROFILE_ORAMOND.json",
        "roadmap/v1.1/WG19H_STYLE_PROFILE_KRAILOS.json",
        "roadmap/v1.1/WG19H_UNIQUENESS_PROFILE.json",
        "roadmap/v1.1/WG19H_NECRO_ARCHITECTURAL_BLUEPRINT.json",
        "roadmap/v1.1/WG19H_FLOOR_REALIZATION_PLAN.json",
        "roadmap/v1.1/WG19H_FLOOR_DISTRIBUTION_AUDIT.json",
        "roadmap/v1.1/WG19H_BUILDING_REALIZATION.json",
        "roadmap/v1.1/WG19H_INTERIOR_REALIZATION.json",
        "roadmap/v1.1/WG19H_ROAD_NETWORK.json",
        "roadmap/v1.1/WG19H_WATER_AUDIT.json",
        "roadmap/v1.1/WG19H_BRIDGE_NETWORK.json",
        "roadmap/v1.1/WG19H_HUNT_REALIZATION.json",
        "roadmap/v1.1/WG19H_ARCHITECTURAL_TILE_MODEL.json",
        "roadmap/v1.1/WG19H_VISUAL_PLAUSIBILITY_AUDIT.json",
        "roadmap/v1.1/WG19H_QUALITY_REPORT.json",
        "roadmap/v1.1/WG19H_REPORT.json",
        "roadmap/v1.1/WG19H_CERTIFICATION.json",
    ],
    required_json_keys={
        "roadmap/v1.1/WG19H_CERTIFICATION.json": ["status", "checks"],
    },
)

# Artifacts proving Materialization phase completed
MATERIALIZATION_ARTIFACTS = PhaseArtifactSet(
    description="WG-18HH-F Authoritative OTBM Materialization artifacts",
    required_files=[
        "roadmap/v1.1/WG18HHF_INPUT_AUDIT.json",
        "roadmap/v1.1/WG18HHF_CITY_MODEL_VALIDATION.json",
        "roadmap/v1.1/WG18HHF_TILE_MATERIALIZATION_AUDIT.json",
        "roadmap/v1.1/WG18HHF_TOWN_MATERIALIZATION_AUDIT.json",
        "roadmap/v1.1/WG18HHF_ITEM_VALIDATION_AUDIT.json",
        "roadmap/v1.1/WG18HHF_GROUND_VALIDATION_AUDIT.json",
        "roadmap/v1.1/WG18HHF_OTBM_GENERATION_AUDIT.json",
        "roadmap/v1.1/WG18HHF_PROVENANCE_VALIDATION.json",
        "roadmap/v1.1/WG18HHF_RME_PRECHECK.json",
        "roadmap/v1.1/WG18HHF_QUALITY_REPORT.json",
        "roadmap/v1.1/WG18HHF_REPORT.json",
        "roadmap/v1.1/WG18HHF_CERTIFICATION.json",
    ],
    required_json_keys={
        "roadmap/v1.1/WG18HHF_CERTIFICATION.json": ["status", "certification"],
    },
)


# ---------------------------------------------------------------------------
# Core enforcer
# ---------------------------------------------------------------------------


@dataclass
class Rule33CResult:
    """Result of a RULE-33-C enforcement check."""

    passed: bool = False
    blocker: str | None = None
    current_phase: str | None = None
    last_completed_phase: str | None = None
    missing_artifacts: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": "RULE-33-C",
            "passed": self.passed,
            "blocker": self.blocker,
            "current_phase": self.current_phase,
            "last_completed_phase": self.last_completed_phase,
            "missing_artifacts": self.missing_artifacts,
            "details": self.details,
        }


class Rule33CEnforcer:
    """
    Enforces the mandatory pipeline order:

        Knowledge Extraction
        → Semantic Design
        → Architectural Realization
        → Materialization
        → OTBM Export

    Before any phase can proceed, all required artifacts from the previous
    phase must exist and be valid.  The enforcer blocks OTBM export if
    Semantic Design and Architectural Realization have not been completed.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        self.root = project_root or Path(__file__).resolve().parents[2]
        self.roadmap = self.root / "roadmap" / "v1.1"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_pipeline_readiness(
        self, target_phase: str = PHASE_OTBM_EXPORT
    ) -> Rule33CResult:
        """
        Check whether all prerequisite phases for *target_phase* have been
        completed.

        Args:
            target_phase: The phase the caller wants to execute.
                          One of the PHASE_* constants.

        Returns:
            Rule33CResult: passed=True only when every phase before
                           *target_phase* has its artifacts verified.
        """
        target_idx = self._phase_index(target_phase)
        if target_idx is None:
            return Rule33CResult(
                passed=False,
                blocker=BLOCKER_DIRECT_EXPORT,
                current_phase=target_phase,
                details={"error": f"Unknown target phase: {target_phase}"},
            )

        # A direct OTBM export without going through the pipeline is always
        # forbidden if no design phase has completed.
        if target_phase == PHASE_OTBM_EXPORT:
            semantic_ok = self._verify_phase(PHASE_SEMANTIC_DESIGN)
            arch_ok = self._verify_phase(PHASE_ARCHITECTURAL_REALIZATION)
            if not semantic_ok.passed:
                return Rule33CResult(
                    passed=False,
                    blocker=BLOCKER_SEMANTIC_DESIGN_MISSING,
                    current_phase=target_phase,
                    last_completed_phase=PHASE_KNOWLEDGE_EXTRACTION,
                    details={
                        "message": (
                            "Semantic Design phase (WG-19A) must be completed "
                            "before OTBM export. The semantic model is the "
                            "source of truth."
                        ),
                        "canonical_pipeline": CANONICAL_PIPELINE_ORDER,
                        "forbidden_pattern": "Knowledge Extraction → Direct OTBM Export",
                    },
                )
            if not arch_ok.passed:
                return Rule33CResult(
                    passed=False,
                    blocker=BLOCKER_ARCHITECTURAL_REALIZATION_MISSING,
                    current_phase=target_phase,
                    last_completed_phase=PHASE_SEMANTIC_DESIGN,
                    details={
                        "message": (
                            "Architectural Realization phase (WG-19H) must be "
                            "completed before OTBM export. The OTBM export is "
                            "only a materialized representation of the approved "
                            "architectural model."
                        ),
                        "canonical_pipeline": CANONICAL_PIPELINE_ORDER,
                        "missing_arch_artifacts": arch_ok.missing_artifacts,
                    },
                )

            # Check materialization too when targeting OTBM export
            mat_ok = self._verify_phase(PHASE_MATERIALIZATION)
            if not mat_ok.passed:
                return Rule33CResult(
                    passed=False,
                    blocker=BLOCKER_MATERIALIZATION_MISSING,
                    current_phase=target_phase,
                    last_completed_phase=PHASE_ARCHITECTURAL_REALIZATION,
                    details={
                        "message": (
                            "Materialization phase (WG-18HH-F) must be "
                            "completed before OTBM export."
                        ),
                        "missing_mat_artifacts": mat_ok.missing_artifacts,
                    },
                )

            return Rule33CResult(
                passed=True,
                current_phase=target_phase,
                last_completed_phase=PHASE_MATERIALIZATION,
                details={
                    "message": "All prerequisite phases verified. OTBM export permitted.",
                    "canonical_pipeline": CANONICAL_PIPELINE_ORDER,
                },
            )

        # For non-OTBM-export phases, verify the immediate predecessor
        if target_idx > 0:
            prev_phase = CANONICAL_PIPELINE_ORDER[target_idx - 1]
            prev_ok = self._verify_phase(prev_phase)
            if not prev_ok.passed:
                return Rule33CResult(
                    passed=False,
                    blocker={
                        PHASE_SEMANTIC_DESIGN: BLOCKER_SEMANTIC_DESIGN_MISSING,
                        PHASE_ARCHITECTURAL_REALIZATION: (
                            BLOCKER_ARCHITECTURAL_REALIZATION_MISSING
                        ),
                        PHASE_MATERIALIZATION: BLOCKER_MATERIALIZATION_MISSING,
                    }.get(
                        target_phase, BLOCKER_DIRECT_EXPORT
                    ),
                    current_phase=target_phase,
                    last_completed_phase=CANONICAL_PIPELINE_ORDER[
                        max(0, target_idx - 2)
                    ]
                    if target_idx >= 2
                    else None,
                    missing_artifacts=prev_ok.missing_artifacts,
                    details={
                        "message": (
                            f"Phase '{prev_phase}' must be completed before "
                            f"'{target_phase}' can proceed."
                        ),
                        "canonical_pipeline": CANONICAL_PIPELINE_ORDER,
                        "missing_artifacts": prev_ok.missing_artifacts,
                    },
                )

        return Rule33CResult(
            passed=True,
            current_phase=target_phase,
            last_completed_phase=CANONICAL_PIPELINE_ORDER[
                max(0, target_idx - 1)
            ]
            if target_idx > 0
            else None,
            details={"message": f"Phase '{target_phase}' has no prerequisites."},
        )

    def assert_otbm_export_allowed(self) -> None:
        """
        Raise RuntimeError if OTBM export is attempted without completing
        the required design and architecture phases.

        This is the primary enforcement entry point for export commands.
        """
        result = self.check_pipeline_readiness(PHASE_OTBM_EXPORT)
        if not result.passed:
            msg = (
                f"RULE-33-C BLOCKER: {result.blocker}\n"
                f"  Pipeline order must be:\n"
                f"    Knowledge Extraction\n"
                f"    → Semantic Design\n"
                f"    → Architectural Realization\n"
                f"    → Materialization\n"
                f"    → OTBM Export\n"
                f"  Forbidden: Knowledge Extraction → Direct OTBM Export\n"
                f"  Last completed: {result.last_completed_phase}\n"
                f"  Current phase: {result.current_phase}\n"
            )
            if result.missing_artifacts:
                msg += f"  Missing artifacts: {', '.join(result.missing_artifacts)}\n"
            raise RuntimeError(msg)

    def assert_phase_allowed(self, phase: str) -> None:
        """
        Raise RuntimeError if the requested *phase* cannot proceed because
        its prerequisites have not been met.
        """
        result = self.check_pipeline_readiness(phase)
        if not result.passed:
            msg = (
                f"RULE-33-C BLOCKER: {result.blocker}\n"
                f"  Phase '{phase}' cannot proceed.\n"
                f"  Missing prerequisites from previous phase:\n"
            )
            if result.missing_artifacts:
                msg += (
                    f"    {', '.join(result.missing_artifacts)}\n"
                )
            if result.details.get("message"):
                msg += f"  {result.details['message']}\n"
            raise RuntimeError(msg)

    def generate_rule33c_report(self) -> dict[str, Any]:
        """
        Generate a comprehensive RULE-33-C compliance report covering all
        pipeline phases.
        """
        phases: dict[str, dict[str, Any]] = {}
        for phase in CANONICAL_PIPELINE_ORDER:
            verification = self._verify_phase(phase)
            phases[phase] = {
                "passed": verification.passed,
                "artifact_count": len(verification.missing_artifacts),
                "missing_artifacts": verification.missing_artifacts,
            }

        otbm_allowed = self.check_pipeline_readiness(PHASE_OTBM_EXPORT)

        return {
            "rule": "RULE-33-C",
            "title": "Semantic Design Before Materialization",
            "status": "PASS" if otbm_allowed.passed else "BLOCKED",
            "blocker": otbm_allowed.blocker if not otbm_allowed.passed else None,
            "canonical_pipeline": CANONICAL_PIPELINE_ORDER,
            "phases": phases,
            "otbm_export_permitted": otbm_allowed.passed,
            "forbidden_pattern": "Knowledge Extraction → Direct OTBM Export",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _phase_index(self, phase: str) -> int | None:
        try:
            return CANONICAL_PIPELINE_ORDER.index(phase)
        except ValueError:
            return None

    def _verify_phase(self, phase: str) -> Rule33CResult:
        """
        Verify that all required artifacts for *phase* exist.
        Returns a Rule33CResult with passed=True iff all artifacts check out.
        """
        artifact_set = self._artifact_set_for(phase)
        if artifact_set is None:
            # Knowledge Extraction is presupposed by the system
            return Rule33CResult(passed=True)

        missing: list[str] = []
        for rel_path in artifact_set.required_files:
            full = self.root / rel_path
            if not full.exists():
                missing.append(rel_path)

        # Check JSON key presence for files that do exist
        for rel_path, keys in artifact_set.required_json_keys.items():
            full = self.root / rel_path
            if not full.exists():
                continue  # already counted as missing
            try:
                data = json.loads(full.read_text(encoding="utf-8"))
                for key in keys:
                    if key not in data:
                        missing.append(f"{rel_path}: missing key '{key}'")
            except (json.JSONDecodeError, OSError) as exc:
                missing.append(f"{rel_path}: unreadable ({exc})")

        return Rule33CResult(
            passed=len(missing) == 0,
            missing_artifacts=missing,
        )

    @staticmethod
    def _artifact_set_for(phase: str) -> PhaseArtifactSet | None:
        mapping: dict[str, PhaseArtifactSet] = {
            PHASE_SEMANTIC_DESIGN: SEMANTIC_DESIGN_ARTIFACTS,
            PHASE_ARCHITECTURAL_REALIZATION: ARCHITECTURAL_REALIZATION_ARTIFACTS,
            PHASE_MATERIALIZATION: MATERIALIZATION_ARTIFACTS,
        }
        return mapping.get(phase)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def enforce_rule33c_otbm_export(project_root: Path | None = None) -> None:
    """
    Check RULE-33-C before OTBM export.  Raises RuntimeError if the pipeline
    order has been violated (direct export without architecture).
    """
    enforcer = Rule33CEnforcer(project_root)
    enforcer.assert_otbm_export_allowed()
    logger.info("RULE-33-C: OTBM export permitted — pipeline order verified.")


def enforce_rule33c_phase(
    phase: str, project_root: Path | None = None
) -> None:
    """
    Check RULE-33-C for a specific pipeline phase.
    Raises RuntimeError if the prerequisite phase(s) have not been completed.
    """
    enforcer = Rule33CEnforcer(project_root)
    enforcer.assert_phase_allowed(phase)
    logger.info(
        "RULE-33-C: Phase '%s' permitted — prerequisite artifacts verified.",
        phase,
    )


def rule33c_report(project_root: Path | None = None) -> dict[str, Any]:
    """
    Generate and return a RULE-33-C compliance report.
    """
    enforcer = Rule33CEnforcer(project_root)
    return enforcer.generate_rule33c_report()
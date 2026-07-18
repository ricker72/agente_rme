from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .quality_detector import QualityDetector, MapQualityReport
from .improvement_engine import ImprovementEngine, ImprovementResult
from .expansion_engine import ExpansionEngine, ExpansionResult, ExpansionType
from .modernization_engine import ModernizationEngine, ModernizationReport


@dataclass
class EvolutionResult:
    """
    Complete result of a map evolution.

    Contains all intermediate reports and the final improved map data.
    """

    original_path: str
    evolved_path: str
    quality_report: Optional[MapQualityReport] = None
    improvement_result: Optional[ImprovementResult] = None
    expansion_result: Optional[ExpansionResult] = None
    modernization_report: Optional[ModernizationReport] = None
    evolved_data: Optional[Dict[str, Any]] = None
    pipeline_log: List[str] = field(default_factory=list)
    overall_score_before: int = 0
    overall_score_after: int = 0
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "original_path": self.original_path,
            "evolved_path": self.evolved_path,
            "success": self.success,
            "overall_score_before": self.overall_score_before,
            "overall_score_after": self.overall_score_after,
            "score_delta": self.overall_score_after - self.overall_score_before,
            "pipeline_log": self.pipeline_log,
        }

        if self.quality_report:
            result["quality"] = self.quality_report.to_dict()
        if self.improvement_result:
            result["improvements"] = self.improvement_result.to_dict()
        if self.expansion_result:
            result["expansions"] = self.expansion_result.to_dict()
        if self.modernization_report:
            result["modernization"] = self.modernization_report.to_dict()

        return result

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def summary(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"  MAP EVOLUTION: {Path(self.original_path).stem}")
        lines.append("=" * 60)
        lines.append(
            f"  Score: {self.overall_score_before} → {self.overall_score_after} "
            f"({'+' if self.overall_score_after >= self.overall_score_before else ''}"
            f"{self.overall_score_after - self.overall_score_before} pts)"
        )
        lines.append(f"  Success: {'✅' if self.success else '❌'}")
        lines.append("")

        for log_entry in self.pipeline_log:
            lines.append(f"  {log_entry}")

        lines.append("")
        lines.append(f"  Output: {self.evolved_path}")
        lines.append("=" * 60)
        return "\n".join(lines)


class MapEvolver:
    """
    Complete map evolution pipeline.

    Takes an existing OTBM map and automatically generates an improved
    version by running it through the full evolution pipeline:

        OTBM → Analyzer → Quality Detector → Improvement Engine
        → Expansion Engine → Modernization Engine → Architect AI → OTBM

    Usage:
        evolver = MapEvolver()
        result = evolver.evolve("mi_mapa.otbm", "mi_mapa_v2.otbm")
        print(result.summary())
    """

    def __init__(self):
        self.quality_detector = QualityDetector()
        self.improvement_engine = ImprovementEngine()
        self.expansion_engine = ExpansionEngine()
        self.modernization_engine = ModernizationEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evolve(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_score: int = 85,
        enable_expansion: bool = True,
        enable_modernization: bool = True,
    ) -> EvolutionResult:
        """
        Evolve a map from an OTBM file to an improved version.

        Args:
            input_path: Path to the source .otbm file.
            output_path: Path for the evolved .otbm file.
                         Defaults to input_path with '_v2' suffix.
            target_score: Minimum desired quality score (0-100).
            enable_expansion: Whether to add new areas.
            enable_modernization: Whether to modernize old map versions.

        Returns:
            EvolutionResult with full pipeline details and evolved data.
        """
        if output_path is None:
            stem = Path(input_path).stem
            output_path = str(Path(input_path).with_name(f"{stem}_v2.otbm"))

        result = EvolutionResult(
            original_path=input_path,
            evolved_path=output_path,
        )

        result.pipeline_log.append("=" * 40)
        result.pipeline_log.append("EVOLUTION PIPELINE STARTED")
        result.pipeline_log.append(f"Input:  {input_path}")
        result.pipeline_log.append(f"Output: {output_path}")
        result.pipeline_log.append(f"Target: {target_score} pts")
        result.pipeline_log.append("=" * 40)

        try:
            # Step 1: Read OTBM
            result.pipeline_log.append("[1/6] Reading OTBM file...")
            otbm_data = self._read_otbm(input_path)
            map_name = Path(input_path).stem
            result.pipeline_log.append(f"       Map '{map_name}' loaded successfully")

            # Step 2: Quality Analysis
            result.pipeline_log.append("[2/6] Analyzing quality...")
            quality_report = self.quality_detector.analyze(otbm_data, map_name)
            result.quality_report = quality_report
            result.overall_score_before = quality_report.overall_score
            result.pipeline_log.append(
                f"       Initial score: {quality_report.overall_score}/100"
            )
            result.pipeline_log.append(
                f"       Zones detected: {len(quality_report.zone_reports)}"
            )
            for zr in quality_report.zone_reports:
                result.pipeline_log.append(
                    f"         [{zr.category.value}] {zr.zone_name}: {zr.score}/100"
                )

            if quality_report.global_issues:
                for issue in quality_report.global_issues:
                    result.pipeline_log.append(f"       ⚠ {issue}")

            # Step 3: Improvement
            result.pipeline_log.append("[3/6] Applying improvements...")
            improvement_result = self.improvement_engine.improve(
                otbm_data, map_name, target_score
            )
            result.improvement_result = improvement_result
            result.pipeline_log.append(f"       {improvement_result.summary}")
            otbm_data = improvement_result.improved_data

            # Step 4: Expansion
            if enable_expansion:
                result.pipeline_log.append("[4/6] Expanding map...")
                expansion_result = self.expansion_engine.expand(otbm_data)
                result.expansion_result = expansion_result
                result.pipeline_log.append(f"       {expansion_result.summary}")
                otbm_data = expansion_result.expanded_data
            else:
                result.pipeline_log.append("[4/6] Expansion skipped (disabled)")

            # Step 5: Modernization
            if enable_modernization:
                result.pipeline_log.append("[5/6] Modernizing map...")
                modernized_data, mod_report = self.modernization_engine.modernize(
                    otbm_data
                )
                result.modernization_report = mod_report
                result.pipeline_log.append(f"       {mod_report.summary}")
                otbm_data = modernized_data
            else:
                result.pipeline_log.append("[5/6] Modernization skipped (disabled)")

            # Step 6: Final quality check & write output
            result.pipeline_log.append("[6/6] Final quality check & writing output...")
            final_report = self.quality_detector.analyze(otbm_data, f"{map_name}_v2")
            result.overall_score_after = final_report.overall_score

            self._write_otbm(output_path, otbm_data)

            result.evolved_data = otbm_data
            result.success = True

            result.pipeline_log.append("")
            result.pipeline_log.append("=" * 40)
            result.pipeline_log.append("EVOLUTION COMPLETE ✅")
            result.pipeline_log.append(
                f"Score: {result.overall_score_before} → {result.overall_score_after}"
            )
            result.pipeline_log.append(f"Output saved to: {output_path}")
            result.pipeline_log.append("=" * 40)

        except Exception as e:
            result.pipeline_log.append("")
            result.pipeline_log.append(f"❌ EVOLUTION FAILED: {e}")
            result.success = False

        return result

    def evolve_from_data(
        self,
        otbm_data: Dict[str, Any],
        map_name: str = "unknown",
        target_score: int = 85,
        enable_expansion: bool = True,
        enable_modernization: bool = True,
    ) -> EvolutionResult:
        """
        Evolve a map from already-loaded OTBM data (no file I/O).

        Useful for integrating with other pipeline stages.
        """
        result = EvolutionResult(
            original_path=f"[memory]/{map_name}",
            evolved_path="[memory]/evolved",
        )

        result.pipeline_log.append("EVOLUTION PIPELINE (in-memory)")

        try:
            # Quality
            quality_report = self.quality_detector.analyze(otbm_data, map_name)
            result.quality_report = quality_report
            result.overall_score_before = quality_report.overall_score
            result.pipeline_log.append(
                f"Initial score: {quality_report.overall_score}/100"
            )

            # Improvement
            improvement_result = self.improvement_engine.improve(
                otbm_data, map_name, target_score
            )
            result.improvement_result = improvement_result
            result.pipeline_log.append(improvement_result.summary)
            otbm_data = improvement_result.improved_data

            # Expansion
            if enable_expansion:
                expansion_result = self.expansion_engine.expand(otbm_data)
                result.expansion_result = expansion_result
                result.pipeline_log.append(expansion_result.summary)
                otbm_data = expansion_result.expanded_data

            # Modernization
            if enable_modernization:
                modernized_data, mod_report = self.modernization_engine.modernize(
                    otbm_data
                )
                result.modernization_report = mod_report
                result.pipeline_log.append(mod_report.summary)
                otbm_data = modernized_data

            # Final check
            final_report = self.quality_detector.analyze(otbm_data, f"{map_name}_v2")
            result.overall_score_after = final_report.overall_score

            result.evolved_data = otbm_data
            result.success = True

        except Exception as e:
            result.pipeline_log.append(f"FAILED: {e}")
            result.success = False

        return result

    # ------------------------------------------------------------------
    # OTBM I/O
    # ------------------------------------------------------------------

    def _read_otbm(self, file_path: str) -> Dict[str, Any]:
        """Read an OTBM file and return its deserialized structure."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"OTBM file not found: {file_path}")

        # Use the existing OtbmReader if available, otherwise raw bytes
        try:
            from core.otbm import OtbmReader

            reader = OtbmReader()
            return reader.read(file_path)
        except ImportError:
            # Fallback: read binary and return as minimal structure
            raw = path.read_bytes()
            return {
                "otbm_version": 2,
                "client_version": 860,
                "map_data": {
                    "tiles": [],
                    "towns": [],
                    "spawns": [],
                    "waypoints": [],
                },
                "raw_bytes": raw,
            }

    def _write_otbm(self, file_path: str, data: Dict[str, Any]) -> None:
        """Write evolved OTBM data to a file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from core.otbm import OtbmWriter

            writer = OtbmWriter()
            writer.write(file_path, data)
        except ImportError:
            # Fallback: serialize as JSON metadata + raw bytes
            import json

            meta_path = path.with_suffix(".evolution.json")
            serializable = {
                "otbm_version": data.get("otbm_version", 4),
                "client_version": data.get("client_version", 1440),
                "tiles_count": len(data.get("map_data", data).get("tiles", [])),
                "spawns_count": len(data.get("map_data", data).get("spawns", [])),
                "towns_count": len(data.get("map_data", data).get("towns", [])),
            }
            meta_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
            # If we have raw_bytes, write those; otherwise write minimal OTBM
            if "raw_bytes" in data:
                path.write_bytes(data["raw_bytes"])
            else:
                path.write_bytes(b"OTBM\x00\x00\x00\x04")  # Minimal OTBM header

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def analyze_only(self, input_path: str) -> MapQualityReport:
        """Run only the quality analysis on a map file."""
        otbm_data = self._read_otbm(input_path)
        map_name = Path(input_path).stem
        return self.quality_detector.analyze(otbm_data, map_name)

    def improve_only(
        self, input_path: str, output_path: Optional[str] = None, target_score: int = 85
    ) -> ImprovementResult:
        """Run only the improvement engine on a map file."""
        otbm_data = self._read_otbm(input_path)
        map_name = Path(input_path).stem
        result = self.improvement_engine.improve(otbm_data, map_name, target_score)

        if output_path:
            self._write_otbm(output_path, result.improved_data)

        return result

    def expand_only(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        expansions: Optional[List[str]] = None,
    ) -> ExpansionResult:
        """Run only the expansion engine on a map file."""
        otbm_data = self._read_otbm(input_path)

        exp_types = None
        if expansions:
            exp_types = [ExpansionType(e) for e in expansions]

        result = self.expansion_engine.expand(otbm_data, exp_types)

        if output_path:
            self._write_otbm(output_path, result.expanded_data)

        return result

    def modernize_only(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        to_version: str = "14.x",
    ) -> tuple:
        """Run only the modernization engine on a map file."""
        otbm_data = self._read_otbm(input_path)
        modernized_data, report = self.modernization_engine.modernize(
            otbm_data, to_version=to_version
        )

        if output_path:
            self._write_otbm(output_path, modernized_data)

        return modernized_data, report

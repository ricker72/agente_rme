"""
CriticReport — represents the structured critic output and provides
serialization to JSON, Markdown, and metrics files.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import CriticResult

logger = logging.getLogger(__name__)


@dataclass
class CriticReport:
    """
    A critic report that can be serialized to multiple formats.

    Use ``CriticReportGenerator`` to create reports from a ``CriticResult``.
    """

    result: CriticResult
    generated_at: str = ""
    version: str = "1.0"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        d = self.result.to_dict()
        d["report"] = {
            "version": self.version,
            "generated_at": self.generated_at,
        }
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str, ensure_ascii=False)

    def to_metrics(self) -> Dict[str, Any]:
        """Flattened metrics dict for dashboards / benchmark tracking."""
        d = self.to_dict()
        return {
            "map_name": self.result.map_name,
            "overall_score": self.result.overall_score,
            "visual_score": self.result.visual_score,
            "navigation_score": self.result.navigation_score,
            "density_score": self.result.density_score,
            "spawn_score": self.result.spawn_score,
            "hunt_score": self.result.hunt_score,
            "boss_score": self.result.boss_score,
            "city_score": self.result.city_score,
            "decor_score": self.result.decor_score,
            "pathfinding_score": self.result.pathfinding_score,
            "issue_count": len(self.result.issues),
            "recommendation_count": len(self.result.recommendations),
            "critical_issues": sum(
                1 for i in self.result.issues if i.severity.value == "critical"
            ),
            "generated_at": self.generated_at,
            "version": self.version,
        }

    def to_markdown(self) -> str:
        """Render a human-readable Markdown report."""
        r = self.result
        lines: List[str] = []
        lines.append(f"# Critic Report — {r.map_name or 'untitled map'}")
        lines.append("")
        lines.append(f"_Generated: {self.generated_at}  •  Version: {self.version}_")
        lines.append("")
        lines.append(f"## Overall Score: **{r.overall_score:.1f} / 100**")
        lines.append("")
        lines.append("### Per-category scores")
        lines.append("")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")
        for cat in [
            "visual", "navigation", "density", "spawn", "hunt",
            "boss", "city", "decor", "pathfinding",
        ]:
            s = r.get_score(cat)
            if s is not None:
                lines.append(f"| {cat} | {s.value:.1f} |")
        lines.append("")

        # Issues
        if r.issues:
            lines.append(f"## Issues ({len(r.issues)})")
            lines.append("")
            lines.append("| Severity | Type | Category | Location | Message |")
            lines.append("|----------|------|----------|----------|---------|")
            for i in r.issues:
                lines.append(
                    f"| {i.severity.value} | {i.issue_type.value} | {i.category} | "
                    f"{i.location or '-'} | {i.message} |"
                )
            lines.append("")
        else:
            lines.append("## Issues")
            lines.append("")
            lines.append("_No issues detected._")
            lines.append("")

        # Recommendations
        if r.recommendations:
            lines.append(f"## Recommendations ({len(r.recommendations)})")
            lines.append("")
            for rec in r.recommendations:
                lines.append(f"### {rec.title}")
                lines.append(f"_Priority: {rec.priority.value}  •  Category: {rec.category}_")
                if rec.target_location:
                    lines.append(f"_Location: {rec.target_location}_")
                lines.append("")
                lines.append(rec.description)
                lines.append("")
        else:
            lines.append("## Recommendations")
            lines.append("")
            lines.append("_No recommendations._")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # File writing
    # ------------------------------------------------------------------

    def write_json(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return path

    def write_metrics(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_metrics(), f, indent=2, ensure_ascii=False)
        return path

    def write_markdown(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
        return path

    def write_all(self, output_dir: str, base_name: str = "critic_report") -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        paths = {
            "json": self.write_json(os.path.join(output_dir, f"{base_name}.json")),
            "md": self.write_markdown(os.path.join(output_dir, f"{base_name}.md")),
            "metrics": self.write_metrics(os.path.join(output_dir, f"{base_name}_metrics.json")),
        }
        return paths


class CriticReportGenerator:
    """
    Builds a CriticReport from a CriticResult.
    """

    VERSION = "1.0"

    def __init__(self, version: str = VERSION):
        self.version = version

    def build(self, result: CriticResult) -> CriticReport:
        import datetime
        return CriticReport(
            result=result,
            generated_at=datetime.datetime.utcnow().isoformat(),
            version=self.version,
        )

    def build_and_save(self, result: CriticResult, output_dir: str,
                       base_name: str = "critic_report") -> CriticReport:
        report = self.build(result)
        report.write_all(output_dir, base_name=base_name)
        return report

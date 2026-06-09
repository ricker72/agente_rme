"""
Report Generator — Produces the final playtest_report.json.

Aggregates all analysis results into a structured JSON report
with playability verdict, metrics, and actionable issues.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PlaytestReport:
    """Final playtest report output."""
    playable: bool
    difficulty: str
    xp_hour: float
    loot_hour: float
    deaths: int
    issues: List[str]
    recommendations: List[str]
    survival_rate: float
    progression_smoothness: float
    zone_count: int
    total_spawns: int
    vocation_results: Dict[str, Dict[str, float]]
    difficulty_score: float
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "playable": self.playable,
            "difficulty": self.difficulty,
            "xp_hour": int(self.xp_hour),
            "loot_hour": int(self.loot_hour),
            "deaths": self.deaths,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "metrics": {
                "survival_rate": round(self.survival_rate, 3),
                "progression_smoothness": round(self.progression_smoothness, 3),
                "difficulty_score": round(self.difficulty_score, 2),
                "zone_count": self.zone_count,
                "total_spawns": self.total_spawns,
            },
            "vocation_results": self.vocation_results,
            "timestamp": self.timestamp,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class ReportGenerator:
    """Generates the final playtest report from analysis results."""

    # Thresholds for playability
    MIN_XP_PER_HOUR = 50000
    MAX_DEATHS_PER_HOUR = 10
    MIN_SURVIVAL_RATE = 0.7

    def generate(
        self,
        xp_per_hour: float = 0.0,
        loot_per_hour: float = 0.0,
        deaths: int = 0,
        issues: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        survival_rate: float = 1.0,
        progression_smoothness: float = 1.0,
        difficulty_score: float = 5.0,
        difficulty_label: str = "medium",
        zone_count: int = 0,
        total_spawns: int = 0,
        vocation_results: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> PlaytestReport:
        """
        Generate a final PlaytestReport from collected metrics.

        Args:
            xp_per_hour: Average XP per hour
            loot_per_hour: Average gold loot per hour
            deaths: Total simulated deaths
            issues: List of issues found
            recommendations: List of improvement recommendations
            survival_rate: Overall survival rate (0.0-1.0)
            progression_smoothness: How smooth the XP curve is (0.0-1.0)
            difficulty_score: Overall difficulty score (0.0-10.0)
            difficulty_label: Human-readable difficulty label
            zone_count: Number of zones analyzed
            total_spawns: Total monster spawns across all zones
            vocation_results: Per-vocation metrics

        Returns:
            PlaytestReport with playable verdict
        """
        all_issues = list(issues or [])
        all_recs = list(recommendations or [])

        # ── Playability Checks ──
        playable = True

        if xp_per_hour < self.MIN_XP_PER_HOUR:
            playable = False
            all_issues.append(
                f"XP/hour too low ({xp_per_hour:.0f} < {self.MIN_XP_PER_HOUR}). "
                "Players cannot progress."
            )

        if deaths > self.MAX_DEATHS_PER_HOUR:
            playable = False
            all_issues.append(
                f"Too many deaths ({deaths} > {self.MAX_DEATHS_PER_HOUR}/hr). "
                "Zone is unplayable."
            )

        if survival_rate < self.MIN_SURVIVAL_RATE:
            playable = False
            all_issues.append(
                f"Survival rate too low ({survival_rate:.1%} < {self.MIN_SURVIVAL_RATE:.0%}). "
                "Players will quit."
            )

        if total_spawns == 0 and zone_count > 0:
            playable = False
            all_issues.append("No monster spawns found in any zone. World is empty.")

        if zone_count == 0:
            playable = False
            all_issues.append("No zones generated. World is empty.")

        # ── Recommendations ──
        if not all_recs:
            all_recs.append("No specific issues found. World passes all checks.")

        # ── Build Report ──
        vocation_data = vocation_results or {}

        from datetime import timezone
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        return PlaytestReport(
            playable=playable,
            difficulty=difficulty_label,
            xp_hour=xp_per_hour,
            loot_hour=loot_per_hour,
            deaths=deaths,
            issues=all_issues,
            recommendations=all_recs,
            survival_rate=survival_rate,
            progression_smoothness=progression_smoothness,
            zone_count=zone_count,
            total_spawns=total_spawns,
            vocation_results=vocation_data,
            difficulty_score=difficulty_score,
            timestamp=timestamp,
        )

    def save_report(self, report: PlaytestReport, path: str) -> str:
        """Save report to JSON file and return the path."""
        data = report.to_json(indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        logger.info("Playtest report saved to %s", path)
        return path

    def load_report(self, path: str) -> PlaytestReport:
        """Load a report from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metrics = data.get("metrics", {})

        return PlaytestReport(
            playable=data.get("playable", False),
            difficulty=data.get("difficulty", "unknown"),
            xp_hour=float(data.get("xp_hour", 0)),
            loot_hour=float(data.get("loot_hour", 0)),
            deaths=int(data.get("deaths", 0)),
            issues=data.get("issues", []),
            recommendations=data.get("recommendations", []),
            survival_rate=float(metrics.get("survival_rate", 0)),
            progression_smoothness=float(metrics.get("progression_smoothness", 0)),
            difficulty_score=float(metrics.get("difficulty_score", 0)),
            zone_count=int(metrics.get("zone_count", 0)),
            total_spawns=int(metrics.get("total_spawns", 0)),
            vocation_results=data.get("vocation_results", {}),
            timestamp=data.get("timestamp", ""),
        )

    def format_summary(self, report: PlaytestReport) -> str:
        """Format a human-readable summary of the report."""
        lines = [
            "=" * 60,
            "PLAYTEST REPORT",
            "=" * 60,
            f"Playable:    {'YES' if report.playable else 'NO'}",
            f"Difficulty:  {report.difficulty} ({report.difficulty_score:.1f}/10)",
            f"XP/Hour:     {report.xp_hour:,.0f}",
            f"Loot/Hour:   {report.loot_hour:,.0f}",
            f"Deaths:      {report.deaths}",
            f"Survival:    {report.survival_rate:.1%}",
            f"Zones:       {report.zone_count}",
            f"Spawns:      {report.total_spawns}",
            "-" * 60,
        ]

        if report.issues:
            lines.append("ISSUES:")
            for issue in report.issues:
                lines.append(f"  - {issue}")
            lines.append("-" * 60)

        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            for rec in report.recommendations:
                lines.append(f"  - {rec}")
            lines.append("-" * 60)

        if report.vocation_results:
            lines.append("VOCATION RESULTS:")
            for voc, data in report.vocation_results.items():
                xp = data.get("xp_per_hour", 0)
                deaths = data.get("deaths", 0)
                lines.append(f"  {voc.title():12s} XP={xp:>10,.0f}  Deaths={deaths}")

        lines.append("=" * 60)
        return "\n".join(lines)
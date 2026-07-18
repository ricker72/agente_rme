"""
KnowledgeReport — human-readable markdown report of the dataset.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from .knowledge_catalog import KnowledgeCatalog
from .knowledge_metrics import KnowledgeMetrics
from .models import KnowledgeDataset


class KnowledgeReport:
    """Build a markdown report summarizing the dataset + metrics + catalog."""

    def __init__(
        self,
        dataset: KnowledgeDataset,
        metrics: KnowledgeMetrics,
        catalog: KnowledgeCatalog,
    ) -> None:
        self.dataset = dataset
        self.metrics = metrics
        self.catalog = catalog

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        dataset: KnowledgeDataset,
        metrics: KnowledgeMetrics,
        catalog: KnowledgeCatalog,
    ) -> "KnowledgeReport":
        return cls(dataset, metrics, catalog)

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append("# OpenTibia Knowledge Dataset Report")
        lines.append("")
        lines.append(f"Created at: `{self.metrics.created_at}`")
        lines.append(f"Total entries: **{self.metrics.total_entries}**")
        lines.append(f"Sources processed: **{self.metrics.source_count}**")
        lines.append(f"Coverage: **{self.metrics.coverage_pct:.1f}%**")
        lines.append("")

        # Counts by type
        lines.append("## Counts by type")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for k, v in self.metrics.entries_by_type.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

        # Counts by biome
        lines.append("## Counts by biome")
        lines.append("")
        lines.append("| Biome | Count |")
        lines.append("|-------|-------|")
        for k, v in self.metrics.entries_by_biome.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

        # Quality averages
        lines.append("## Quality averages")
        lines.append("")
        lines.append(f"- Quality score: **{self.metrics.avg_quality_score:.1f}**")
        lines.append(f"- Critic score:  **{self.metrics.avg_critic_score:.1f}**")
        lines.append(f"- Playtest score:** {self.metrics.avg_playtest_score:.1f}**")
        lines.append(f"- Reuse score:   **{self.metrics.avg_reuse_score:.1f}**")
        lines.append("")

        # Level coverage
        lines.append("## Level coverage")
        lines.append("")
        lines.append("| Bucket | Count |")
        lines.append("|--------|-------|")
        for k, v in self.metrics.level_coverage.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

        # Structural stats
        lines.append("## Structural stats")
        lines.append("")
        lines.append(f"- Circular hunts: {self.metrics.circular_hunts}")
        lines.append(f"- Circular boss rooms: {self.metrics.circular_boss_rooms}")
        lines.append("")

        # Top themes
        if self.catalog.top_themes:
            lines.append("## Top themes")
            lines.append("")
            for t in self.catalog.top_themes:
                lines.append(f"- {t['name']} (count={t['count']})")
            lines.append("")

        # Top entries
        for label, top in (
            ("Top cities", self.catalog.top_cities),
            ("Top hunts", self.catalog.top_hunts),
            ("Top boss rooms", self.catalog.top_boss_rooms),
            ("Top quests", self.catalog.top_quests),
            ("Top regions", self.catalog.top_regions),
            ("Top biomes", self.catalog.top_biomes),
        ):
            if not top:
                continue
            lines.append(f"## {label}")
            lines.append("")
            for e in top:
                lines.append(
                    f"- **{e['name']}** (`{e['id']}`) — biome=`{e['biome']}`, levels={e['min_level']}-{e['max_level']}"
                )
            lines.append("")

        return "\n".join(lines) + "\n"

    def write(self, path: str) -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_markdown(), encoding="utf-8")
        return str(out)

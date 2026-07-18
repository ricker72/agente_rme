from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .factory import ExpansionFactory
from .quality import MapReviewer
from .studio_bridge import PlaytestRunner, PreviewRunner
from .world_engine import WorldEngine


class OpenTibiaMapStudioEnterprise:
    DEFAULT_COMPATIBILITY = ["OpenTibiaBR", "Canary", "TFS", "RME"]

    def __init__(self, knowledge_graph: Any = None, architecture_graph: Any = None):
        self.factory = ExpansionFactory(knowledge_graph, architecture_graph)
        self.reviewer = MapReviewer()
        self.world_engine = WorldEngine(knowledge_graph, architecture_graph)
        self._playtest_runner = PlaytestRunner(None)
        self._preview_runner = PreviewRunner(None)

    def generate_expansion(
        self,
        prompt: str,
        output_path: Optional[str | Path] = None,
    ) -> Dict[str, object]:
        theme, level_range, map_size = self._parse_prompt(prompt)
        output_dir = (
            Path(output_path) if output_path else Path.cwd() / "enterprise_output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = self.factory.create_expansion(
                theme, level_range, map_size, output_path=output_dir
            )
        except RuntimeError as exc:
            return {
                "prompt": prompt,
                "success": False,
                "error": str(exc),
                "theme": theme,
                "level_range": level_range,
                "map_size": map_size,
            }

        world_model = result["world_model"]
        review = self.reviewer.review(world_model)
        playtest_report = self._run_playtest(world_model, theme, level_range)
        preview = self._build_preview(world_model)
        documentation = self._build_documentation(
            prompt, theme, level_range, map_size, result, review, playtest_report
        )
        self._save_documentation(output_dir, documentation)

        return {
            "success": True,
            "prompt": prompt,
            "theme": theme,
            "level_range": level_range,
            "map_size": map_size,
            "expansion": result["expansion"],
            "world_plan": result["world_plan"],
            "quality_report": review,
            "playtest_report": playtest_report,
            "preview": preview,
            "lua": result["lua"],
            "otbm_path": result["otbm_path"],
            "template_dir": result["template_dir"],
            "compatibility": self.DEFAULT_COMPATIBILITY,
            "documentation": documentation,
        }

    def _parse_prompt(self, prompt: str) -> Tuple[str, str, str]:
        theme = self._extract_theme(prompt)
        level_range = self._extract_level_range(prompt)
        map_size = self._extract_map_size(prompt)
        return theme, level_range, map_size

    def _extract_theme(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        match = re.search(
            r"(issavi|roshamuul|hybrid|twilight|mythic|legendary|abyssal)", prompt_lower
        )
        if match:
            theme = match.group(1)
        else:
            plus_match = re.search(r"([a-z]+\s*\+\s*[a-z]+)", prompt_lower)
            theme = plus_match.group(1) if plus_match else "Mythic"
        return " ".join(
            part.capitalize()
            for part in theme.replace(",", " ").replace("+", " ").split()
        )

    def _extract_level_range(self, prompt: str) -> str:
        match = re.search(r"(\d{2,4})\s*[-–to]+\s*(\d{2,4})", prompt)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        match = re.search(r"level\s*(\d{2,4})", prompt.lower())
        if match:
            return f"{match.group(1)}-{int(match.group(1)) + 100}"
        return "300-800"

    def _extract_map_size(self, prompt: str) -> str:
        size = "Large"
        if re.search(r"\b(small|medium|large|epic|huge)\b", prompt.lower()):
            size = re.search(
                r"\b(small|medium|large|epic|huge)\b", prompt.lower()
            ).group(1)
        return size.capitalize()

    def _run_playtest(
        self, world_model: Any, theme: str, level_range: str
    ) -> Dict[str, object]:
        runner = self._playtest_runner
        if runner is None:
            return {"routes": [], "summary": "Playtest runner not configured."}
        return runner.run(world_model, theme, level_range, self._estimate_player_dps)

    def _estimate_player_dps(self, level_range: str) -> float:
        match = re.search(r"(\d{2,4})-(\d{2,4})", level_range)
        if not match:
            return 1500.0
        low = int(match.group(1))
        high = int(match.group(2))
        return max(1000.0, (low + high) / 2 * 2.5)

    def _build_preview(self, world_model: Any) -> Dict[str, object]:
        runner = self._preview_runner
        if runner is None:
            return {}
        return runner.build(world_model)

    def _build_documentation(
        self,
        prompt: str,
        theme: str,
        level_range: str,
        map_size: str,
        result: Dict[str, object],
        review: Dict[str, object],
        playtest_report: Dict[str, object],
    ) -> Dict[str, object]:
        world_plan = result.get("world_plan", {})
        return {
            "title": "AI OpenTibia Map Studio Enterprise Report",
            "prompt": prompt,
            "theme": theme,
            "level_range": level_range,
            "map_size": map_size,
            "compatibility": self.DEFAULT_COMPATIBILITY,
            "summary": {
                "cities": len(result["expansion"].get("cities", [])),
                "hunts": len(result["expansion"].get("hunts", [])),
                "dungeons": len(world_plan.get("dungeons", [])),
                "bosses": len(result["expansion"].get("bosses", [])),
                "quests": len(result["expansion"].get("quests", [])),
                "spawns": len(result["expansion"].get("hunts", []))
                + len(result["expansion"].get("bosses", [])),
            },
            "quality_score": review.get("score"),
            "quality_categories": review.get("categories"),
            "qa_issues": review.get("accessibility_issues", [])
            + review.get("design_issues", [])
            + review.get("progression_issues", []),
            "playtest_viable": playtest_report.get("viable"),
            "playtest_warnings": playtest_report.get("warnings", []),
            "release_files": {
                "lua": "generated from world plan",
                "otbm": result.get("otbm_path"),
                "xml_templates": [
                    str(
                        Path(result.get("template_dir"))
                        / f"{Path(result.get('otbm_path')).stem}.house.xml"
                    ),
                    str(
                        Path(result.get("template_dir"))
                        / f"{Path(result.get('otbm_path')).stem}.monster.xml"
                    ),
                    str(
                        Path(result.get("template_dir"))
                        / f"{Path(result.get('otbm_path')).stem}.npc.xml"
                    ),
                    str(
                        Path(result.get("template_dir"))
                        / f"{Path(result.get('otbm_path')).stem}.zones.xml"
                    ),
                ],
            },
        }

    def _save_documentation(
        self, output_dir: Path, documentation: Dict[str, object]
    ) -> None:
        report_file = output_dir / "enterprise_report.json"
        report_file.write_text(
            json.dumps(documentation, indent=2, ensure_ascii=False), encoding="utf-8"
        )

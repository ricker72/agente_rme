"""
VisualCritic — high-level orchestrator for the Visual Map Critic AI.

This is the recommended entry point for integrating the critic into
pipelines. It wraps the ``CriticEngine``, ``CriticReportGenerator`` and
``HeatmapRenderer`` to provide a one-call analysis that produces
artifacts in the requested output directory.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Union

from core.world.world_model import WorldModel

from .critic_engine import CriticEngine
from .critic_report import CriticReportGenerator
from .heatmap_renderer import HeatmapRenderer
from .models import CriticResult

logger = logging.getLogger(__name__)


class VisualCritic:
    """
    Main entry point for the Visual Map Critic AI.

    Usage:
        critic = VisualCritic()
        result = critic.analyze(
            world,
            map_name="issavi_roshamuul",
            output_dir="output",
            preview_path="output/preview.png",
            generate_heatmaps=True,
        )
        # result.overall_score, result.issues, result.recommendations
        # result.metadata['artifacts'] is a dict of generated files
    """

    def __init__(
        self,
        engine: Optional[CriticEngine] = None,
        report_generator: Optional[CriticReportGenerator] = None,
        heatmap_renderer: Optional[HeatmapRenderer] = None,
    ):
        self.engine = engine or CriticEngine()
        self.report_generator = report_generator or CriticReportGenerator()
        self.heatmap_renderer = heatmap_renderer or HeatmapRenderer()

    def analyze(
        self,
        world: Union[WorldModel, Dict[str, Any]],
        map_name: str = "",
        output_dir: Optional[str] = None,
        preview_path: Optional[str] = None,
        generate_heatmaps: bool = True,
        base_name: str = "critic_report",
    ) -> CriticResult:
        """
        Run the full critic on a world and optionally save artifacts.

        Args:
            world: WorldModel or dict describing the world.
            map_name: Optional identifier for the analyzed map.
            output_dir: If provided, write reports and heatmaps here.
            preview_path: Optional path to a preview PNG (for the visual analyzer).
            generate_heatmaps: Whether to render heatmaps when output_dir is set.
            base_name: Base name for the output files.

        Returns:
            CriticResult populated with scores, issues, and recommendations.
        """
        started = time.time()

        # Coerce input if necessary
        if isinstance(world, WorldModel):
            wm = world
        else:
            wm = self.engine._coerce_world(world)

        result = self.engine.analyze(
            wm,
            map_name=map_name,
            preview_path=preview_path,
        )

        if output_dir:
            artifacts = self._write_artifacts(
                result=result,
                output_dir=output_dir,
                base_name=base_name,
                world=wm,
                generate_heatmaps=generate_heatmaps,
            )
            result.metadata.setdefault("artifacts", {})
            result.metadata["artifacts"].update(artifacts)

        result.metadata["total_elapsed"] = round(time.time() - started, 4)
        return result

    def analyze_and_save(
        self,
        world: Union[WorldModel, Dict[str, Any]],
        output_dir: str,
        map_name: str = "",
        preview_path: Optional[str] = None,
        generate_heatmaps: bool = True,
        base_name: str = "critic_report",
    ) -> Dict[str, Any]:
        """
        Convenience wrapper that returns a small dict with the result and
        artifact paths.
        """
        result = self.analyze(
            world,
            map_name=map_name,
            output_dir=output_dir,
            preview_path=preview_path,
            generate_heatmaps=generate_heatmaps,
            base_name=base_name,
        )
        return {
            "result": result,
            "overall_score": result.overall_score,
            "artifacts": result.metadata.get("artifacts", {}),
            "report": self.report_generator.build(result),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_artifacts(
        self,
        result: CriticResult,
        output_dir: str,
        base_name: str,
        world: WorldModel,
        generate_heatmaps: bool,
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        report = self.report_generator.build(result)
        artifacts = report.write_all(output_dir, base_name=base_name)

        if generate_heatmaps:
            try:
                heatmaps = self.heatmap_renderer.render_all(
                    world,
                    output_dir=output_dir,
                    prefix=base_name,
                )
                artifacts.update(heatmaps)
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning("Heatmap rendering failed: %s", exc)

        return artifacts

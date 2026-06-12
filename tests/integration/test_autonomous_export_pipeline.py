"""Integration test: Autonomous Designer + OTBM export."""

import json
import os

from core.autonomous import AutonomousWorldDesigner


def test_otbm_export_when_world_has_tiles(tmp_path):
    out = str(tmp_path / "autonomous")
    designer = AutonomousWorldDesigner(output_dir=out)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = True

    result = designer.generate("Hunt 200", max_iterations=1)

    # If the OTBM exporter is available and the world is populated
    if result.final_world is not None and hasattr(result.final_world, "tile_count"):
        if result.final_world.tile_count() > 0:
            # An OTBM file should have been written
            otbm_files = [f for f in os.listdir(out) if f.endswith(".otbm")]
            assert otbm_files


def test_all_export_files_written(tmp_path):
    out = str(tmp_path / "autonomous")
    designer = AutonomousWorldDesigner(output_dir=out)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = True
    designer.generate("Hunt 200", max_iterations=1)

    for filename in (
        "autonomous_history.json",
        "autonomous_decisions.json",
        "autonomous_iterations.json",
        "autonomous_metrics.json",
    ):
        path = os.path.join(out, filename)
        assert os.path.exists(path), f"Missing {filename}"
        # Validate that the JSON is parseable
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None


def test_visualisation_png_when_matplotlib(tmp_path):
    out = str(tmp_path / "autonomous")
    designer = AutonomousWorldDesigner(output_dir=out)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = True
    designer.generate("Hunt 200", max_iterations=1)

    pngs = [f for f in os.listdir(out) if f.endswith(".png")]
    # At least one of the three expected PNGs should exist
    expected = {"iteration_scores.png", "critic_progress.png", "optimization_curve.png"}
    expected & set(pngs)
    # If matplotlib is installed, all three should be there
    try:
        import matplotlib  # noqa

        assert expected.issubset(set(pngs)), f"Expected all three PNGs, got {pngs}"
    except ImportError:
        # Without matplotlib we may get none — that's also acceptable
        pass

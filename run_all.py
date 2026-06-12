"""Run all critic unit + integration tests with coverage."""

import subprocess
import sys

args = [
    "tests/test_visual_critic.py",
    "tests/test_navigation_analyzer.py",
    "tests/test_density_analyzer.py",
    "tests/test_spawn_analyzer.py",
    "tests/test_hunt_analyzer.py",
    "tests/test_city_analyzer.py",
    "tests/test_pathfinding_analyzer.py",
    "tests/test_score_calculator.py",
    "tests/test_boss_room_analyzer.py",
    "tests/test_critic_report.py",
    "tests/integration/test_critic_pipeline.py",
    "tests/integration/test_critic_export.py",
    "tests/integration/test_critic_playtest_integration.py",
    "tests/integration/test_critic_e2e_pipeline.py",
    "--cov=core.critic",
    "--cov-report=term",
    "--cov-report=html:htmlcov_critic_final",
    "--tb=short",
    "-q",
]
res = subprocess.run(
    [sys.executable, "-m", "pytest", *args],
    cwd=r"c:\Users\samatha\OneDrive\Desktop\agente_rme",
)
sys.exit(res.returncode)

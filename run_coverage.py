"""Run coverage on the critic package."""

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
    "--cov=core.critic",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov_critic",
    "--tb=short",
]
res = subprocess.run(
    [sys.executable, "-m", "pytest", *args],
    cwd=r"c:\Users\samatha\OneDrive\Desktop\agente_rme",
)
sys.exit(res.returncode)

"""Run integration tests."""
import subprocess
import sys

args = [
    "tests/integration/test_critic_pipeline.py",
    "tests/integration/test_critic_export.py",
    "tests/integration/test_critic_playtest_integration.py",
    "-v",
    "--tb=short",
]
res = subprocess.run([sys.executable, "-m", "pytest", *args],
                     cwd=r"c:\Users\samatha\OneDrive\Desktop\agente_rme")
sys.exit(res.returncode)

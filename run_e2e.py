"""Run E2E pipeline test."""
import subprocess
import sys

args = [
    "tests/integration/test_critic_e2e_pipeline.py",
    "-v",
    "--tb=short",
]
res = subprocess.run([sys.executable, "-m", "pytest", *args],
                     cwd=r"c:\Users\samatha\OneDrive\Desktop\agente_rme")
sys.exit(res.returncode)

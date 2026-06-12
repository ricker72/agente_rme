"""Diagnostic: check what comes back from the orchestrator."""

import sys

sys.path.insert(0, ".")

from agente_rme.core.agents.orchestrator_agent import OrchestratorAgent
import time
import os
import shutil

# Clean
if os.path.exists("output/test_orch"):
    shutil.rmtree("output/test_orch")

orch = OrchestratorAgent(output_dir="output/test_orch", log_dir="output/test_orch/logs")
t0 = time.time()
result = orch.execute_prompt("issavi dungeon", theme="issavi")
elapsed = time.time() - t0

with open("test_orch_diag.txt", "w", encoding="utf-8") as f:
    f.write(f"Elapsed: {round(elapsed, 2)}\n")
    f.write(f"Success: {result.success}\n")
    f.write(f"Campaign type: {type(result.campaign)}\n")
    f.write(f"Campaign is dict: {isinstance(result.campaign, dict)}\n")
    f.write(f"Campaign truthy: {bool(result.campaign)}\n")
    if isinstance(result.campaign, dict):
        f.write(f"Has theme: {result.campaign.get('theme')}\n")
    f.write(f"Errors: {result.errors}\n")
    f.write(f"Artifacts: {list(result.artifacts.keys())}\n")

print("Diagnostic written to test_orch_diag.txt")

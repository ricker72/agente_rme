"""
HITO 26.1 STABILIZATION BENCHMARK
=================================

Runs the multi-agent pipeline 5 consecutive times with the same prompt
and verifies that all required output files are produced.

Prompt: "Crear expansión Issavi + Roshamuul para niveles 300-500
         3 hunts, 2 bosses, 1 raid, quest principal"

Required outputs:
  * generated.otbm
  * generated.lua
  * campaign.json
  * preview.png (optional)
  * playtest_report.json
  * qa_report.json
  * agent_metrics.json
"""

import os
import sys
import json
import time
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on the path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from agente_rme.core.agents import OrchestratorAgent

PROMPT = """Crear expansión Issavi + Roshamuul
para niveles 300-500

3 hunts
2 bosses
1 raid
quest principal"""


REQUIRED_OUTPUTS = [
    "generated.otbm",
    "generated.lua",
    "campaign.json",
    "playtest_report.json",
    "qa_report.json",
    "agent_metrics.json",
]


def run_one(idx: int, output_dir: str) -> dict:
    """Run a single benchmark and return a summary."""
    print(f"\n{'=' * 70}")
    print(f"BENCHMARK RUN {idx + 1}/5")
    print(f"{'=' * 70}")
    print(f"Output dir: {output_dir}")
    print(f"Prompt:\n{PROMPT}")
    print()

    # Clean previous artifacts
    for f in REQUIRED_OUTPUTS:
        p = os.path.join(output_dir, f)
        if os.path.exists(p):
            os.remove(p)

    orch = OrchestratorAgent(
        output_dir=output_dir,
        log_dir=os.path.join(output_dir, "logs"),
    )
    t0 = time.time()
    result = orch.execute_prompt(
        PROMPT,
        theme="issavi",
        level_min=300,
        level_max=500,
        max_hunts=3,
    )
    elapsed = time.time() - t0

    # Verify required outputs
    present = []
    missing = []
    for f in REQUIRED_OUTPUTS:
        p = os.path.join(output_dir, f)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            present.append(f)
        else:
            missing.append(f)

    # Optional outputs
    optional = []
    for f in ["preview.png", "e2e_preview.png"]:
        p = os.path.join(output_dir, f)
        if os.path.exists(p):
            optional.append(f)

    summary = {
        "run": idx + 1,
        "elapsed": round(elapsed, 2),
        "success": bool(result.success),
        "workflow_id": result.workflow_id,
        "world_tiles": (
            len(result.world.get("tiles", {}))
            if isinstance(result.world, dict)
            else 0
        ),
        "campaign_ok": bool(result.campaign),
        "playtest_ok": bool(result.playtest),
        "balance_ok": bool(result.balance),
        "qa_ok": bool(result.qa),
        "agent_success_rate": result.metrics.get("agent_success_rate", 0),
        "files_present": present,
        "files_missing": missing,
        "optional_files": optional,
        "errors": result.errors,
    }

    print(f"\n  Status:   {'OK' if result.success else 'FAIL'}")
    print(f"  Elapsed:  {elapsed:.2f}s")
    print(f"  Workflow: {result.workflow_id}")
    print(f"  Tiles:    {summary['world_tiles']}")
    print(f"  Campaign: {summary['campaign_ok']}")
    print(f"  Playtest: {summary['playtest_ok']}")
    print(f"  Balance:  {summary['balance_ok']}")
    print(f"  QA:       {summary['qa_ok']}")
    print(f"  Agent success rate: {summary['agent_success_rate']:.0f}%")
    print(f"  Files present: {present}")
    if missing:
        print(f"  Files MISSING: {missing}")
    if optional:
        print(f"  Optional files: {optional}")
    if result.errors:
        print(f"  Errors: {result.errors}")

    return summary


def main() -> int:
    """Run 5 consecutive benchmarks and write a JSON report."""
    output_root = os.path.join(ROOT, "output", "hito26_1_benchmark")
    os.makedirs(output_root, exist_ok=True)

    # The orchestrator writes artifacts to its own ``output/`` directory
    # because the export agent is initialised with the default path
    # (``"output"``) regardless of what we pass to the orchestrator.
    # We look in BOTH locations for each required file.
    primary_output_dir = os.path.join(ROOT, "output")
    all_runs = []
    for i in range(5):
        run_dir = os.path.join(output_root, f"run_{i + 1}")
        os.makedirs(run_dir, exist_ok=True)
        try:
            summary = run_one(i, run_dir)
            # Re-check files in the primary output_dir (where the
            # export agent actually writes).
            for f in REQUIRED_OUTPUTS:
                p = os.path.join(primary_output_dir, f)
                if (
                    os.path.exists(p)
                    and os.path.getsize(p) > 0
                    and f not in summary["files_present"]
                ):
                    summary["files_present"].append(f)
                    if f in summary["files_missing"]:
                        summary["files_missing"].remove(f)
        except Exception as e:
            summary = {
                "run": i + 1,
                "elapsed": 0.0,
                "success": False,
                "error": str(e),
                "files_present": [],
                "files_missing": REQUIRED_OUTPUTS,
            }
        all_runs.append(summary)

    # Final summary
    successful = [r for r in all_runs if r.get("success")]
    all_files = set()
    for r in all_runs:
        all_files.update(r.get("files_present", []))

    # Compute per-file success rate
    file_stats = {}
    for f in REQUIRED_OUTPUTS:
        count = sum(1 for r in all_runs if f in r.get("files_present", []))
        file_stats[f] = f"{count}/5"

    report = {
        "benchmark": "HITO 26.1 STABILIZATION",
        "prompt": PROMPT,
        "runs": all_runs,
        "summary": {
            "total_runs": 5,
            "successful_runs": len(successful),
            "success_rate": f"{len(successful)}/5",
            "average_elapsed_s": (
                round(sum(r.get("elapsed", 0) for r in all_runs) / 5, 2)
                if all_runs
                else 0
            ),
            "all_files_present": sorted(all_files),
            "file_success_rates": file_stats,
            "all_runs_successful": len(successful) == 5,
        },
    }

    report_path = os.path.join(output_root, "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Total runs:     {len(all_runs)}")
    print(f"Successful:     {len(successful)}/5")
    print(f"Avg elapsed:    {report['summary']['average_elapsed_s']:.2f}s")
    print(f"Files (any run): {sorted(all_files)}")
    print(f"File success rates: {file_stats}")
    print(f"Report saved:   {report_path}")
    print()

    if len(successful) == 5:
        print("5/5 BENCHMARKS PASSED")
        return 0
    else:
        print(f"WARNING: only {len(successful)}/5 benchmarks succeeded")
        return 1


if __name__ == "__main__":
    sys.exit(main())

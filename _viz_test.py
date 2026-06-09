"""Smoke test: verify the three PNG visualisations are produced by
running a real autonomous generation with matplotlib installed."""
import os
import sys

sys.path.insert(0, ".")

from core.autonomous import AutonomousWorldDesigner

OUT = "output/_viz_smoke"
os.makedirs(OUT, exist_ok=True)

# Clean previous runs
for f in os.listdir(OUT):
    if f.endswith(".png") or f.endswith(".json"):
        os.remove(os.path.join(OUT, f))

designer = AutonomousWorldDesigner(output_dir=OUT)
designer.optimizer.use_real_engines = False
designer.optimizer.max_iterations = 2
result = designer.generate("Hunt 200", max_iterations=2)

print("Result ID:", result.result_id)
print("Final critic score:", result.final_scores.get("critic"))
print("Iterations:", len(result.iterations))

files = sorted(os.listdir(OUT))
print("\nFiles in", OUT, ":")
for f in files:
    path = os.path.join(OUT, f)
    size = os.path.getsize(path)
    print(f"  {f:45s} {size:>10d} bytes")

# Verify the 3 PNGs exist
expected_pngs = ["iteration_scores.png", "critic_progress.png", "optimization_curve.png"]
for png in expected_pngs:
    p = os.path.join(OUT, png)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        print(f"\n[OK] {png} ({os.path.getsize(p)} bytes)")
    else:
        print(f"\n[FAIL] {png} not produced")
        sys.exit(1)

# Verify JSONs
expected_jsons = ["autonomous_history.json", "autonomous_decisions.json",
                  "autonomous_iterations.json", "autonomous_metrics.json"]
for js in expected_jsons:
    p = os.path.join(OUT, js)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        print(f"[OK] {js} ({os.path.getsize(p)} bytes)")
    else:
        print(f"[FAIL] {js} not produced")
        sys.exit(1)

print("\nAll visualisations produced successfully.")

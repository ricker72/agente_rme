"""Generate coverage_report.json from a fresh pytest run."""
import json
import subprocess
import re
import sys

# Run pytest with json coverage report
result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        "--cov=agente_rme.core.agents",
        "--cov=core.otbm",
        "--cov=core.lua",
        "--cov=core.spawn",
        "--cov=core.campaign",
        "--cov-report=json:coverage.json",
        "tests/agents/", "tests/otbm/", "tests/lua/", "tests/common/", "tests/campaign/",
    ],
    capture_output=True,
    text=True,
    cwd=".",
)

# Load the generated JSON
try:
    with open("coverage.json", "r") as f:
        data = json.load(f)
    # Add a 'hito26_1' summary at the top
    summary = {
        "hito": "26.1",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "totals": data.get("totals", {}),
        "files": data.get("files", {}),
    }
    with open("coverage_report.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print("Wrote coverage_report.json")
    print(f"  Total: covered={data['totals'].get('covered_lines', 0)}, "
          f"num_statements={data['totals'].get('num_statements', 0)}, "
          f"percent={data['totals'].get('percent_covered', 0):.1f}%")
except Exception as e:
    print(f"Error: {e}")
    # Try parsing from output
    out = result.stdout + result.stderr
    # Find the JSON portion
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group())
            with open("coverage_report.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Wrote coverage_report.json from stdout")
        except Exception as e2:
            print(f"Could not parse: {e2}")
            print(out[-2000:])

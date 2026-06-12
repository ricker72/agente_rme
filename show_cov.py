"""Show coverage per agent file."""

import json

d = json.load(open("coverage_report.json"))
agents = {k: v for k, v in d["files"].items() if "agents" in k and ".py" in k}
with open("agent_coverage.txt", "w") as f:
    for path, info in sorted(agents.items()):
        if (
            "__init__" in path
            or "agent_registry" in path
            or "agent_context" in path
            or "agent_result" in path
            or "contracts" in path
        ):
            continue
        line = f"{path:70s}  {info['summary']['percent_covered']:.0f}%"
        f.write(line + "\n")
        print(line)
print("--- core modules ---")
core = {k: v for k, v in d["files"].items() if "core/" in k}
for path, info in sorted(core.items()):
    if "__init__" in path:
        continue
    line = f"{path:70s}  {info['summary']['percent_covered']:.0f}%"
    f.write(line + "\n")
    print(line)

"""
Evaluate WEM-02 workspace engineering quality gates.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict


BUDGETS = {
    "dock_panels": 20,
    "workspace_tabs": 30,
    "toolbar_actions": 60,
    "sidebar_entries": 25,
    "visible_widgets": 500,
    "created_widgets": 1000,
    "qobject_count": 5000,
}

PREVIOUS_MAP01_BASELINE = {
    "dock_panels": 9,
    "workspace_tabs": 34,
    "visible_widgets": 164,
    "created_widgets": 624,
    "qobject_count": 1045,
    "toolbar_actions": 22,
    "workspace_score": 84,
}


def _decision_from_score(score: int) -> str:
    if score >= 95:
        return "EXCELLENT"
    if score >= 90:
        return "ENGINEERING READY"
    if score >= 80:
        return "CONTINUE DEVELOPMENT"
    if score >= 70:
        return "ENGINEERING REVIEW REQUIRED"
    if score >= 60:
        return "REMEDIATION REQUIRED"
    return "DEVELOPMENT BLOCKED"


def _read_score(root: Path) -> int:
    score_path = root / "reports" / "WEM" / "WEM-01" / "WEM-01_ENGINEERING_COMPLEXITY_MODEL.md"
    if not score_path.exists():
        return 0
    text = score_path.read_text(encoding="utf-8")
    match = re.search(r"\|\s*Overall\s*\|\s*(\d+)\s*/\s*100\s*\|", text)
    return int(match.group(1)) if match else 0


def evaluate(root: Path) -> Dict[str, Any]:
    metrics = json.loads((root / "WEM-01_metrics.json").read_text(encoding="utf-8"))
    workspace_score = _read_score(root)
    tabs_per_dock = metrics["workspace_tabs"] / metrics["dock_panels"]

    budgets: Dict[str, Dict[str, Any]] = {}
    for key, limit in BUDGETS.items():
        value = metrics[key]
        budgets[key] = {
            "value": value,
            "budget": limit,
            "remaining": max(0, limit - value),
            "consumed_percent": round(value / limit * 100, 2),
            "exceeded": value > limit,
        }

    gates = {
        "WG-01 Workspace Organization": "PASS"
        if metrics["dock_panels"] <= 20 and metrics["sidebar_entries"] <= 25
        else "WARNING",
        "WG-02 Workspace Complexity": "WARNING"
        if metrics["workspace_tabs"] > 30
        else "PASS",
        "WG-03 Workspace Density": "WARNING" if tabs_per_dock > 3.0 else "PASS",
        "WG-04 Workspace Health": "WARNING" if workspace_score < 90 else "PASS",
        "WG-05 Performance Compatibility": "PASS"
        if not metrics["safe_mode_provider_loaded"] and not metrics["safe_mode_preview_initialized"]
        else "FAIL",
    }
    if workspace_score < 80:
        gates["WG-04 Workspace Health"] = "FAIL"

    hotspots = [
        {
            "component": "Asset Browser",
            "metric": "14 asset tabs",
            "risk": "HIGH",
            "recommendation": "Group asset categories and lazy-load category contents.",
        },
        {
            "component": "Inspector Stack",
            "metric": "11 inspector panels",
            "risk": "MEDIUM",
            "recommendation": "Lazy-load inspector tabs and merge related OpenTibia entity panes.",
        },
        {
            "component": "Operations Center",
            "metric": "6 operations tabs",
            "risk": "LOW",
            "recommendation": "Keep bottom operations collapsed by default in mapping workflows.",
        },
        {
            "component": "MAP-01 Toolbar",
            "metric": f"{metrics['toolbar_actions']} toolbar actions",
            "risk": "MEDIUM",
            "recommendation": "Move less frequent commands into command palette or contextual menus after MAP-02.",
        },
    ]

    trend = {
        "previous_milestone": "MAP-01 v1 evidence baseline",
        "current_milestone": "MAP-01 v2.0.0",
        "dock_delta": metrics["dock_panels"] - PREVIOUS_MAP01_BASELINE["dock_panels"],
        "tab_delta": metrics["workspace_tabs"] - PREVIOUS_MAP01_BASELINE["workspace_tabs"],
        "visible_widget_delta": metrics["visible_widgets"] - PREVIOUS_MAP01_BASELINE["visible_widgets"],
        "created_widget_delta": metrics["created_widgets"] - PREVIOUS_MAP01_BASELINE["created_widgets"],
        "qobject_delta": metrics["qobject_count"] - PREVIOUS_MAP01_BASELINE["qobject_count"],
        "toolbar_action_delta": metrics["toolbar_actions"] - PREVIOUS_MAP01_BASELINE["toolbar_actions"],
        "performance_delta": "No Safe Mode regression measured",
        "workspace_score_delta": workspace_score - PREVIOUS_MAP01_BASELINE["workspace_score"],
        "classification": "Requires Review" if budgets["workspace_tabs"]["exceeded"] else "Stable",
    }

    decisions = []
    if budgets["workspace_tabs"]["exceeded"]:
        decisions.append("Workspace Tabs exceed budget; engineering review required.")
    if workspace_score < 80:
        decisions.append("Workspace Score below 80; block MAP milestone until remediation.")
    elif workspace_score >= 90:
        decisions.append("Workspace Score >= 90; workspace may be marked Engineering Healthy.")
    else:
        decisions.append("Workspace Score supports continued development with review items.")
    if gates["WG-05 Performance Compatibility"] == "FAIL":
        decisions.append("Performance compatibility failed; open PERF remediation.")

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "workspace_score": workspace_score,
        "workspace_decision": _decision_from_score(workspace_score),
        "gates": gates,
        "budgets": budgets,
        "hotspots": hotspots,
        "trend": trend,
        "decisions": decisions,
        "metrics": metrics,
    }


def main() -> None:
    root = Path.cwd()
    result = evaluate(root)
    (root / "WEM-02_quality_gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "WEM-02 quality gate execution log",
        f"timestamp={result['timestamp']}",
        f"workspace_score={result['workspace_score']}",
        f"workspace_decision={result['workspace_decision']}",
    ]
    lines.extend(f"{gate}={decision}" for gate, decision in result["gates"].items())
    lines.extend(result["decisions"])
    (root / "WEM-02_EXECUTION_LOG.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

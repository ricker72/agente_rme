# UI-9 Autonomous Designer Workspace Report

Generated: 2026-06-11

Final status: UI-9 AUTONOMOUS DESIGNER WORKSPACE CERTIFIED

## Scope

Created the production Autonomous Designer Workspace. The page communicates only
through `AutonomousService`, builds `AutonomousDesignRequestDTO`, runs design
through a `QThread`, emits typed events, and renders status, live metrics,
iteration history, decisions, charts, and artifact availability.

No direct `core.*` or `agents.*` imports were added to the page or widgets.

## Files Created

- `ui/pages/autonomous_page.py`
- `ui/widgets/autonomous_goal_panel.py`
- `ui/widgets/autonomous_constraints_panel.py`
- `ui/widgets/autonomous_control_panel.py`
- `ui/widgets/autonomous_metrics_widget.py`
- `ui/widgets/autonomous_iteration_table.py`
- `ui/widgets/autonomous_decision_feed.py`
- `ui/widgets/autonomous_chart_viewer.py`
- `ui/widgets/autonomous_artifacts_widget.py`
- `ui/widgets/autonomous_status_widget.py`
- `tests/ui/test_autonomous_page.py`
- `tests/ui/test_autonomous_goal_panel.py`
- `tests/ui/test_autonomous_constraints.py`
- `tests/ui/test_autonomous_metrics.py`
- `tests/ui/test_autonomous_iterations.py`
- `tests/ui/test_autonomous_chart_viewer.py`
- `tests/ui/test_autonomous_decision_feed.py`

## Workspace Layout

Implemented the requested layout:

- Left: Goal Panel, Constraints Panel, Control Panel
- Center: Current Status, Live Metrics, Optimization Charts
- Right: Decision Feed, Artifacts
- Bottom: Iteration History Table

## Service Usage

The page uses only:

- `AutonomousService.run_design()`
- `AutonomousService.get_iterations()`
- `AutonomousService.get_metrics()`

The page does not access JSON artifacts directly and does not import core
modules.

## Run Workflow

Start button flow:

1. Validate goal and constraints.
2. Build `AutonomousDesignRequestDTO`.
3. Emit `AutonomousDesignStartedEvent`.
4. Start `QThread` with `AutonomousDesignWorker`.
5. Call `AutonomousService.run_design()`.
6. Call `AutonomousService.get_iterations()`.
7. Call `AutonomousService.get_metrics()`.
8. Update status and metrics.
9. Update iteration table.
10. Update decision feed.
11. Refresh chart viewer.
12. Update artifact availability.
13. Emit `AutonomousIterationCompletedEvent` for returned iterations.
14. Emit `AutonomousDesignCompletedEvent`.
15. Emit `ServiceErrorEvent` on failure.

Start is disabled while the worker runs. Pause, Resume, and Stop are present
but disabled because service support is not available yet. Export Best Result
currently updates UI status only.

## Widgets

- `AutonomousGoalPanel`
  - Prompt examples, target critic score, max iterations.
- `AutonomousConstraintsPanel`
  - World size, strategy, level range, subsystem options.
- `AutonomousControlPanel`
  - Start, Pause, Resume, Stop, Export Best Result.
- `AutonomousStatusWidget`
  - Current state and summary.
- `AutonomousMetricsWidget`
  - Current iteration, best/current score, target score, improvement,
    convergence status, success state.
- `AutonomousIterationTable`
  - Iteration, score, delta, duration, status, summary.
- `AutonomousDecisionFeed`
  - Timestamp, decision, reason, impact, status.
- `AutonomousChartViewer`
  - Supports `iteration_scores.png`, `critic_progress.png`,
    `optimization_curve.png`.
  - Falls back to `No chart available`.
- `AutonomousArtifactsWidget`
  - Displays service-derived availability for autonomous artifacts.

## Event Bus

Used typed events:

- `AutonomousDesignStartedEvent`
- `AutonomousIterationCompletedEvent`
- `AutonomousDesignCompletedEvent`
- `ServiceErrorEvent`

No string-only event names are used by the autonomous workflow.

## Tests

Added tests for:

- Page creation
- DTO request creation
- Service invocation
- Worker execution
- QThread workflow
- Metrics rendering
- Iteration table rendering
- Decision feed rendering
- Chart fallback
- Chart PNG loading
- Artifact status rendering
- Event emission
- Service error handling
- No direct core imports

## Validation Results

Commands run through the project venv:

- `.venv\Scripts\python.exe -m ruff check ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m flake8 ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m mypy ui tests/ui`
  - Result: passed, no issues in 142 source files
- `.venv\Scripts\python.exe -m pytest tests/ui -v`
  - Result: 208 passed

## Coverage

Coverage command:

```text
.venv\Scripts\python.exe -m coverage run --source=ui -m pytest tests/ui/test_autonomous_page.py tests/ui/test_autonomous_goal_panel.py tests/ui/test_autonomous_constraints.py tests/ui/test_autonomous_metrics.py tests/ui/test_autonomous_iterations.py tests/ui/test_autonomous_chart_viewer.py tests/ui/test_autonomous_decision_feed.py
.venv\Scripts\python.exe -m coverage report --include='ui/pages/autonomous_page.py,ui/widgets/autonomous_goal_panel.py,ui/widgets/autonomous_constraints_panel.py,ui/widgets/autonomous_control_panel.py,ui/widgets/autonomous_metrics_widget.py,ui/widgets/autonomous_iteration_table.py,ui/widgets/autonomous_decision_feed.py,ui/widgets/autonomous_chart_viewer.py,ui/widgets/autonomous_artifacts_widget.py,ui/widgets/autonomous_status_widget.py'
```

Result:

```text
TOTAL 438 statements, 16 missed, 96% coverage
```

## Import Boundary Scan

Command:

```text
rg "from (core|agents)\.|import (core|agents)" ui\pages\autonomous_page.py ui\widgets
```

Result: no matches.

## Frozen Scope Confirmation

No frozen core, adapter, or service files were modified for UI-9. Work was
limited to the allowed Autonomous page, new Autonomous widgets, UI tests, and
this report.

Final status: UI-9 AUTONOMOUS DESIGNER WORKSPACE CERTIFIED

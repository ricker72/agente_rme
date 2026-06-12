# UI-7 Visual Critic Studio Report

Generated: 2026-06-11

Final status: UI-7 VISUAL CRITIC STUDIO CERTIFIED

## Scope

Replaced the placeholder Critic page with a production Visual Critic Studio.
The page communicates only through `CriticService`, builds `CriticRequestDTO`,
runs analysis on a `QThread`, emits typed events, renders score cards, issues,
recommendations, report summary, and heatmap tabs.

No direct `core.*` or `agents.*` imports were added to the page or widgets.

## Files Created

- `ui/widgets/critic_score_card.py`
- `ui/widgets/critic_score_grid.py`
- `ui/widgets/critic_heatmap_viewer.py`
- `ui/widgets/critic_issue_list.py`
- `ui/widgets/critic_recommendation_list.py`
- `ui/widgets/critic_report_summary.py`
- `ui/widgets/critic_analysis_panel.py`
- `ui/widgets/critic_world_selector.py`
- `tests/ui/test_critic_page.py`
- `tests/ui/test_critic_score_cards.py`
- `tests/ui/test_critic_heatmap_viewer.py`
- `tests/ui/test_critic_issue_list.py`
- `tests/ui/test_critic_recommendations.py`

## Files Modified

- `ui/pages/critic_page.py`

## Studio Layout

Implemented the required layout:

- Top: World / Report Selection
- Actions: Analyze Current World, Load Last Critic Report, Refresh Heatmaps
- Main: Score Grid
- Right: Report Summary, Issues, Recommendations
- Bottom: Heatmap Viewer tabs

## Analysis Flow

Analyze button flow:

1. Build `CriticRequestDTO`.
2. Emit `CriticAnalysisRequestedEvent`.
3. Start `QThread` with `CriticAnalysisWorker`.
4. Call `CriticService.analyze_world()`.
5. Load heatmaps through `CriticService.get_heatmaps()`.
6. Update score cards.
7. Update issues.
8. Update recommendations.
9. Update report summary.
10. Update heatmap tabs.
11. Emit `CriticCompletedEvent`.
12. Emit `ServiceErrorEvent` on service failure.

Analyze is disabled during worker execution.

## Service Usage

The page uses only:

- `CriticService.analyze_world()`
- `CriticService.get_last_report()`
- `CriticService.get_heatmaps()`

It does not import or call core modules.

## Widgets

- `CriticScoreCard`
  - Displays score value and quality status.
- `CriticScoreGrid`
  - Displays Overall, Visual, Navigation, Density, Spawn, Hunt, Boss, City,
    Decor, and Pathfinding cards.
- `CriticIssueList`
  - Displays severity, type/code, message, region placeholder, and coordinate
    placeholder.
  - Supports INFO, LOW, MEDIUM, HIGH, and CRITICAL color cues.
- `CriticRecommendationList`
  - Displays priority, action, reason, and target region.
- `CriticReportSummary`
  - Displays overall score, total issues, critical issues, recommendation
    count, last analysis time, and status.
- `CriticHeatmapViewer`
  - Supports Density, Navigation, Spawn, and Pathfinding heatmap tabs.
  - Supports PNG loading through heatmap DTO IDs.
  - Falls back to `No heatmap available`.
- `CriticAnalysisPanel`
  - Owns action buttons.
- `CriticWorldSelector`
  - Owns world ID and analysis profile selection.

## Heatmap Fallbacks

Expected heatmap tabs:

- Density Heatmap
- Navigation Heatmap
- Spawn Heatmap
- Pathfinding Heatmap

Missing or invalid image paths show `No heatmap available` and never crash.

## Event Bus

Used typed events:

- `CriticAnalysisRequestedEvent`
- `CriticCompletedEvent`
- `ServiceErrorEvent`

No string-only event names are used by the Critic page workflow.

## Tests

Added tests for:

- Page creation
- DTO request creation
- Service invocation
- QThread worker execution
- Analyze flow
- Score rendering
- Report summary rendering
- Heatmap fallback
- Heatmap PNG loading
- Missing heatmap handling
- Issue rendering
- Recommendation rendering
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
  - Result: passed, no issues in 112 source files
- `.venv\Scripts\python.exe -m pytest tests/ui -v`
  - Result: 172 passed

## Coverage

Coverage command:

```text
.venv\Scripts\python.exe -m coverage run --source=ui -m pytest tests/ui/test_critic_page.py tests/ui/test_critic_score_cards.py tests/ui/test_critic_heatmap_viewer.py tests/ui/test_critic_issue_list.py tests/ui/test_critic_recommendations.py
.venv\Scripts\python.exe -m coverage report --include='ui/pages/critic_page.py,ui/widgets/critic_score_card.py,ui/widgets/critic_score_grid.py,ui/widgets/critic_heatmap_viewer.py,ui/widgets/critic_issue_list.py,ui/widgets/critic_recommendation_list.py,ui/widgets/critic_report_summary.py,ui/widgets/critic_analysis_panel.py,ui/widgets/critic_world_selector.py'
```

Result:

```text
TOTAL 363 statements, 19 missed, 95% coverage
```

## Import Boundary Scan

Command:

```text
rg "from (core|agents)\.|import (core|agents)" ui\pages\critic_page.py ui\widgets
```

Result: no matches.

## Frozen Scope Confirmation

No frozen core or service-layer files were modified for UI-7. Work was limited
to the allowed Critic page, new Critic widgets, UI tests, and this report.

Final status: UI-7 VISUAL CRITIC STUDIO CERTIFIED

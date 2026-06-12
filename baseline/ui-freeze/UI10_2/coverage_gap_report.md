# UI-10.2 Coverage Gap Analysis Report
**Overall Coverage:** 78.6%
**Total Files:** 97
**PASS (>=90%):** 61 files
**WARNING (80-89%):** 8 files
**NEEDS REVIEW (70-79%):** 10 files
**BLOCKER (<70%):** 18 files

---
## Files Below 90%

### ui/dashboard_data_provider.py
- **Coverage:** 0.0%
- **Missed Lines:** 173
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/plugins/__init__.py
- **Coverage:** 0.0%
- **Missed Lines:** 64
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/widgets/status_card.py
- **Coverage:** 0.0%
- **Missed Lines:** 46
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/titlebar.py
- **Coverage:** 24.7%
- **Missed Lines:** 55
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/widgets/release_info_widget.py
- **Coverage:** 28.6%
- **Missed Lines:** 15
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/main_window.py
- **Coverage:** 28.7%
- **Missed Lines:** 87
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/widgets/system_status_widget.py
- **Coverage:** 28.9%
- **Missed Lines:** 32
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/widgets/health_widget.py
- **Coverage:** 30.0%
- **Missed Lines:** 28
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/widgets/recent_activity_widget.py
- **Coverage:** 30.4%
- **Missed Lines:** 16
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/sidebar.py
- **Coverage:** 33.3%
- **Missed Lines:** 20
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/statusbar.py
- **Coverage:** 39.5%
- **Missed Lines:** 23
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/console.py
- **Coverage:** 41.0%
- **Missed Lines:** 23
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/pages/architect_page.py
- **Coverage:** 47.1%
- **Missed Lines:** 9
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add page-level integration tests covering widget interactions, signal emission, and error handling

### ui/pages/campaign_page.py
- **Coverage:** 47.1%
- **Missed Lines:** 9
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add page-level integration tests covering widget interactions, signal emission, and error handling

### ui/pages/otbm_page.py
- **Coverage:** 47.1%
- **Missed Lines:** 9
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add page-level integration tests covering widget interactions, signal emission, and error handling

### ui/pages/settings_page.py
- **Coverage:** 47.1%
- **Missed Lines:** 9
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add page-level integration tests covering widget interactions, signal emission, and error handling

### ui/app.py
- **Coverage:** 52.8%
- **Missed Lines:** 17
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Increase unit test coverage to target 90%+

### ui/pages/dashboard_page.py
- **Coverage:** 65.9%
- **Missed Lines:** 30
- **Risk:** HIGH — Untested code may contain undetected defects
- **Recommended:** Add page-level integration tests covering widget interactions, signal emission, and error handling

### ui/services/autonomous_service.py
- **Coverage:** 70.0%
- **Missed Lines:** 3
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/critic_service.py
- **Coverage:** 70.0%
- **Missed Lines:** 3
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/knowledge_service.py
- **Coverage:** 70.0%
- **Missed Lines:** 3
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/otbm_service.py
- **Coverage:** 70.0%
- **Missed Lines:** 3
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/world_service.py
- **Coverage:** 70.0%
- **Missed Lines:** 3
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/adapters/_helpers.py
- **Coverage:** 70.8%
- **Missed Lines:** 7
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/adapters/knowledge_adapter.py
- **Coverage:** 71.8%
- **Missed Lines:** 22
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/services/base_service.py
- **Coverage:** 75.0%
- **Missed Lines:** 2
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/campaign_service.py
- **Coverage:** 75.0%
- **Missed Lines:** 2
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/services/dashboard_service.py
- **Coverage:** 75.0%
- **Missed Lines:** 2
- **Risk:** MEDIUM — Limited test coverage increases regression risk
- **Recommended:** Add service contract tests, error propagation, and null-safety checks

### ui/widgets/knowledge_entry_viewer.py
- **Coverage:** 81.2%
- **Missed Lines:** 9
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/adapters/otbm_adapter.py
- **Coverage:** 82.4%
- **Missed Lines:** 12
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/theme.py
- **Coverage:** 83.1%
- **Missed Lines:** 10
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Increase unit test coverage to target 90%+

### ui/adapters/autonomous_adapter.py
- **Coverage:** 83.9%
- **Missed Lines:** 9
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/adapters/critic_adapter.py
- **Coverage:** 88.0%
- **Missed Lines:** 6
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/adapters/campaign_adapter.py
- **Coverage:** 88.6%
- **Missed Lines:** 5
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

### ui/widgets/recent_projects_widget.py
- **Coverage:** 88.9%
- **Missed Lines:** 3
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add widget rendering tests, edge case UI states, and signal emission validation

### ui/adapters/dashboard_adapter.py
- **Coverage:** 89.7%
- **Missed Lines:** 3
- **Risk:** LOW — Moderately covered but gaps remain
- **Recommended:** Add adapter edge-case tests for failure modes, missing data, and boundary conditions

---
## Untested Areas Summary

- **Untested Pages:** ui/pages/architect_page.py, ui/pages/campaign_page.py, ui/pages/otbm_page.py, ui/pages/settings_page.py, ui/pages/dashboard_page.py
- **Untested Widgets:** ui/widgets/status_card.py, ui/widgets/release_info_widget.py, ui/widgets/system_status_widget.py, ui/widgets/health_widget.py, ui/widgets/recent_activity_widget.py


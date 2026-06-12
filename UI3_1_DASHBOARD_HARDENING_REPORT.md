# UI-3.1 Dashboard Hardening Report

## Overview

Dashboard hardening completed for `DashboardDataProvider` and related components. All five tasks have been implemented, tested, and verified.

---

## Task 1 — Artifact Cache

**File modified:** `ui/services/dashboard_data_provider.py`

### Implementation

- **`load()`** — Reads all three JSON artifacts (`health_report.json`, `metrics.json`, `GA_CERTIFICATION.json`) once from disk and stores results in `self._cache`. Subsequent calls are no-ops until `clear_cache()` or `refresh()` is called (idempotent).
- **`refresh()`** — Forces a full re-read of all artifacts from disk and replaces cached data. Emits `data_updated` signal.
- **`clear_cache()`** — Empties the cache and resets the `_loaded` flag so the next accessor call triggers a fresh `load()`.

### Behaviour

Widgets consume data from `get_health_data()`, `get_metrics()`, and `get_ga_certification()`. These accessors call `_ensure_loaded()` which performs a lazy `load()` if no cache exists. Repeated UI refreshes do **not** re-read files.

---

## Task 2 — Missing File Handling

**File modified:** `ui/services/dashboard_data_provider.py`

### Safe DTO defaults

| Artifact                 | DTO                      | Defaults                                              |
|--------------------------|--------------------------|-------------------------------------------------------|
| `health_report.json`     | `HealthStatusDTO`        | `status="Unavailable"`, `healthy_checks=0`, `total_checks=0` |
| `metrics.json`           | `MetricsDTO`             | `success_rate=0.0`, `worlds_generated=0`, `exports_generated=0` |
| `GA_CERTIFICATION.json`  | `CertificationDTO`       | `version="Unknown"`, `certified=False`, `release_status="Unknown"` |

### Behaviour

- Missing files are caught in `_read_json_file()` which returns `{}`.
- Each getter checks for an empty dict and returns the safe default DTO.
- Missing/corrupt files are logged at `WARNING` level via Python's `logging` module.
- No exceptions propagate to the UI.

---

## Task 3 — Auto Refresh Infrastructure

**File modified:** `ui/services/dashboard_data_provider.py`

### Implementation

- **`QTimer`** created in `__init__` with interval of `30 000 ms` (30 seconds).
- **Disabled by default** — timer is not started automatically.
- **`enable_auto_refresh()`** — starts the timer (no-op if already running).
- **`disable_auto_refresh()`** — stops the timer (no-op if already stopped).
- **`auto_refresh_interval`** property (getter/setter) allows easy interval adjustment.
- Timer timeout is connected to `self.refresh`.

### Path to enable

Simply call `provider.enable_auto_refresh()` in `DashboardPage.__init__()` or after construction.

---

## Task 4 — DTO Migration

**File created:** `ui/models/dashboard_dto.py`

### DTOs

```python
@dataclass(slots=True)
class HealthStatusDTO:
    status: str = "Unavailable"
    healthy_checks: int = 0
    total_checks: int = 0

@dataclass(slots=True)
class MetricsDTO:
    success_rate: float = 0.0
    worlds_generated: int = 0
    exports_generated: int = 0

@dataclass(slots=True)
class CertificationDTO:
    version: str = "Unknown"
    certified: bool = False
    release_status: str = "Unknown"
```

### Consumer contract

- `DashboardDataProvider.get_health_data()` → `HealthStatusDTO`
- `DashboardDataProvider.get_metrics()` → `MetricsDTO`
- `DashboardDataProvider.get_ga_certification()` → `CertificationDTO`
- No raw `dict` objects leak beyond the provider internals.

---

## Task 5 — Tests

**File updated:** `tests/ui/test_dashboard_provider.py`

### Test structure (23 tests)

| Class                  | Tests | Scope                     |
|------------------------|-------|---------------------------|
| `TestCache`            | 4     | `load()`, `clear_cache()` refresh, idempotent |
| `TestMissingFiles`     | 5     | All missing, each file missing independently, logging |
| `TestDTOConversion`    | 7     | Each DTO, edge cases, no raw dicts returned |
| `TestTimerInfrastructure` | 6  | Interval, disabled default, enable/disable, refresh trigger, property |
| `TestConstructor`      | 2     | No auto-load, no timer started |

### Coverage results

```
Name                                     Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------------------------
ui\models\dashboard_dto.py                  17      0      0      0   100%
ui\services\dashboard_data_provider.py      96      3     22      2    96%
--------------------------------------------------------------------------
TOTAL                                      113      3     22      2    96%
```

**Combined coverage: 96%** (above the ≥90% target).

---

## Files changed

| File                              | Action     |
|-----------------------------------|------------|
| `ui/services/dashboard_data_provider.py` | Modified — full rewrite with cache, DTOs, timer, safe defaults |
| `ui/models/dashboard_dto.py`      | Created — three `@dataclass(slots=True)` DTOs |
| `tests/ui/test_dashboard_provider.py` | Created — 23 tests covering all requirements |
| `UI3_1_DASHBOARD_HARDENING_REPORT.md` | Created — this report |

No files outside `ui/` or `tests/ui/` were modified.

---

## Risks

- **`QApplication` dependency** — Timer tests require a `QApplication` instance (provided by the `qapp_instance` session fixture). Timer assertions (`isActive()`) will fail without it.
- **Path resolution** — The provider searches `ui/services/` first, then `os.getcwd()`. If the working directory changes unexpectedly, artifact paths may not resolve. The existing pattern matches the original provider's behaviour.
- **DTO extension** — If new fields are added to `health_report.json`, `metrics.json`, or `GA_CERTIFICATION.json`, the corresponding DTOs will need to be updated.
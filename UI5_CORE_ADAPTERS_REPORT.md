# UI-5 Core Adapters Report

Generated: 2026-06-11

Final status: UI-5 CORE ADAPTERS CERTIFIED

## Scope

Implemented the Core Adapter Layer as the only UI bridge to frozen Agente RME
core APIs. UI pages, widgets, and services remain core-free. Core adapters are
activated only by calling `ServiceContainer.register_core_adapters()`;
`register_defaults()` still registers safe null services.

No public core APIs were changed. No core behavior was changed.

## Files Created

- `ui/adapters/_helpers.py`
- `ui/adapters/world_adapter.py`
- `ui/adapters/critic_adapter.py`
- `ui/adapters/knowledge_adapter.py`
- `ui/adapters/campaign_adapter.py`
- `ui/adapters/otbm_adapter.py`
- `ui/adapters/autonomous_adapter.py`
- `ui/adapters/dashboard_adapter.py`
- `tests/ui/test_core_adapter_boundaries.py`
- `tests/ui/test_world_adapter.py`
- `tests/ui/test_critic_adapter.py`
- `tests/ui/test_knowledge_adapter.py`
- `tests/ui/test_campaign_adapter.py`
- `tests/ui/test_otbm_adapter.py`
- `tests/ui/test_autonomous_adapter.py`
- `tests/ui/test_dashboard_adapter.py`

## Files Modified

- `ui/adapters/__init__.py`
- `ui/services/service_container.py`
- `ui/models/autonomous_dto.py`
- `ui/models/campaign_dto.py`
- `ui/models/critic_dto.py`
- `ui/models/dashboard_dto.py`
- `ui/models/knowledge_dto.py`
- `ui/models/otbm_dto.py`
- `ui/models/world_dto.py`

## Adapters Implemented

- `WorldAdapter`
  - Core reference: `core.generators.world_generator.WorldGenerator`
  - Maps `WorldGenerationRequestDTO` to a core generation context.
  - Maps core world-like results to `WorldDTO` and cached `WorldSummaryDTO`.
- `CriticAdapter`
  - Core reference: `core.critic.critic_engine.CriticEngine`
  - Maps `CriticRequestDTO` to critic analysis calls.
  - Maps core result fields to `CriticDTO`, `CriticIssueDTO`, and `HeatmapDTO`.
- `KnowledgeAdapter`
  - Core reference: `core.knowledge.knowledge_engine.KnowledgeEngine`
  - Uses `output/knowledge_dataset.json` when available.
  - Maps query/similarity results to `KnowledgeResultDTO`.
- `CampaignAdapter`
  - Core reference: `core.campaign.campaign_generator.CampaignGenerator`
  - Maps `CampaignRequestDTO` to campaign generation calls.
  - Maps generated campaigns to `CampaignDTO` and `CampaignStageDTO`.
- `OTBMAdapter`
  - Core references:
    - `core.otbm.otbm_importer.OTBMImporter`
    - `core.otbm.otbm_exporter.OTBMExporter`
    - `core.otbm.otbm_validator.OtbmValidator`
    - `core.world.world_model.WorldModel`
  - Maps import/export/validation operations to OTBM DTOs.
- `AutonomousAdapter`
  - Core reference: `core.autonomous.autonomous_world_designer.AutonomousWorldDesigner`
  - Maps design requests to autonomous generation calls.
  - Maps results and metrics artifacts to autonomous DTOs.
- `DashboardAdapter`
  - Reuses `DashboardDataProvider`.
  - Maps provider DTOs into aggregate `DashboardDTO`.

## DTO Mapping Changes

Added explicit failure-state fields where adapters need safe error reporting:

- `success`
- `error_message`
- existing `status`, `message`, or `summary` fields remain the user-facing state.

Adapters never return raw core objects from public methods.

## Failure Behavior

Adapters do not silently switch to null services.

When a core import or core call fails, adapters:

- catch the exception,
- log an English error,
- return a typed DTO,
- set `success=False`,
- set `status`, `message`, or `summary` to `Core unavailable` or
  `Core execution failed`,
- include the exception text in `error_message`.

Core loading is adapter-local and explicit. This prevents mypy from type-checking
frozen core internals during UI validation while preserving the UI-5 boundary.

## Service Container Integration

Added:

- `ServiceContainer.register_core_adapters()`

Behavior:

- `register_defaults()` registers null services.
- `register_core_adapters()` replaces them with core-backed adapters.
- Core adapters are never activated unless explicitly requested.

Smoke check:

```text
NullDashboardService
DashboardAdapter
```

## Tests

Added tests for:

- core import boundary enforcement,
- explicit adapter activation,
- null services remaining default,
- DTO returns for every adapter,
- failure DTO behavior,
- no raw core object exposure in adapter outputs.

Full UI suite result:

```text
141 passed
```

## Quality Results

Commands run through the project venv:

- `.venv\Scripts\python.exe -m ruff check ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m flake8 ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m mypy ui tests/ui`
  - Result: passed, no issues in 87 source files
- `.venv\Scripts\python.exe -m pytest tests/ui -v`
  - Result: 141 passed

## Import Boundary Scan

Forbidden scan:

```text
rg "from (core|agents)\.|import (core|agents)" ui\pages ui\widgets ui\services
```

Result: no matches.

Adapter core-reference scan:

```text
rg "core\." ui\adapters
```

Result: passed. Core references exist only in `ui/adapters/`.

## Frozen Core Confirmation

This implementation did not modify any frozen core directories or public core
APIs. The current worktree already contains many unrelated dirty files outside
the UI-5 scope; they were not edited for this hito. UI-5 changes were limited
to `ui/adapters/`, `ui/services/service_container.py`, DTO field additions in
`ui/models/`, `tests/ui/`, and this report.

Final status: UI-5 CORE ADAPTERS CERTIFIED

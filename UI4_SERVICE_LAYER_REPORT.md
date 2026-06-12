# UI-4 Service Layer Report

Generated: 2026-06-11

Final status: UI-4 SERVICE LAYER CERTIFIED

## Scope

Implemented the official PySide6 UI service boundary for future UI-5 Core
Adapters. The layer defines DTOs, service Protocol contracts, a dependency
injection registry/container, typed service events, and safe null services.

No real core engines are connected. No agents are executed. No business logic
was added.

## Files Created

- `ui/services/base_service.py`
- `ui/services/dashboard_service.py`
- `ui/services/null_services.py`
- `ui/services/service_exceptions.py`
- `tests/ui/test_null_services.py`
- `tests/ui/test_service_events.py`

## Files Modified

- `ui/event_bus.py`
- `ui/models/__init__.py`
- `ui/models/autonomous_dto.py`
- `ui/models/campaign_dto.py`
- `ui/models/critic_dto.py`
- `ui/models/dashboard_dto.py`
- `ui/models/knowledge_dto.py`
- `ui/models/otbm_dto.py`
- `ui/models/world_dto.py`
- `ui/services/__init__.py`
- `ui/services/autonomous_service.py`
- `ui/services/campaign_service.py`
- `ui/services/critic_service.py`
- `ui/services/knowledge_service.py`
- `ui/services/otbm_service.py`
- `ui/services/service_container.py`
- `ui/services/service_registry.py`
- `ui/services/world_service.py`
- `tests/ui/test_service_container.py`
- `tests/ui/test_service_contracts.py`
- `tests/ui/test_service_registry.py`

## Service Contracts

- `WorldService`
  - `generate_world(request: WorldGenerationRequestDTO) -> WorldDTO`
  - `get_recent_worlds() -> list[WorldDTO]`
  - `get_world_summary(world_id: str) -> WorldSummaryDTO`
- `CriticService`
  - `analyze_world(request: CriticRequestDTO) -> CriticDTO`
  - `get_last_report() -> CriticDTO`
  - `get_heatmaps() -> list[HeatmapDTO]`
- `KnowledgeService`
  - `search(query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]`
  - `find_similar(name: str, entry_type: str) -> list[KnowledgeResultDTO]`
  - `get_metrics() -> KnowledgeMetricsDTO`
- `CampaignService`
  - `generate_campaign(request: CampaignRequestDTO) -> CampaignDTO`
  - `get_last_campaign() -> CampaignDTO`
- `OTBMService`
  - `import_otbm(path: str) -> OTBMImportResultDTO`
  - `export_otbm(request: OTBMExportRequestDTO) -> OTBMExportResultDTO`
  - `validate_otbm(path: str) -> OTBMValidationDTO`
- `AutonomousService`
  - `run_design(request: AutonomousDesignRequestDTO) -> AutonomousResultDTO`
  - `get_iterations() -> list[AutonomousIterationDTO]`
  - `get_metrics() -> AutonomousMetricsDTO`
- `DashboardService`
  - `load_dashboard() -> DashboardDTO`
  - `refresh_dashboard() -> DashboardDTO`

## DTOs

All UI-4 DTOs use `@dataclass(slots=True)`, contain JSON-safe fields, and do
not expose core models.

- World: `WorldGenerationRequestDTO`, `WorldDTO`, `WorldSummaryDTO`
- Critic: `CriticRequestDTO`, `CriticIssueDTO`, `CriticDTO`, `HeatmapDTO`
- Knowledge: `KnowledgeQueryDTO`, `KnowledgeResultDTO`, `KnowledgeMetricsDTO`
- Campaign: `CampaignRequestDTO`, `CampaignStageDTO`, `CampaignDTO`
- OTBM: `OTBMImportResultDTO`, `OTBMExportRequestDTO`,
  `OTBMExportResultDTO`, `OTBMValidationDTO`
- Autonomous: `AutonomousDesignRequestDTO`, `AutonomousIterationDTO`,
  `AutonomousResultDTO`, `AutonomousMetricsDTO`
- Dashboard: `DashboardDTO`, plus existing dashboard summary DTOs

Compatibility aliases were retained for older UI imports:
`KnowledgeDTO`, `OTBMExportDTO`, and `OTBMImportDTO`.

## Registry And Container

- `ServiceRegistry` supports `register(name, service_or_factory)`,
  `resolve(name)`, `unregister(name)`, `has(name)`, and `clear()`.
- Lazy factories are resolved once and cached as singletons.
- Replacement for tests is supported with `force=True` and
  `ServiceContainer.register_mock()`.
- Missing and duplicate services raise descriptive typed exceptions.
- `ServiceContainer.register_defaults()` installs one null service for every
  official service contract.
- Typed getters are available for all seven services.

## Null Services

`ui/services/null_services.py` implements safe placeholders for every service
contract:

- `NullWorldService`
- `NullCriticService`
- `NullKnowledgeService`
- `NullCampaignService`
- `NullOTBMService`
- `NullAutonomousService`
- `NullDashboardService`

Null services never import core, never execute agents, never crash for normal
typed requests, and return DTO defaults with the clear status/message:
`Service not connected`.

## Typed Events

Added or completed these typed dataclass events:

- `WorldGenerationRequestedEvent`
- `WorldGeneratedEvent`
- `CriticAnalysisRequestedEvent`
- `CriticCompletedEvent`
- `KnowledgeQueryRequestedEvent`
- `KnowledgeQueryCompletedEvent`
- `CampaignGeneratedEvent`
- `OTBMImportCompletedEvent`
- `OTBMExportCompletedEvent`
- `AutonomousDesignStartedEvent`
- `AutonomousIterationCompletedEvent`
- `AutonomousDesignCompletedEvent`
- `ServiceErrorEvent`

No string-only service event names are required.

## Tests

Added or updated tests for:

- Service registration and duplicate handling
- Lazy factory resolution and singleton caching
- Replacement and mock overrides
- Unregister and clear behavior
- Missing service errors
- DTO return types for every service contract
- Null service safe behavior
- Typed service event creation and dispatch
- No forbidden `core.*` or `agents.*` imports in `ui/pages`,
  `ui/widgets`, or `ui/services`

## Validation

Commands run through the project venv:

- `.venv\Scripts\python.exe -m ruff check ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m flake8 ui tests/ui`
  - Result: passed, 0 issues
- `.venv\Scripts\python.exe -m mypy ui tests/ui`
  - Result: passed, no issues in 71 source files
- `.venv\Scripts\python.exe -m pytest tests/ui -v`
  - Result: 123 passed
- `.venv\Scripts\python.exe -m coverage run --source=ui/services -m pytest tests/ui`
  and `.venv\Scripts\python.exe -m coverage report --include='ui/services/*'`
  - Result: `ui/services` total coverage 92%
- `.venv\Scripts\python.exe -c "from ui.services.service_container import ServiceContainer; c=ServiceContainer(); c.register_defaults(); print(c.get_dashboard_service())"`
  - Result: returned `NullDashboardService`

## Risks

- Real adapter behavior is intentionally absent until UI-5.
- The existing worktree contains many unrelated dirty files outside the UI-4
  scope; those were not edited for this hito.
- Protocol modules contain ellipsis method bodies, so their individual coverage
  is naturally lower, but the aggregate `ui/services` target is met.

## Frozen Core Confirmation

This UI-4 implementation only changed allowed UI service, UI model, UI event,
test, and report files. It does not import `core.*` or `agents.*` from
`ui/pages`, `ui/widgets`, or `ui/services`, and it does not connect to or
modify frozen core engines.

Final status: UI-4 SERVICE LAYER CERTIFIED

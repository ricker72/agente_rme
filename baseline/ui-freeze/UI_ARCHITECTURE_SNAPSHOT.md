# UI Architecture Snapshot (Frozen)

## Architecture

```
UI Pages
  |
  v
Services
  |
  v
Adapters
  |
  v
Frozen Core
```

## Page Modules

| Page | File | Status |
|------|------|--------|
| Dashboard | `ui/pages/dashboard_page.py` | FROZEN |
| World Studio | `ui/pages/world_page.py` | FROZEN |
| Critic Studio | `ui/pages/critic_page.py` | FROZEN |
| Knowledge Explorer | `ui/pages/knowledge_page.py` | FROZEN |
| Autonomous Designer Workspace | `ui/pages/autonomous_page.py` | FROZEN |
| Settings | `ui/pages/settings_page.py` | FROZEN |
| Campaign | `ui/pages/campaign_page.py` | FROZEN |
| OTBM | `ui/pages/otbm_page.py` | FROZEN |
| Architect | `ui/pages/architect_page.py` | FROZEN |

## Service Layer

| Service | File |
|---------|------|
| Base Service | `ui/services/base_service.py` |
| Dashboard Service | `ui/services/dashboard_service.py` |
| World Service | `ui/services/world_service.py` |
| Critic Service | `ui/services/critic_service.py` |
| Knowledge Service | `ui/services/knowledge_service.py` |
| Autonomous Service | `ui/services/autonomous_service.py` |
| Campaign Service | `ui/services/campaign_service.py` |
| OTBM Service | `ui/services/otbm_service.py` |
| Service Container | `ui/services/service_container.py` |
| Service Registry | `ui/services/service_registry.py` |
| Null Services | `ui/services/null_services.py` |
| Service Exceptions | `ui/services/service_exceptions.py` |
| Dashboard Data Provider | `ui/services/dashboard_data_provider.py` |

## Adapters (Only layer allowed to reference core)

| Adapter | File |
|---------|------|
| Dashboard Adapter | `ui/adapters/dashboard_adapter.py` |
| World Adapter | `ui/adapters/world_adapter.py` |
| Critic Adapter | `ui/adapters/critic_adapter.py` |
| Knowledge Adapter | `ui/adapters/knowledge_adapter.py` |
| Autonomous Adapter | `ui/adapters/autonomous_adapter.py` |
| Campaign Adapter | `ui/adapters/campaign_adapter.py` |
| OTBM Adapter | `ui/adapters/otbm_adapter.py` |
| Helpers | `ui/adapters/_helpers.py` |

## DTO Layer

| DTO | File |
|-----|------|
| Dashboard DTO | `ui/models/dashboard_dto.py` |
| World DTO | `ui/models/world_dto.py` |
| Critic DTO | `ui/models/critic_dto.py` |
| Knowledge DTO | `ui/models/knowledge_dto.py` |
| Autonomous DTO | `ui/models/autonomous_dto.py` |
| Campaign DTO | `ui/models/campaign_dto.py` |
| OTBM DTO | `ui/models/otbm_dto.py` |

## Certified Modules

- UI-1: Foundation
- UI-2: Application Shell
- UI-3: Dashboard
- UI-3.1: Dashboard Hardening
- UI-4: Service Layer
- UI-5: Core Adapters
- UI-6: World Generation Studio
- UI-7: Visual Critic Studio
- UI-8: Knowledge Explorer
- UI-9: Autonomous Designer Workspace

## Application Shell Components

| Component | File |
|-----------|------|
| Main Window | `ui/main_window.py` |
| Sidebar | `ui/sidebar.py` |
| Status Bar | `ui/statusbar.py` |
| Title Bar | `ui/titlebar.py` |
| Navigation | `ui/navigation.py` |
| Page Registry | `ui/page_registry.py` |
| Event Bus | `ui/event_bus.py` |
| Theme | `ui/theme.py` |
| Console | `ui/console.py` |

## Frozen Files

Total UI Python files: **97**
Total UI tests: **45**

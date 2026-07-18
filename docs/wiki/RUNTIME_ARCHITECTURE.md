# Runtime Architecture

## Agent

- `rme_ai_studio_launcher.py` starts the desktop runtime.
- `rme.py` exposes the supported agent entry surface.
- `core/world_generator/color_first_map_pipeline.py` coordinates semantic planning, material resolution, ecological distribution, criticism, and OTBM materialization.
- `core/world_generator/planner_knowledge_database.py` compiles official catalogs and abstract reference knowledge into SQLite.
- `core/otbm` and `core/world_generator/otbm_world` own OTBM parsing, mutation, serialization, and roundtrip validation.
- `rme_rendering` owns sprite-backed rendering independently from UI packages.

## Workspace

The desktop editor at `C:/Users/samatha/Videos/rme_workspace/rme_workspace` is a separate application boundary.

- `main.py` and `mainwindow.py` own process and window lifecycle.
- `workspace_core/adapter.py` bridges documents to the certified agent core.
- `workspace_core/editor` owns commands, transactions, selection, metadata, brushes, borders, dirty regions, and visual feedback.
- `workspace_core/rendering` owns appearance lookup, sprite resolution, stack rendering, and visible-tile calculation.
- `viewport` and `panels` are presentation layers; they must not implement map rules.

## Dependency rule

UI may call editor services. Editor services may call the certified core. The certified core must never import UI code. OTBM writing occurs only after material, gameplay, repetition, visual, and roundtrip gates pass.

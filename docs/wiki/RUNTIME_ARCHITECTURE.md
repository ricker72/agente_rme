# Runtime Architecture

## Agent

- `rme_ai_studio_launcher.py` starts the desktop runtime.
- `rme.py` exposes the supported agent entry surface.
- `core/world_generator/color_first_map_pipeline.py` coordinates semantic planning, material resolution, ecological distribution, criticism, and OTBM materialization.
- `core/world_generator/planner_knowledge_database.py` compiles official catalogs and abstract reference knowledge into SQLite.
- `core/world_generator/reference_corpus_live_service.py` watches the complete
  reference corpus, rebuilds it in a staging database, validates integrity, and
  publishes it without stopping live Planner readers.
- `core/otbm` and `core/world_generator/otbm_world` own OTBM parsing, mutation, serialization, and roundtrip validation.
- `rme_rendering` owns sprite-backed rendering independently from UI packages.
- `RME_AGENT_ASSET_PATH` identifies the startup-validated external Tibia `assets`
  directory. Shared render consumers resolve this path before repository metadata.
- Client assets and RME materials are separate runtime authorities. `asset_root`
  contains `appearances-*.dat`, `catalog-content.json`, and sprite sheets only;
  it must never be used to resolve `data/materials`. `material_root` identifies a
  complete RME tree rooted at `materials.xml`, with `brushs`, `borders`, and
  `tilesets` imports. Source runs use Canary's `data/materials`; frozen Workspace
  builds use their packaged `resources/materials` copy.

## Workspace

The desktop editor at `C:/Users/samatha/Videos/rme_workspace/rme_workspace` is a separate application boundary.

- `main.py` and `mainwindow.py` own process and window lifecycle.
- `workspace_core/adapter.py` bridges documents to the certified agent core.
- `workspace_core/editor` owns commands, transactions, selection, metadata, brushes, borders, dirty regions, and visual feedback.
- `workspace_core/editor/creature_catalog_loader.py` owns the certified Monster
  and NPC type catalog. It parses the Lua/XML grammar accepted by RME and merges
  map sidecars only as unresolved instance references.
- `workspace_core/rendering` owns appearance lookup, sprite resolution, stack rendering, and visible-tile calculation.
- `workspace_core/startup.py` requires one appearances file, the official catalog,
  and every reachable sprite sheet before the certified editor is initialized.
- Workspace packages do not embed Tibia client sprite sheets. First-run setup stores
  the selected external client path under the current user's application settings.
- `workspace_core/runtime.py` resolves the external client asset root and the
  packaged/source material root independently, then passes both paths explicitly
  across `WorkspaceAgentService`. A client folder must not become a core or material
  search root.
- Monster and NPC Lua directories are independent persisted preferences. Palette
  rows become editable only when their type declaration has a concrete official
  outfit; model or filename guesses cannot cross this boundary.
- `viewport` and `panels` are presentation layers; they must not implement map rules.
- `viewport/map_scene.py` keeps one current-floor chunk cache and one projected-floor
  overlay chunk cache. Both are bounded to the visible region plus the RME-style
  safety ring; viewport movement must not trigger a whole-map or full-overlay read.
- Viewport refresh has two phases. Current-floor chunks intersecting the visible
  rectangle are rendered synchronously; the surrounding safety ring and projected
  floor overlays are queued independently. Existing pixmaps remain visible until
  their replacements are ready, so panning cannot expose avoidable blank sectors.
- `app_theme.py` owns the successor UI theme. Black surfaces, restrained gold focus
  states, and popup shadows are presentation choices only and never alter RME map,
  brush, ItemType, selection, or transaction semantics.
- `panels/properties_panel.py` reads ItemType text capabilities through
  `workspace_core/adapter.py` and commits one copy-on-write metadata transaction.
  Numeric ID rules remain in `workspace_core/editor/metadata_editor.py` and the
  certified Agent validator, rather than being trusted to UI-only checks.
- `workspace_core/adapter.py` owns one exact `RMEItemTypeCatalog` instance for the
  active appearances file and official material tree. Painting, properties, stack
  QA, and viewport observation receive that same instance. A visual observer must
  wait for it or report one catalog-unavailable blocker; rebuilding a partial
  catalog per viewport is forbidden.
- The RME palette dock scrolls only its material catalog. Tools and brush-size
  controls retain fixed geometry and remain reachable at the bottom of the dock.

## Dependency rule

UI may call editor services. Editor services may call the certified core. The certified core must never import UI code. OTBM writing occurs only after material, gameplay, repetition, visual, and roundtrip gates pass.

## AI proposal lifecycle

`WorkspaceAgentService.propose()` stores the exact certified semantic plan associated
with the normalized objective. Approval consumes that same plan once; it must not
ask the model network to reinterpret the prompt before materialization. A different
objective invalidates the prepared plan and requires a fresh Planner pass.

Model consultation remains bounded and bidirectional: models may suggest semantic
intent, the Planner may reject or request correction, and only the certified Planner
plan reaches the Brush Engine. Models never write item IDs, tile stacks, borders, or
OTBM nodes directly. Approval and visual application run outside the Qt UI thread and
are committed as one atomic editor action after QA passes.

Each provider attempt has one total deadline shared by model fallback, schema retry,
and correction retry. AI Studio remains responsive in a worker thread and displays
elapsed Planner/model time. A hierarchical result of `NOT_REQUESTED` is successful
for terrain-only objectives; only `BLOCKED` or invalid hierarchy output blocks the
proposal. The local Planner server publishes a protocol version and process ID so a
new runtime can replace a verified stale local instance without binding two servers.
Protocol v4 also exposes authenticated live-reference status and refresh routes.
The server always writes to the user's writable Planner database; a packaged
database is copied there once and is never mutated in place.

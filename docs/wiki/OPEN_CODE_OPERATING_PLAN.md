# Open Code Operating Plan

This plan is mandatory for Open Code or any programming AI before touching
Agente RME AI, RME Workspace, the Planner, the local server, databases, builds,
or OpenTibia map/runtime code.

## Prime Directive

Use only functional OpenTibia/RME/Canary-backed code. Do not invent item IDs,
flags, OTBM structures, brush behavior, menu behavior, AI shortcuts, renderer
rules, or success states. If the behavior is not proven by the wiki, current
runtime code, Canary/RME sources, official material XML, OTB/appearance data, or
a real validation run, stop and report the missing evidence.

## Mandatory Startup Sequence

1. Read `AGENTS.md`.
2. Run:

```powershell
python scripts/preflight.py --project-root "C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme" --intent "<exact task>"
```

3. Read these wiki pages before planning edits:
   - `docs/wiki/README.md`
   - `docs/wiki/AI_CODE_GUARDIAN.md`
   - `docs/wiki/RUNTIME_ARCHITECTURE.md`
   - `docs/wiki/RME_COMPATIBILITY.md`
   - `docs/wiki/CODE_CLEANUP_POLICY.md`
   - `docs/wiki/GITHUB_STORAGE_POLICY.md`
   - `docs/wiki/SECRET_HANDLING_POLICY.md`
   - this page
4. Inspect the task-specific active runtime path. Do not edit isolated files.
5. Inspect the official Canary/RME source or material data that owns the
   behavior before editing.
6. State the evidence files in the work update.

## Where To Search

Agente RME AI:

```text
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme
```

RME Workspace:

```text
C:\Users\samatha\Videos\rme_workspace\rme_workspace
```

Current Canary/RME source authority:

```text
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme\projects\canary-extracted\canary-map-editor-v4.0-windows\source
```

Official materials:

```text
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme\projects\canary-extracted\canary-map-editor-v4.0-windows\data\materials
```

Official assets configured by the user:

```text
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme\assets
C:\Users\samatha\OneDrive\Desktop\15.24 localhost\assets
```

Reference maps:

```text
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme\projects\Mapas Referencia
C:\Users\samatha\OneDrive\Documentos\GitHub\agente_rme\projects\world\world.otbm
```

Workspace logs:

```text
C:\Users\samatha\AppData\Local\Agente RME\RME Workspace\logs\rme_workspace.log
```

## Active Runtime Paths

For map generation:

```text
core/world_generator/color_first_map_pipeline.py
core/world_generator/planner_*.py
core/world_generator/reference_*.py
core/world_generator/scene_graph*.py
core/editor/certified_otbm_service.py
```

For Workspace UI and editor behavior:

```text
C:\Users\samatha\Videos\rme_workspace\rme_workspace\main.py
C:\Users\samatha\Videos\rme_workspace\rme_workspace\mainwindow.py
C:\Users\samatha\Videos\rme_workspace\rme_workspace\workspace_core\adapter.py
C:\Users\samatha\Videos\rme_workspace\rme_workspace\workspace_core\editor
C:\Users\samatha\Videos\rme_workspace\rme_workspace\workspace_core\rendering
C:\Users\samatha\Videos\rme_workspace\rme_workspace\panels
```

For packaging:

```text
C:\Users\samatha\Videos\rme_workspace\rme_workspace\rme_workspace.spec
C:\Users\samatha\Videos\rme_workspace\rme_workspace\build_release.py
C:\Users\samatha\Videos\rme_workspace\rme_workspace\workspace_core\artifact_retention.py
```

## Hung Process Rules

Before rebuilding or replacing a build, inspect running processes. Kill only a
process whose executable path or command line points inside the Workspace build
or source tree.

Recommended inspection:

```powershell
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -match 'RME_Agente_AI|python|pyinstaller'
  } |
  Select-Object ProcessId, Name, ExecutablePath, CommandLine
```

Safe stop rule:

- Prefer closing the app normally.
- If it is hung, stop only the specific PID whose path is under
  `C:\Users\samatha\Videos\rme_workspace\rme_workspace`.
- Never kill unrelated Python, Ollama, browser, editor, or system processes.
- Never use broad commands such as killing every `python.exe`.

## Failure Recovery

If a build fails:

- Keep the last successful `dist_current`.
- Do not delete the last working executable.
- Read the PyInstaller/build log and Workspace runtime log.
- Revert only the current failed patch or create a targeted repair. Do not run
  destructive git commands.

If startup fails:

- Inspect `rme_workspace.log`.
- Check for missing bundled modules, missing materials, missing assets, stale
  saved layout, and PySide object lifetime errors.
- Validate from source with `python -m py_compile` before rebuilding.

If map loading fails:

- Confirm the OTBM file opens in Canary/RME.
- Route through `workspace_core.adapter` and the certified editor boundary.
- Preserve unknown OTBM payloads. Do not rewrite full files unless the
  certified writer confirms compact/lossless behavior.

If materials are empty:

- Verify `resources/materials` exists in source and build.
- Verify `brushs.xml`, `borders.xml`, `tilesets.xml`, `materials.xml`, and the
  `brushs`, `borders`, `tilesets` folders are bundled.
- Run the material loader from the active Workspace environment and inspect its
  summary. Do not replace official material XML with invented fallback data.

## RME Parity Rules

Before implementing editor behavior, inspect Canary/RME for the same feature:

- Menu and toolbar behavior: `source/main_menubar.cpp`, `data/menubar.xml`.
- Palettes and brushes: `source/palette*`, `source/brush.*`,
  `source/ground_brush.*`, `source/wall_brush.*`,
  `source/doodad_brush.*`, `source/house_brush.*`, material XML.
- Rendering: `source/map_drawer.*`, `source/gui.cpp`, OpenGL render code,
  item draw order, elevation, animation, and minimap colors.
- OTBM IO: `source/iomap*`, `source/otbm*`, item attribute handling.
- Houses, spawns, NPCs, monsters, towns, waypoints, and zones: inspect the
  matching source files and official server data.

Port semantics into the existing Workspace/core boundary. Do not duplicate a
second editor engine inside UI code.

## AI And Planner Rules

AI output is advice, not map data. The allowed path is:

```text
Prompt
  -> Planner semantic plan
  -> Reference/style lookup with provenance
  -> Material resolver
  -> Certified brush engines
  -> Atomic transaction
  -> OTBM roundtrip validation
  -> Visual QA
  -> Human-visible proposal/commit
```

The AI network must never:

- Write raw tile stacks directly.
- Invent item IDs, material families, spawns, NPCs, quest actions, storages, or
  object attributes.
- Bypass `MaterialSafetyValidator`, Similarity Guard, visual QA, or OTBM
  validation.
- Store API keys, prompts containing secrets, or user-specific credentials in
  source, logs, builds, Git history, or Planner databases.

## Validation Checklist

Before claiming a fix:

1. Compile changed Python files with `python -m py_compile`.
2. Run the repo preflight.
3. Start the real Workspace entry point or packaged executable.
4. Inspect the runtime log for unhandled exceptions.
5. For materials, confirm palette categories and entries are loaded.
6. For editor changes, perform a real map mutation through the UI/core boundary.
7. For map generation, export OTBM and open it in Canary/RME.
8. For packaging, confirm only the current successful build remains.
9. Before Git publication, run the size guard and secret guard.

## Prohibited Shortcuts

- Vibe coding.
- Placeholder production code.
- Mock success reports.
- Name-based item safety inference.
- Hardcoded fake IDs or fallback material IDs.
- Duplicate renderer, duplicate brush engine, or duplicate OTBM writer.
- UI code mutating map files directly.
- Deleting broad folders without proving they are generated or obsolete.
- Shipping official assets, generated databases, maps, builds, or secrets as
  normal Git blobs.

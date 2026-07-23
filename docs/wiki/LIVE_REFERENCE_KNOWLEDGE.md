# Live Reference Knowledge

## Purpose

The local Planner server watches `projects/Mapas Referencia` and persists
coordinate-free knowledge while Agente RME AI and Workspace remain online.
Reference maps are evidence for style and construction grammar only. Their source
coordinates, tile stacks, chunks, screenshots, and geometry are never exposed to a
model or reused by the Planner.

## Refresh lifecycle

1. `ReferenceCorpusLiveService` watches `.otbm` maps and their `.xml` sidecars.
2. Changes are debounced before a refresh begins.
3. `ReferenceMapCorpusAnalyzer` scans every reference into a staging copy of the
   Planner SQLite database.
4. The staging database must pass `PRAGMA integrity_check`.
5. A second source snapshot must match the one taken before scanning. If a map
   changed during the scan, staging is discarded and queued again.
6. SQLite backup publishes the validated staging state into the writable live
   database. Existing readers continue using a complete database during the scan.
7. The service stores completion state and automatically repeats this process after
   later map changes. A server restart is not required.

The service keeps a local `reference_corpus_state.json` manifest beside the writable
Planner database. Matching file size and modification-time records make normal
restarts immediate. If the manifest is absent or stale, full SHA-256 validation runs
in a background thread while the last certified database remains readable; a real
mismatch schedules an atomic rebuild.

The server endpoints `/v1/knowledge/status` and
`/v1/knowledge/reference-refresh` expose bounded status and an explicit refresh
request. They require the same loopback token as all other Planner operations.

## Extracted evidence

Each reference contributes:

- floor ranges, density, minimap colors, and official material usage;
- complete official brush-family coverage;
- ground transitions and ground/border mixtures;
- coordinate-free adjacency between ecological GroundBrush, DoodadBrush, and
  WallBrush families;
- stairs, ramps, ladders, and vertical support detected from the official
  `Stairs / Ramps / Ladders` tileset;
- aggregate building and biome grammar already supported by the reference scanner.

Connector membership comes from Canary/RME
`data/materials/tilesets/stairs.xml`. Border and wall behavior remains owned by
`GroundBrush::doBorders`, `WallBrush::doWalls`, and `Tile::borderize` /
`Tile::wallize`; the scanner does not invent equivalent IDs or orientations.

## Planner contract

The certified reference brief can provide family coverage, biome-family mixtures,
and vertical connector statistics. These values guide original topology. Exact
source geometry remains unavailable and every generated map still passes material,
similarity, gameplay, visual, and OTBM roundtrip gates.

# RME Compatibility

## Official sources

- `projects/canary-extracted/canary-map-editor-v4.0-windows/source`
- `projects/canary-extracted/canary-map-editor-v4.0-windows/data/materials`
- `assets/appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat`
- `assets/catalog-content.json`

The repository copies above are metadata inputs, not a complete render client. A
render-capable runtime also requires the `sprites-*.bmp.lzma` files named by the
selected client's `catalog-content.json`. They remain external and are selected by
the Workspace startup gate; a metadata-only folder must fail validation.

## Required contracts

- Workspace palettes load from their autonomous official
  `resources/materials` distribution. A valid tree contains `materials.xml`,
  `brushs.xml`, `borders.xml`, `tilesets.xml`, and non-empty imported XML trees
  for brushes, borders, and tilesets. Missing material data is a startup/build
  failure; synthetic empty tilesets are forbidden.
- Source runtimes resolve the canonical Canary `data/materials` tree. Frozen
  Workspace runtimes resolve the packaged `resources/materials` tree from the
  application bundle. Both paths pass the same complete-tree validation before
  `RMEBrushEngine` is constructed; falling through to an empty catalog is
  forbidden.

- GroundBrush replaces the ground and preserves unrelated stack items.
- WallBrush resolves alignment before selecting a positive-chance member and reorients affected neighbors in the same action.
- DoodadBrush selects one weighted alternative and preserves composite offsets and stack order.
- AutoBorder uses the complete eight-neighbor mask and can emit several border pieces per tile.
- Table and carpet connected-item post-processing is independent from AutoMagic.
- OTBM loaded stack order is retained; the renderer does not broadly resort it.
- Every emitted item is sprite-backed and certified by exact ItemType flags.
- Viewport QA uses the editor's active exact ItemType catalog. It must not create a
  metadata-only fallback catalog that labels valid grounds or stack items as
  uncertified.
- Unknown OTBM payloads are preserved by copy-on-write mutation.

## Field context menu

The Workspace field menu follows `source/map_display.cpp` rather than exposing
always-enabled placeholders.

- Cut, Copy, and Delete require a committed selection; Paste requires a non-empty
  editor clipboard.
- Copy Item ID and Copy Item Name require exactly one resolved stack item.
- Select RAW resolves the clicked item. Ground, wall, carpet, table, doodad, door,
  and house selectors appear only when the clicked stack has a real owning brush or
  house relationship in the official catalogs.
- Properties is enabled only for editable tile or item metadata. Browse Field opens
  the complete ordered stack and does not mutate it.
- Menu actions call the same transactional commands used by shortcuts and menus;
  no context-menu-only mutation path is allowed.

## Navigation and readable items

- Arrow-key panning follows RME `MapCanvas::OnKey`: 3 tiles normally, 10
  with Ctrl, and 1 tile at 100% zoom. The Workspace accepts a 1% floating
  tolerance around 100% so a fitted Qt transform does not change the command.
- Visible current-floor and projected-floor sectors are loaded incrementally.
  Incoming chunks are rendered before stale chunks are retired, and projected
  floor overlays are cached by `(chunk_x, chunk_y, z)`.
- `writeable` implies `readable`, matching both Canary and RME item parsing.
  Text controls exist only for `readable`/`writeable` items; description controls
  exist only for `allowdistread`; `maxtextlen` is enforced when present.
- Optional Action IDs are `0` or `100..65535`. Optional Unique IDs are `0` or
  `1000..65535`, as defined by RME `const.h` and checked by its properties dialog.
- Complex-item editing starts from a deep copy of the original attribute map.
  Known fields are replaced while unknown attributes and nested containers remain.

## Model boundary

Cloud or local models produce semantic intent such as `krailos_rocks` or `sea`. They do not produce numeric IDs. The Contextual Material Resolver maps intent to an official brush token, and the Brush Engine chooses the concrete member using the official grammar.

Town metadata such as `Town: Ika` names the output town but does not by itself request
a complete city. The Hierarchical Architectural Planner derives buildings only from
explicit design intent. A compact temple has one materialization owner, a broad open
threshold, a complete PZ interior, and no DoorBrush item; it must not be repainted by
the generic settlement fallback.

## Menus, creatures and spawns

The command contract was audited against
`opentibiabr/remeres-map-editor` commit
`57ee0e5b915909f207aa7a60968c8ed6e4f7f406`, especially
`data/menubar.xml`, `source/main_menubar.cpp`, `source/palette_monster.cpp`,
`source/palette_npc.cpp`, `source/spawn_monster.cpp`, and
`source/spawn_npc.cpp`.

- `Edit`, `Map`, `Select`, `View`, and `Window` preserve the official command
  hierarchy and shortcuts. A visible command is connected only when the
  Workspace owns a certified operation. Unsupported commands remain disabled;
  they must never report placeholder success.
- `Find on Map` scans floors 0 through 15. `Find on Selection` is restricted to
  the committed selection. Unique ID, Action ID, nested-container, writeable,
  and duplicate searches use lossless item attributes and exact ItemType flags.
- Monster placement requires ground, a walkable tile, compatible spawn coverage,
  and rejects protection zones. NPC placement permits protection zones and
  replaces an existing NPC, matching RME.
- Monster and NPC spawn centers require ground and use a square area with side
  `2 * radius + 1`. Spawn time is bounded to `0..3600` in palette controls;
  selection updates require `1..3600`.
- Monster spawn candidate rows are checkable and sorted. The official density
  control is labelled as a percentage but declares the range `0..3600` in
  `palette_monster.cpp`; default weight is `0..100`. A materializer must still
  bound placement by the finite `((2 * radius) + 1)^2` candidate positions.
  Numeric creature or item IDs are never accepted from model output.
- Empty-spawn cleanup searches the complete square radius for an entity of the
  matching kind and commits removal as one atomic action.

Creature type catalogs are not reconstructed from map spawn sidecars. RME v4
loads them from the user-configured Monster and NPC Lua directories. The exact
accepted Lua declarations are `Game.createMonsterType("name")` or
`local internalMonsterName = "name"`, and `Game.createNpcType("name")` or
`local internalNpcName = "name"`. A definition also needs an outfit assignment
and a concrete `lookType` or `lookTypeEx`. XML fallback accepts `<monster>` and
`<npc>` roots with `type`, `item`, `lookex`, or `typeex`; an XML NPC is named from
its filename stem. Spawn sidecars provide instances only.

The Workspace persists both directories in `File > Preferences`, rebuilds the
certified catalogs, and refreshes the Monster and Npc palettes. Unknown names
remain visible but disabled. It is forbidden to infer a look type from a name,
to invent an outfit, or to treat a sidecar instance as a resolved type.

RME can associate several monsters with a spawn area. The current Workspace
`TileStack` owns one creature field per coordinate. Placing a second different
monster on an occupied coordinate therefore fails closed with
`RME-MULTI-MONSTER-MODEL` until a lossless multi-creature representation is
implemented.

## Canonical world source

The Planner town scanner reads town identifiers, names, and temple positions
from canonical OTBM `TOWN` nodes. Large official worlds are resolved from
`RME_WORLD_OTBM`; the historical `projects/world/world.otbm` path remains the
default when present. House, monster, and NPC evidence comes from sibling
`<stem>-house.xml`, `<stem>-monster.xml`, and `<stem>-npc.xml` files.

This keeps the 194 MiB world outside normal Git history while preserving exact
OpenTibia evidence. The derived town-anchor cache is published atomically and
is accepted only when its SHA-256 matches the selected world.

## OTBM file identifier compatibility

Canary/RME `DiskNodeFileReadHandle` accepts either the four-byte wildcard
identifier (`00 00 00 00`) or the configured identifier. `IOMapOTBM` configures
that identifier as `OTBM`. The certified importer, validator, inspector, and
deserializer therefore accept both read signatures, followed by the root node
marker. Writers keep their configured canonical output and do not rewrite a
source file merely because it uses the other accepted identifier.

This rule is evidenced by `source/filehandle.cpp` and
`source/iomap_otbm.cpp`. It prevents valid RME maps such as
`roshamuul_map.otbm` from being rejected while still failing closed for any
other signature.

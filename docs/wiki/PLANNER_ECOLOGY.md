# Planner Ecology

## Pipeline

1. The semantic Planner creates original regions, routes, structures, habitats, and gameplay anchors.
2. The Contextual Material Resolver selects official GroundBrush, WallBrush, and DoodadBrush families.
3. `EcologicalDistributionPlanner` classifies buildable tiles as coast, dry, oasis, or rocky habitat.
4. A density budget allocates bounded quotas to semantic families.
5. Candidates are ranked deterministically and filtered by structures, roads, gameplay buffers, habitat, and minimum spacing.
6. `RepetitionCritic` checks family dominance, connected repetition, and spacing.
7. Deterministic repair removes low-priority violations and recomputes the complete audit.
8. Any unresolved violation blocks OTBM export.

## Krailos budget

The current compact Krailos profile uses official semantic families only: Krailos plants, forest shrubs, Krailos rocks, dry rock details, Krailos mountains, and dark fungi. The weights are targets, not permission to exceed each family's maximum share.

Reference maps contribute ratios and grammar, never copied coordinates or tile stacks. Generated geometry remains original and is protected by the Similarity Guard.

## Complete reference corpus

The Planner server continuously scans every `.otbm` under
`projects/Mapas Referencia`. It derives official brush-family coverage,
coordinate-free biome-family adjacency, and vertical connector support. This lets
the Planner distinguish, for example, a mountain surface from its stairs, ramps,
walls, borders, and neighboring nature families without copying the source
mountain footprint.

Only GroundBrush, DoodadBrush, and WallBrush roles participate in ecological
mixture statistics. Carpet, table, and border memberships remain available in
family coverage but cannot be mistaken for a dominant biome.

## Roshamuul reference profile

`projects/Mapas Referencia/Islas/roshamuul_map.otbm` is an analysis-only
reference. Its SHA-256 is
`290e61106af61796e94b8c9358ed220f4d7a3ca68db05a79b3581e41d1150900`.
The full-file scan covers floors 6 through 8 and records:

- 286,605 tiles and 3,375 used material IDs;
- 483 official brush families;
- 3,113 ground transitions and 12,005 ground/border mixtures;
- 47 floor-aware minimap colors linked to 1,315 material selections.

Dominant official families include `sea`, `mountain`, `muddy sand`,
`swamp clay mountain`, `terracotta`, `sand`, `earth`, `lush meadow`,
`mossy floor`, `rock soil`, `loose gravel`, `roshamuul pavement`, and
`dry grass tufts`. Counts are stored in the Planner database and must be used
as density and compatibility evidence, not as fixed output quotas.

When a prompt explicitly names Roshamuul, the reference selector prioritizes
this profile over generic thematic matches such as mountain or cave maps.
Neither the Planner nor a model receives source coordinates, tile stacks, or
screenshots. Generated geometry must remain original and pass the Similarity
Guard.

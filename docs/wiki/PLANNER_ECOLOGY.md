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

# Critic Report — deep_orc_cave_100

_Generated: 2026-06-08T15:14:22.835072  •  Version: 1.0_

## Overall Score: **62.1 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 49.3 |
| navigation | 85.0 |
| density | 40.6 |
| spawn | 54.0 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 60.0 |
| decor | 71.6 |
| pathfinding | 100.0 |

## Issues (9)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | underdecorated_area | visual | - | Only 24% of ground tiles have content |
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,49,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (49,0,7) | Bottleneck: only 2 connections |
| warning | underdecorated_area | density | - | Only 5% of tiles have content |
| warning | spawn_cluster | spawn | (0,2) | Spawn cluster of 3 creatures at (0, 2) |
| warning | spawn_cluster | spawn | (0,9) | Spawn cluster of 6 creatures at (0, 9) |
| warning | spawn_cluster | spawn | (0,14) | Spawn cluster of 4 creatures at (0, 14) |
| warning | empty_region | region | hunt_orc_cave | Region 'hunt_orc_cave' is empty or near-empty (0 tiles) |

## Recommendations (6)

### Add visual content
_Priority: medium  •  Category: visual_

Large portions of the map are visually empty. Add items, spawns or decoration.

### Add decoration to empty areas
_Priority: medium  •  Category: density_

Large portions of the map are empty. Add decoration, structures or spawns to improve density.

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Define boss arenas
_Priority: low  •  Category: boss_

Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.

### Define city zones
_Priority: low  •  Category: city_

Add zones with names containing 'city', 'town', 'village', 'hub' or 'market'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: hunt_orc_cave. Add tiles, decoration or remove them.

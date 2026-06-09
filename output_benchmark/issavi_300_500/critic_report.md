# Critic Report — issavi_300_500

_Generated: 2026-06-08T15:14:20.909206  •  Version: 1.0_

## Overall Score: **66.0 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 79.7 |
| navigation | 57.0 |
| density | 40.2 |
| spawn | 55.6 |
| hunt | 70.9 |
| boss | 100.0 |
| city | 100.0 |
| decor | 56.4 |
| pathfinding | 54.3 |

## Issues (18)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| error | isolated_region | navigation | - | Map has 7 disconnected regions |
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,29,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (29,0,7) | Bottleneck: only 2 connections |
| warning | spawn_cluster | spawn | (50,5) | Spawn cluster of 3 creatures at (50, 5) |
| warning | spawn_cluster | spawn | (50,10) | Spawn cluster of 3 creatures at (50, 10) |
| warning | spawn_cluster | spawn | (50,15) | Spawn cluster of 3 creatures at (50, 15) |
| warning | hunt_gap | hunt | - | Hunts 0 and 2 are 120 tiles apart — consider adding a closer hunt |
| warning | underdecorated_area | decor | - | Only 3 unique decoration types — map looks repetitive |
| warning | overdecorated_area | decor | - | Item 777 represents 43% of decorations |
| warning | empty_region | region | city_issavi | Region 'city_issavi' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_issavi_depot | Region 'city_issavi_depot' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_issavi_temple | Region 'city_issavi_temple' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_issavi_npc | Region 'city_issavi_npc' is empty or near-empty (0 tiles) |
| critical | isolated_region | pathfinding | - | Only 39% of tiles are reachable from entry point |
| warning | bottleneck | pathfinding | (180,180,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (219,180,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (180,219,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (6)

### Connect disconnected regions
_Priority: high  •  Category: navigation_

There are 7 disconnected map regions. Add paths, doors, teleporters or stairs to connect them.

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Increase decoration variety
_Priority: medium  •  Category: decor_

Map uses only 3 unique items. Add more decoration variety.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: city_issavi, city_issavi_depot, city_issavi_temple, city_issavi_npc. Add tiles, decoration or remove them.

### Connect isolated regions
_Priority: critical  •  Category: pathfinding_

Several map regions are unreachable. Add paths, doors or teleporters to connect them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.

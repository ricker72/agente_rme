# Agente RME v1.1 Technical Scope

## Snapshot Metadata

```json
{
  "status": "FROZEN",
  "release": "ui-v1.0",
  "support": "SUPPORTED"
}
```

## Scope Boundary

v1.1 development must build on the certified UI v1.0 baseline without destabilizing the supported `release/ui-v1` branch. New work belongs on `develop`, `feature/*`, or `release/v1.1`.

## World Generator 2.0 Scope

- City layout generation with districts, roads, landmarks, service zones, and entrance logic.
- Hunt generation with spawn distribution, density tuning, traversal flow, and reward pacing.
- Dungeon generation with room graphs, loops, encounter pacing, locked areas, and exit guarantees.
- Boss area generation with arena design, telegraph space, hazards, and access routes.
- Quest chain generation with objectives, dependencies, NPC/area links, and reward progression.

## Blueprint Intelligence 2.0 Scope

- Extract reusable structural patterns from Issavi, Roshamuul, Soul War, Falcon Bastion, Library, and Ferumbras.
- Convert learned patterns into generator constraints and templates.
- Track pattern provenance so generated layouts can be audited.
- Preserve adapter boundaries between UI, services, and core generation systems.

## Visual Critic 2.0 Scope

- Pathing analysis for connectivity, bottlenecks, loops, travel distance, and stuck-risk.
- Density analysis for walkability, spawn pressure, feature placement, and visual clutter.
- Spawn quality analysis for encounter balance, monster grouping, and escalation.
- Progression analysis for unlock flow, difficulty curve, and navigational readability.
- Reward loop analysis for risk/reward pacing and replay incentives.

## Autonomous Designer 2.0 Scope

- Implement the Generate -> Critic -> Improve loop as a controlled workflow.
- Support target score, iteration limit, and stop-condition configuration.
- Preserve human-readable iteration history and artifact traceability.
- Keep long-running work asynchronous and UI-safe.

## Out Of Scope For v1.1 Planning

- Changes to the frozen `release/ui-v1` production branch.
- Redesign of the certified v1.0 UI shell.
- Installer/signing work unless separately scheduled.

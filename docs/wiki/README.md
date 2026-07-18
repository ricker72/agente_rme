# RME Agente AI Code Wiki

This wiki describes the executable editor and mapper code. It is intentionally limited to reachable runtime modules, certified OpenTibia data, and behavior verified against Canary Map Editor v4.

## Pages

- [Runtime architecture](RUNTIME_ARCHITECTURE.md)
- [RME compatibility](RME_COMPATIBILITY.md)
- [Planner ecology](PLANNER_ECOLOGY.md)
- [Code cleanup policy](CODE_CLEANUP_POLICY.md)
- [AI code guardian](AI_CODE_GUARDIAN.md)
- [GitHub storage policy](GITHUB_STORAGE_POLICY.md)
- [Secret handling policy](SECRET_HANDLING_POLICY.md)

## Authority order

1. Canary/RME source and official material XML.
2. `appearances-*.dat`, `catalog-content.json`, OTB item flags and OTBM structure.
3. Abstract metrics from `world.otbm` and reference OTBM maps.
4. Planner semantic rules constrained by the first three sources.
5. Model suggestions. A model never has authority to create an item ID or bypass validation.

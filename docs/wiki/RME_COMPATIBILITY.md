# RME Compatibility

## Official sources

- `projects/canary-extracted/canary-map-editor-v4.0-windows/source`
- `projects/canary-extracted/canary-map-editor-v4.0-windows/data/materials`
- `assets/appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat`
- `assets/catalog-content.json`

## Required contracts

- GroundBrush replaces the ground and preserves unrelated stack items.
- WallBrush resolves alignment before selecting a positive-chance member and reorients affected neighbors in the same action.
- DoodadBrush selects one weighted alternative and preserves composite offsets and stack order.
- AutoBorder uses the complete eight-neighbor mask and can emit several border pieces per tile.
- Table and carpet connected-item post-processing is independent from AutoMagic.
- OTBM loaded stack order is retained; the renderer does not broadly resort it.
- Every emitted item is sprite-backed and certified by exact ItemType flags.
- Unknown OTBM payloads are preserved by copy-on-write mutation.

## Model boundary

Cloud or local models produce semantic intent such as `krailos_rocks` or `sea`. They do not produce numeric IDs. The Contextual Material Resolver maps intent to an official brush token, and the Brush Engine chooses the concrete member using the official grammar.

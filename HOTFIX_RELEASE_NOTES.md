
### Performance

- 200 consecutive generations executed as a stress
  test. Per-generation average: 313.63 ms.
- No memory leak detected (rss_growth = 0.0 MiB).

## Upgrade Notes

Drop-in replacement for v1.0.0 GA. No data migration
required. Existing OTBM and Lua files continue to work
without modification.

## Sign-off

- Release Engineering: Agente RME Release Engineering
- QA: Auto-cert pipeline (hotfix/v1.0.1)
- Status: **STABLE**
- Support tier: **STANDARD**

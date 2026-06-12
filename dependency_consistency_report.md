# Dependency Consistency Report
**Agente RME v1.0.0 GA**
**Date:** 2026-06-10 22:54:34

---

## Summary

| Metric | Value |
|---|---|
| Modules Scanned | 506 |
| Modules Loaded | 506 |
| Modules Failed | 0 |
| Missing References | 903 |
| Orphan Modules | 382 |
| Circular Imports | 0 |
| Critical Legacy Refs | 15 |
| WARNING Legacy Refs | 45 |
| UI Violations | 0 |
| Agent Import Failures | 0 |
| Pipeline Discovery Failures | 8 |

---

## Detailed Results

### Check 1: Import Validation
- Scanned: 506, Loaded: 506, Failed: 0

### Check 2: Missing References & Orphans
- Missing: 903, Orphans: 382
- First 20 missing refs:
  - `boss_generator` -> `asset_registry`
  - `boss_generator` -> `map_designer`
  - `boss_generator` -> `world_model`
  - `core` -> `architecture`
  - `core` -> `playtest`
  - `core` -> `preview`
  - `core` -> `otbm`
  - `core` -> `compiler`
  - `core` -> `factory`
  - `core` -> `quality`
  - `core` -> `world_engine`
  - `core` -> `enterprise`
  - `core` -> `game_design`
  - `core` -> `planner`
  - `core.agents` -> `mapper_agent`
  - `core.agents` -> `agent_registry`
  - `core.agents` -> `balance_agent`
  - `core.agents` -> `orchestrator_agent`
  - `core.agents` -> `architect_agent`
  - `core.agents` -> `critic_agent`
- First 20 orphans:
  - `benchmark_autonomous`
  - `benchmark_blueprint_intelligence`
  - `benchmark_critic`
  - `benchmark_knowledge`
  - `check_utcnow`
  - `cli`
  - `core.agents`
  - `core.agents.agent_registry`
  - `core.agents.architect_agent`
  - `core.agents.balance_agent`
  - `core.agents.critic_agent`
  - `core.agents.expansion_agent`
  - `core.agents.export_agent`
  - `core.agents.mapper_agent`
  - `core.agents.orchestrator_agent`
  - `core.agents.playtest_agent`
  - `core.agents.qa_agent`
  - `core.agents.quest_agent`
  - `core.analyzer.architecture_analyzer`
  - `core.analyzer.city_analyzer`

### Check 3: Public API Consistency
- Checked: 59, Passed: 59, Failed: 0

### Check 4: Agent Dependency Graph
- Agents: 10, Failed: 0
  - [OK] `ArchitectAgent`: imports=PASS, constructor=PASS
  - [OK] `MapperAgent`: imports=PASS, constructor=PASS
  - [OK] `ExpansionAgent`: imports=PASS, constructor=PASS
  - [OK] `QuestAgent`: imports=PASS, constructor=PASS
  - [OK] `PlaytestAgent`: imports=PASS, constructor=PASS
  - [OK] `BalanceAgent`: imports=PASS, constructor=PASS
  - [OK] `CriticAgent`: imports=PASS, constructor=PASS
  - [OK] `QAAgent`: imports=PASS, constructor=PASS
  - [OK] `ExportAgent`: imports=PASS, constructor=PASS
  - [OK] `OrchestratorAgent`: imports=PASS, constructor=PASS

### Check 5: UI Dependency Graph
- Status: PASS, Violations: 0

### Check 6: CLI Validation
- rme importable: True
  - [OK] `generate`: PASS
  - [OK] `critic`: PASS
  - [OK] `knowledge`: PASS
  - [OK] `blueprint`: PASS
  - [OK] `autonomous`: PASS
  - [OK] `health`: PASS
  - [OK] `metrics`: PASS
  - [OK] `diagnose`: PASS
  - [OK] `benchmark`: PASS

### Check 7: Legacy Reference Scan
- Total: 134, SAFE: 74, WARNING: 45, CRITICAL: 15
  - [CRITICAL] `check_utcnow.py` L4: Fails if any production .py file contains ``datetime.utcnow()`` or the literal
  - [CRITICAL] `check_utcnow.py` L71: print(f"\nFAIL: {path} contains datetime.utcnow() references.")
  - [CRITICAL] `check_utcnow.py` L83: print(f"\nFAIL: Found {total} datetime.utcnow() reference(s) in production code.
  - [CRITICAL] `check_utcnow.py` L86: print("OK: No datetime.utcnow() found in production code.")
  - [CRITICAL] `core\critic\critic_report.py` L183: generated_at=datetime.datetime.utcnow().isoformat(),
  - [CRITICAL] `core\critic\models\critic_result.py` L82: self.timestamp = datetime.datetime.utcnow().isoformat()
  - [CRITICAL] `fix_utcnow.py` L1: """Replace datetime.utcnow() with datetime.now(timezone.utc) in project files.""
  - [CRITICAL] `fix_utcnow.py` L15: # agent_response.py — uses `import datetime` and `datetime.datetime.utcnow()`
  - [CRITICAL] `fix_utcnow.py` L33: # orchestrator_agent.py — uses `import datetime` and `datetime.datetime.utcnow()
  - [CRITICAL] `fix_utcnow.py` L64: # 1) `datetime.utcnow()` -> `datetime.now(timezone.utc)`

### Check 8: Pipeline Discovery
  - [OK] `Prompt`: PASS
  - [FAIL] `Architect`: NOT_FOUND
  - [OK] `World`: PASS
  - [FAIL] `Expansion`: NOT_FOUND
  - [FAIL] `Playtest`: NOT_FOUND
  - [FAIL] `Balance`: NOT_FOUND
  - [FAIL] `Critic`: NOT_FOUND
  - [FAIL] `Campaign`: NOT_FOUND
  - [FAIL] `Knowledge`: NOT_FOUND
  - [FAIL] `Blueprint`: NOT_FOUND
  - [OK] `OTBM`: PASS
  - [OK] `Export`: PASS

### Check 9: Circular Import Detection
- Analyzed: 506, Cycles: 0

---

## Recommendations
- Resolve 903 missing references.
- Replace 15 CRITICAL legacy references (datetime.utcnow).
- Ensure all pipeline stages are importable.
- Review 382 orphan module(s).
- Address 45 WARNING-level legacy references.

---

## Certification

**Status:** DEPENDENCY CONSISTENCY NOT CERTIFIED

| Criterion | Actual | Target | Pass |
|---|---|---|---|
| Modules Loaded | 506/506 (100%) | 100% | [OK] |
| Missing References | 903 | 0 | [FAIL] |
| Broken Imports | 0 | 0 | [OK] |
| Circular Imports | 0 | 0 | [OK] |
| Critical Legacy | 15 | 0 | [FAIL] |
| Agent Graph | PASS | PASS | [OK] |
| UI Graph | PASS | PASS | [OK] |
| CLI Graph | PASS | PASS | [OK] |
| Pipeline | FAIL | PASS | [FAIL] |

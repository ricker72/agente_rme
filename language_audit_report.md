# Language & Nomenclature Audit Report

## Meta Information

- **Project**: Agente RME v1.0.0 GA
- **Audit Date**: 2026-06-10
- **Audit Type**: Language & Nomenclature Audit
- **Milestone**: HITO 26.3 - Safe Language Normalization

## Summary

- **Total Issues Found**: 2449
- **Critical Issues**: 3
- **Warning Issues**: 626
- **Info Issues**: 1820
- **Files Affected**: 444

- **Estimated Refactor Risk**: MEDIUM
- **Migration Required**: Yes

## Issue Classification Legend

| Risk Level | Description |
|------------|-------------|
| CRITICAL | Public identifiers, API names, serialized structures, export schemas |
| WARNING | Private variables, comments, logs |
| INFO | Documentation, examples, general text |

## Detected Issues

| # | File | Issue Type | Line | Current Value (truncated) | Risk Level | Unicode Blocks |
|---|------|------------|------|---------------------------|------------|----------------|
| 1 | ARCHITECTURE.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Architecture | INFO | Other_NonASCII |
| 2 | ARCHITECTURE.md | documentation_text | 8 | - **Observability** — every agent, exporter, and OTBM operation is logged. | INFO | Other_NonASCII |
| 3 | ARCHITECTURE.md | documentation_text | 9 | - **Recoverability** — pipeline failures do not corrupt output. | INFO | Other_NonASCII |
| 4 | ARCHITECTURE.md | documentation_text | 10 | - **Configurability** — hot-reloadable profiles for dev / production. | INFO | Other_NonASCII |
| 5 | ARCHITECTURE.md | documentation_text | 11 | - **Installability** — under five minutes on Windows, Linux, macOS. | INFO | Other_NonASCII |
| 6 | ARCHITECTURE.md | documentation_text | 16 | ┌─────────────────────────────────────────────────────────────┐ | INFO | Other_NonASCII |
| 7 | ARCHITECTURE.md | documentation_text | 17 | │                       rme.py (CLI)                          │ | INFO | Other_NonASCII |
| 8 | ARCHITECTURE.md | documentation_text | 18 | │   generate \| analyze \| critic \| health \| metrics \| …        │ | INFO | Other_NonASCII |
| 9 | ARCHITECTURE.md | documentation_text | 19 | └────────────────────────────┬────────────────────────────────┘ | INFO | Other_NonASCII |
| 10 | ARCHITECTURE.md | documentation_text | 20 | │ | INFO | Other_NonASCII |
| 11 | ARCHITECTURE.md | documentation_text | 21 | ┌────────────────────┼─────────────────────┐ | INFO | Other_NonASCII |
| 12 | ARCHITECTURE.md | documentation_text | 22 | │                    │                     │ | INFO | Other_NonASCII |
| 13 | ARCHITECTURE.md | documentation_text | 23 | ▼                    ▼                     ▼ | INFO | Other_NonASCII |
| 14 | ARCHITECTURE.md | documentation_text | 26 | │                    │                     │ | INFO | Other_NonASCII |
| 15 | ARCHITECTURE.md | documentation_text | 27 | └──────────┬─────────┴─────────┬───────────┘ | INFO | Other_NonASCII |
| 16 | ARCHITECTURE.md | documentation_text | 28 | ▼                   ▼ | INFO | Other_NonASCII |
| 17 | ARCHITECTURE.md | documentation_text | 30 | │ | INFO | Other_NonASCII |
| 18 | ARCHITECTURE.md | documentation_text | 31 | ┌──────────┴───────────┐ | INFO | Other_NonASCII |
| 19 | ARCHITECTURE.md | documentation_text | 32 | ▼                      ▼ | INFO | Other_NonASCII |
| 20 | ARCHITECTURE.md | documentation_text | 35 | │                      │ | INFO | Other_NonASCII |
| 21 | ARCHITECTURE.md | documentation_text | 36 | └──────────┬───────────┘ | INFO | Other_NonASCII |
| 22 | ARCHITECTURE.md | documentation_text | 37 | ▼ | INFO | Other_NonASCII |
| 23 | ARCHITECTURE.md | documentation_text | 40 | │ | INFO | Other_NonASCII |
| 24 | ARCHITECTURE.md | documentation_text | 41 | ▼ | INFO | Other_NonASCII |
| 25 | ARCHITECTURE.md | documentation_text | 49 | config_manager.py  ───►  config/{default,development,production}.yaml | INFO | Other_NonASCII |
| 26 | ARCHITECTURE.md | documentation_text | 50 | core/observability/logger.py     ──► logs/agent_YYYYMMDD.log + events.jsonl | INFO | Other_NonASCII |
| 27 | ARCHITECTURE.md | documentation_text | 51 | core/observability/metrics.py    ──► metrics.json | INFO | Other_NonASCII |
| 28 | ARCHITECTURE.md | documentation_text | 52 | core/observability/health.py     ──► health_report.json | INFO | Other_NonASCII |
| 29 | ARCHITECTURE.md | documentation_text | 53 | core/observability/diagnostics.py──► diagnostics.json | INFO | Other_NonASCII |
| 30 | ARCHITECTURE.md | documentation_text | 54 | core/recovery.py                 ──► recovery_report.json, .backups/, .checkpoint/ | INFO | Other_NonASCII |
| 31 | ARCHITECTURE.md | documentation_text | 94 | - **Thread safety** — `ConfigManager`, `MetricsCollector`, `RecoveryManager`, and `ObservabilityLogger` use internal locks. | INFO | Other_NonASCII |
| 32 | ARCHITECTURE.md | documentation_text | 95 | - **Determinism** — the generator is seeded; the benchmark uses deterministic seeds. | INFO | Other_NonASCII |
| 33 | ARCHITECTURE.md | documentation_text | 96 | - **Atomicity** — exports go through a temp file + `os.replace()` to avoid partial writes. | INFO | Other_NonASCII |
| 34 | ARCHITECTURE.md | documentation_text | 97 | - **Backups** — any existing target is moved to `.backups/<name>.<ts>.bak` before overwrite. | INFO | Other_NonASCII |
| 35 | audit_report.md | documentation_text | 1 | # AUDITORÍA DE EJECUCIÓN COMPLETA - agente_rme | INFO | Latin_Extended |
| 36 | audit_report.md | documentation_text | 12 | \| Métrica \| Valor \| | INFO | Latin_Extended |
| 37 | audit_report.md | documentation_text | 19 | \| Pipeline E2E \| ✅ **FUNCIONAL** \| | INFO | Other_NonASCII |
| 38 | audit_report.md | documentation_text | 20 | \| Estado General \| ✅ **100% VERDE** \| | INFO | Other_NonASCII |
| 39 | audit_report.md | documentation_text | 22 | ⚠️ **NOTA:** El reporte anterior (06:48) reportaba 6 fallos legacy. **TODOS HAN SIDO CORREGIDOS.** Los 6 tests de `test_mvp_integration.py` ahora pasa | INFO | Other_NonASCII |
| 40 | audit_report.md | documentation_text | 31 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 41 | audit_report.md | documentation_text | 42 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 42 | audit_report.md | documentation_text | 53 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 43 | audit_report.md | documentation_text | 64 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 44 | audit_report.md | documentation_text | 75 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 45 | audit_report.md | documentation_text | 86 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 46 | audit_report.md | documentation_text | 97 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 47 | audit_report.md | documentation_text | 108 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 48 | audit_report.md | documentation_text | 119 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 49 | audit_report.md | documentation_text | 130 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 50 | audit_report.md | documentation_text | 141 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 51 | audit_report.md | documentation_text | 152 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 52 | audit_report.md | documentation_text | 163 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 53 | audit_report.md | documentation_text | 174 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 54 | audit_report.md | documentation_text | 185 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 55 | audit_report.md | documentation_text | 196 | \| **Estado** \| ✅ Funcional \| | INFO | Other_NonASCII |
| 56 | audit_report.md | documentation_text | 209 | Prompt → AI Architect → World Generator → Playtest → Balance → Campaign → Preview → Lua → OTBM → OTBM Importer → Analyzer → Evolution → OTBM Exporter | INFO | Other_NonASCII |
| 57 | audit_report.md | documentation_text | 214 | \| Parse Prompt \| ✅ \| core.prompt_interpreter.PromptInterpreter \| | INFO | Other_NonASCII |
| 58 | audit_report.md | documentation_text | 215 | \| Generate World \| ✅ \| core.world_engine.WorldGenerator \| | INFO | Other_NonASCII |
| 59 | audit_report.md | documentation_text | 216 | \| Expand World \| ✅ \| core.expansion.expansion_ai.ExpansionAI \| | INFO | Other_NonASCII |
| 60 | audit_report.md | documentation_text | 217 | \| Playtest \| ✅ \| core.playtest.playtest_engine.PlaytestEngine \| | INFO | Other_NonASCII |
| 61 | audit_report.md | documentation_text | 218 | \| Balance \| ✅ \| core.balance.balance_engine.BalanceEngine \| | INFO | Other_NonASCII |
| 62 | audit_report.md | documentation_text | 219 | \| Campaign \| ✅ \| core.campaign.campaign_generator.CampaignGenerator \| | INFO | Other_NonASCII |
| 63 | audit_report.md | documentation_text | 220 | \| Preview \| ✅ \| core.preview.preview_generator.PreviewGenerator \| | INFO | Other_NonASCII |
| 64 | audit_report.md | documentation_text | 221 | \| Lua Export \| ✅ \| core.lua.lua_generator.LuaGenerator \| | INFO | Other_NonASCII |
| 65 | audit_report.md | documentation_text | 222 | \| OTBM Export \| ✅ \| core.otbm.OTBMExporter \| | INFO | Other_NonASCII |
| 66 | audit_report.md | documentation_text | 223 | \| OTBM Import \| ✅ \| core.otbm.OTBMImporter \| | INFO | Other_NonASCII |
| 67 | audit_report.md | documentation_text | 224 | \| Map Analyzer \| ✅ \| core.analyzer.MapAnalyzer \| | INFO | Other_NonASCII |
| 68 | audit_report.md | documentation_text | 225 | \| Evolution \| ✅ \| core.evolution.EvolutionEngine \| | INFO | Other_NonASCII |
| 69 | audit_report.md | documentation_text | 226 | \| OTBM Re-Export \| ✅ \| core.otbm.OTBMExporter \| | INFO | Other_NonASCII |
| 70 | audit_report.md | documentation_text | 235 | Los 6 tests que fallaban en la auditoría previa han sido corregidos: | INFO | Latin_Extended |
| 71 | audit_report.md | documentation_text | 237 | \| # \| Test \| Estado Anterior \| Estado Actual \| Corrección \| | INFO | Latin_Extended |
| 72 | audit_report.md | documentation_text | 239 | \| 1 \| test_sprint1_hunt_generator \| ❌ Legacy API \| ✅ PASSED \| HuntGenerator actualizado \| | INFO | Other_NonASCII |
| 73 | audit_report.md | documentation_text | 240 | \| 2 \| test_sprint1_spawn_generator \| ❌ Legacy API \| ✅ PASSED \| HuntGenerator actualizado \| | INFO | Other_NonASCII |
| 74 | audit_report.md | documentation_text | 241 | \| 3 \| test_sprint1_lua_generator \| ❌ Legacy API \| ✅ PASSED \| HuntGenerator actualizado \| | INFO | Other_NonASCII |
| 75 | audit_report.md | documentation_text | 242 | \| 4 \| test_sprint1_preview_generator \| ❌ Legacy API \| ✅ PASSED \| HuntGenerator actualizado \| | INFO | Other_NonASCII |
| 76 | audit_report.md | documentation_text | 243 | \| 5 \| test_balance_modules \| ❌ analyze_zone() \| ✅ PASSED \| BalanceEngine corregido \| | INFO | Other_NonASCII |
| 77 | audit_report.md | documentation_text | 244 | \| 6 \| test_pipeline_cli \| ❌ returncode=1 \| ✅ PASSED \| Pipeline runner corregido \| | INFO | Other_NonASCII |
| 78 | audit_report.md | documentation_text | 248 | ## COBERTURA POR MÓDULOS CRÍTICOS (core/) | INFO | Latin_Extended |
| 79 | audit_report.md | documentation_text | 250 | \| Módulo \| Cobertura \| | INFO | Latin_Extended |
| 80 | audit_report.md | documentation_text | 285 | \| core/otbm → core/world \| ✅ \| | INFO | Other_NonASCII |
| 81 | audit_report.md | documentation_text | 286 | \| core/architect → core/world_planner \| ✅ \| | INFO | Other_NonASCII |
| 82 | audit_report.md | documentation_text | 287 | \| core/world_generator → core/biome_generator \| ✅ \| | INFO | Other_NonASCII |
| 83 | audit_report.md | documentation_text | 288 | \| core/pipeline → core/balance \| ✅ \| | INFO | Other_NonASCII |
| 84 | audit_report.md | documentation_text | 289 | \| core/pipeline → core/playtest \| ✅ \| | INFO | Other_NonASCII |
| 85 | audit_report.md | documentation_text | 290 | \| core/pipeline → core/campaign \| ✅ \| | INFO | Other_NonASCII |
| 86 | audit_report.md | documentation_text | 291 | \| core/pipeline → core/expansion \| ✅ \| | INFO | Other_NonASCII |
| 87 | audit_report.md | documentation_text | 297 | ## CONCLUSIÓN | INFO | Latin_Extended |
| 88 | audit_report.md | documentation_text | 299 | ### ✅ Estado: **100% FUNCIONAL** | INFO | Other_NonASCII |
| 89 | audit_report.md | documentation_text | 304 | \| Pipeline E2E \| ✅ Completo (13 etapas) \| | INFO | Other_NonASCII |
| 90 | audit_report.md | documentation_text | 305 | \| Hit 10-25 \| ✅ Todos funcionales \| | INFO | Other_NonASCII |
| 91 | audit_report.md | documentation_text | 306 | \| Dependencias \| ✅ Sin roturas \| | INFO | Other_NonASCII |
| 92 | audit_report.md | documentation_text | 307 | \| Tests legacy (6) \| ✅ Corregidos \| | INFO | Other_NonASCII |
| 93 | audit_report.md | documentation_text | 311 | ### Decisión sobre Hito 26 | INFO | Latin_Extended |
| 94 | audit_report.md | documentation_text | 313 | ✅ **NO HAY BLOQUEOS.** Todos los tests críticos están verdes. El pipeline completo se ejecuta sin errores. | INFO | Other_NonASCII, Latin_Extended |
| 95 | audit_report.md | documentation_text | 319 | *Reporte generado automáticamente - 2026-06-06 22:50* | INFO | Latin_Extended |
| 96 | benchmark_autonomous.py | other_non_ascii | 1 | ﻿"""Hito 30 â€” Autonomous World Designer benchmark. | INFO | Other_NonASCII, Latin_Extended |
| 97 | benchmark_autonomous.py | other_non_ascii | 144 | f"Î”={improvement:+.3f} ({result.total_duration_seconds:.2f}s)" | INFO | Other_NonASCII, Latin_Extended |
| 98 | benchmark_autonomous.py | other_non_ascii | 206 | parser = argparse.ArgumentParser(description="Hito 30 â€” Autonomous World Designer benchmark") | INFO | Other_NonASCII, Latin_Extended |
| 99 | benchmark_critic.py | print_string | 246 | print(f"\n=== Visual Map Critic AI — Benchmark ({len(MAP_BUILDERS)} maps) ===\n") | WARNING | Other_NonASCII |
| 100 | benchmark_critic.py | comment | 282 | except Exception as e:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 101 | benchmark_knowledge.py | other_non_ascii | 2 | HITO 28 — Knowledge benchmark. | INFO | Other_NonASCII |
| 102 | benchmark_output.txt | documentation_text | 2647 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 103 | benchmark_output.txt | documentation_text | 2678 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 104 | benchmark_output.txt | documentation_text | 2709 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 105 | benchmark_output.txt | documentation_text | 2740 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 106 | benchmark_output.txt | documentation_text | 2771 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 107 | benchmark_output2.txt | documentation_text | 2647 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 108 | benchmark_output2.txt | documentation_text | 2678 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 109 | benchmark_output2.txt | documentation_text | 2709 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 110 | benchmark_output2.txt | documentation_text | 2740 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 111 | benchmark_output2.txt | documentation_text | 2771 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 112 | benchmark_output3.txt | documentation_text | 2647 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 113 | benchmark_output3.txt | documentation_text | 2679 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 114 | benchmark_output3.txt | documentation_text | 2711 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 115 | benchmark_output3.txt | documentation_text | 2743 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 116 | benchmark_output3.txt | documentation_text | 2775 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 117 | benchmark_output4.txt | documentation_text | 2647 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 118 | benchmark_output4.txt | documentation_text | 2678 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 119 | benchmark_output4.txt | documentation_text | 2709 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 120 | benchmark_output4.txt | documentation_text | 2740 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 121 | benchmark_output4.txt | documentation_text | 2771 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 122 | CHANGELOG.md | documentation_text | 5 | ## [1.0.0] - 2026-06-08 — GENERAL AVAILABILITY | INFO | Other_NonASCII |
| 123 | CHANGELOG.md | documentation_text | 11 | - `logger.py` — structured JSON event logger. | INFO | Other_NonASCII |
| 124 | CHANGELOG.md | documentation_text | 12 | - `metrics.py` — thread-safe `MetricsCollector` exporting `metrics.json`. | INFO | Other_NonASCII |
| 125 | CHANGELOG.md | documentation_text | 13 | - `health.py` — `HealthChecker` with 11 system checks → `health_report.json`. | INFO | Other_NonASCII |
| 126 | CHANGELOG.md | documentation_text | 14 | - `diagnostics.py` — on-demand `Diagnostics` → `diagnostics.json`. | INFO | Other_NonASCII |
| 127 | CHANGELOG.md | documentation_text | 23 | - **Production benchmark**: `ga_benchmark.py` — 500 worlds, deterministic, exports `ga_benchmark.json`. | INFO | Other_NonASCII |
| 128 | CHANGELOG.md | documentation_text | 27 | - **Quality gate script** (`_quality_report.py`) — runs ruff / flake8 / mypy / bandit + heuristic scans and exports `quality_report.json`. | INFO | Other_NonASCII |
| 129 | CHANGELOG.md | documentation_text | 28 | - **GA certifier** (`ga_certify.py`) — produces `GA_CERTIFICATION.json`, `GA_METRICS.json`, and `GA_REPORT.md`. | INFO | Other_NonASCII |
| 130 | check_utcnow.py | other_non_ascii | 2 | check_utcnow.py — Pre-commit / CI lint rule | INFO | Other_NonASCII |
| 131 | check_utcnow.py | other_non_ascii | 8 | 0 — no violations found | INFO | Other_NonASCII |
| 132 | check_utcnow.py | other_non_ascii | 9 | 1 — violations found | INFO | Other_NonASCII |
| 133 | cli.py | other_non_ascii | 2 | cli.py — Command Line Interface for RME Map AI Agent v2.0 | INFO | Other_NonASCII |
| 134 | cli.py | print_string | 29 | print("  RME Map AI Agent v2.0 — Production Release") | WARNING | Other_NonASCII |
| 135 | cli.py | comment | 34 | # ── generate ───────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 136 | cli.py | print_string | 89 | print(f"  Lua validation: FAILED — {vresult.errors}") | WARNING | Other_NonASCII |
| 137 | cli.py | print_string | 96 | print(f"  OTBM: {otbm_path} — {report.get('status', 'unknown')}") | WARNING | Other_NonASCII |
| 138 | cli.py | comment | 167 | # ── export ─────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 139 | cli.py | comment | 213 | # ── import ─────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 140 | cli.py | comment | 253 | # ── preview ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 141 | cli.py | comment | 282 | # ── validate ───────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 142 | cli.py | comment | 308 | # ── info ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 143 | cli.py | comment | 357 | # ── knowledge ───────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 144 | cli.py | comment | 537 | # ── Main ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 145 | cli.py | other_non_ascii | 542 | description="RME Map AI Agent v2.0 — AI-powered Tibia map generator", | INFO | Other_NonASCII |
| 146 | cli.py | comment | 746 | # ── blueprint ──────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 147 | cli.py | comment | 917 | # ── autonomous ──────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 148 | config_manager.py | comment | 56 | # ── Internal XML helpers ──────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 149 | config_manager.py | comment | 80 | # ── Validation helpers ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 150 | config_manager.py | other_non_ascii | 90 | return False, "La ruta del cliente Tibia está vacía." | INFO | Latin_Extended |
| 151 | config_manager.py | other_non_ascii | 95 | return False, f"No se encontró appearances.dat ni archivos .otb en: {path}" | INFO | Latin_Extended |
| 152 | config_manager.py | other_non_ascii | 96 | return True, f"Directorio válido ({len(candidates)} archivo(s) de datos encontrado(s))." | INFO | Latin_Extended |
| 153 | config_manager.py | other_non_ascii | 99 | return True, f"Archivo válido: {p.name}" | INFO | Latin_Extended |
| 154 | config_manager.py | other_non_ascii | 106 | return False, "La ruta de items.xml está vacía." | INFO | Latin_Extended |
| 155 | config_manager.py | other_non_ascii | 109 | return False, f"No se encontró el archivo: {path}" | INFO | Latin_Extended |
| 156 | config_manager.py | other_non_ascii | 111 | return False, "El archivo no tiene extensión .xml" | INFO | Latin_Extended |
| 157 | config_manager.py | other_non_ascii | 125 | return False, "El archivo XML no contiene ningún elemento <item id='...'>" | INFO | Latin_Extended |
| 158 | config_manager.py | other_non_ascii | 130 | f"XML válido [{backend}]: {len(items)} items encontrados ({len(named)} con nombre).", | INFO | Latin_Extended |
| 159 | config_manager.py | other_non_ascii | 157 | f"El archivo {path.name} no contiene ningún elemento <{tag} name='...'> ni <{tag}>", | INFO | Latin_Extended |
| 160 | config_manager.py | other_non_ascii | 159 | return True, f"Archivo válido: {len(nodes)} <{tag}> encontrados en {path.name}." | INFO | Latin_Extended |
| 161 | config_manager.py | other_non_ascii | 166 | return False, "La carpeta de monstruos está vacía." | INFO | Latin_Extended |
| 162 | config_manager.py | other_non_ascii | 170 | return False, "El archivo de monstruos no tiene extensión .xml" | INFO | Latin_Extended |
| 163 | config_manager.py | other_non_ascii | 173 | return False, f"No es una carpeta válida: {path}" | INFO | Latin_Extended |
| 164 | config_manager.py | other_non_ascii | 192 | "No se encontraron archivos XML con estructura <monster name='...'> ni un monster.xml válido.", | INFO | Latin_Extended |
| 165 | config_manager.py | other_non_ascii | 196 | f"Carpeta válida: {len(xml_files)} XML encontrados, {len(monster_files)} con estructura de monstruo.", | INFO | Latin_Extended |
| 166 | config_manager.py | other_non_ascii | 202 | return False, "La carpeta de NPCs está vacía." | INFO | Latin_Extended |
| 167 | config_manager.py | other_non_ascii | 206 | return False, "El archivo de NPCs no tiene extensión .xml" | INFO | Latin_Extended |
| 168 | config_manager.py | other_non_ascii | 209 | return False, f"No es una carpeta válida: {path}" | INFO | Latin_Extended |
| 169 | config_manager.py | other_non_ascii | 218 | return True, f"Carpeta válida: {len(xml_files)} archivo(s) XML encontrado(s)." | INFO | Latin_Extended |
| 170 | config_manager.py | other_non_ascii | 224 | return True, "Opcional — omitido." | INFO | Other_NonASCII |
| 171 | config_manager.py | other_non_ascii | 227 | return False, f"No es una carpeta válida: {path}" | INFO | Latin_Extended |
| 172 | config_manager.py | other_non_ascii | 229 | return True, f"Carpeta válida: {len(xml_files)} archivo(s) encontrado(s)." | INFO | Latin_Extended |
| 173 | DEVELOPER_GUIDE.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Developer Guide | INFO | Other_NonASCII |
| 174 | DEVELOPER_GUIDE.md | documentation_text | 9 | ├── core/ | INFO | Other_NonASCII |
| 175 | DEVELOPER_GUIDE.md | documentation_text | 10 | │   ├── observability/   # logger, metrics, health, diagnostics | INFO | Other_NonASCII |
| 176 | DEVELOPER_GUIDE.md | documentation_text | 11 | │   ├── recovery.py | INFO | Other_NonASCII |
| 177 | DEVELOPER_GUIDE.md | documentation_text | 12 | │   ├── config_manager.py | INFO | Other_NonASCII |
| 178 | DEVELOPER_GUIDE.md | documentation_text | 13 | │   ├── generators/ | INFO | Other_NonASCII |
| 179 | DEVELOPER_GUIDE.md | documentation_text | 14 | │   ├── exporters/       # Lua exporter + validator | INFO | Other_NonASCII |
| 180 | DEVELOPER_GUIDE.md | documentation_text | 15 | │   ├── otbm/            # OTBM read/write/validate | INFO | Other_NonASCII |
| 181 | DEVELOPER_GUIDE.md | documentation_text | 16 | │   ├── preview/         # PNG preview generator | INFO | Other_NonASCII |
| 182 | DEVELOPER_GUIDE.md | documentation_text | 17 | │   ├── knowledge/       # RAG layer | INFO | Other_NonASCII |
| 183 | DEVELOPER_GUIDE.md | documentation_text | 18 | │   ├── critic/ | INFO | Other_NonASCII |
| 184 | DEVELOPER_GUIDE.md | documentation_text | 19 | │   ├── blueprint_intelligence/ | INFO | Other_NonASCII |
| 185 | DEVELOPER_GUIDE.md | documentation_text | 20 | │   ├── autonomous/      # Autonomous World Designer | INFO | Other_NonASCII |
| 186 | DEVELOPER_GUIDE.md | documentation_text | 21 | │   ├── agents/          # multi-agent orchestrator | INFO | Other_NonASCII |
| 187 | DEVELOPER_GUIDE.md | documentation_text | 22 | │   └── ... | INFO | Other_NonASCII |
| 188 | DEVELOPER_GUIDE.md | documentation_text | 23 | ├── tests/ | INFO | Other_NonASCII |
| 189 | DEVELOPER_GUIDE.md | documentation_text | 24 | ├── installer/ | INFO | Other_NonASCII |
| 190 | DEVELOPER_GUIDE.md | documentation_text | 25 | ├── config/ | INFO | Other_NonASCII |
| 191 | DEVELOPER_GUIDE.md | documentation_text | 26 | ├── docs/ | INFO | Other_NonASCII |
| 192 | DEVELOPER_GUIDE.md | documentation_text | 27 | ├── rme.py               # v1.0.0 GA entry point | INFO | Other_NonASCII |
| 193 | DEVELOPER_GUIDE.md | documentation_text | 28 | ├── cli.py               # legacy CLI | INFO | Other_NonASCII |
| 194 | DEVELOPER_GUIDE.md | documentation_text | 29 | └── ga_benchmark.py | INFO | Other_NonASCII |
| 195 | fix_utcnow.py | comment | 6 | # (file_path, original_import_block, replacement_import_block) — only modify the | WARNING | Other_NonASCII |
| 196 | fix_utcnow.py | comment | 9 | # agent_result.py — uses `from datetime import datetime` | WARNING | Other_NonASCII |
| 197 | fix_utcnow.py | comment | 15 | # agent_response.py — uses `import datetime` and `datetime.datetime.utcnow()` | WARNING | Other_NonASCII |
| 198 | fix_utcnow.py | comment | 21 | # agent_task.py — uses `from datetime import datetime` | WARNING | Other_NonASCII |
| 199 | fix_utcnow.py | comment | 27 | # workflow_state.py — uses `from datetime import datetime` | WARNING | Other_NonASCII |
| 200 | fix_utcnow.py | comment | 33 | # orchestrator_agent.py — uses `import datetime` and `datetime.datetime.utcnow()` | WARNING | Other_NonASCII |
| 201 | fix_utcnow.py | comment | 39 | # report_generator.py — uses `from datetime import datetime` | WARNING | Other_NonASCII |
| 202 | ga_benchmark.py | other_non_ascii | 2 | ga_benchmark.py — Agente RME v1.0.0 GA production benchmark. | INFO | Other_NonASCII |
| 203 | ga_certify.py | docstring | 1 | """ga_certify.py — Generate GA certification files for Agente RME v1.0.0 GA.""" | WARNING | Other_NonASCII |
| 204 | ga_certify.py | comment | 116 | "# Agente RME v1.0.0 GA — Certification Report", | WARNING | Other_NonASCII |
| 205 | ga_certify.py | other_non_ascii | 119 | f"**Status:** {'✅ PASS — GENERAL AVAILABILITY' if overall else '❌ FAIL'}  ", | INFO | Other_NonASCII |
| 206 | ga_certify.py | other_non_ascii | 131 | lines.append(f"\| {k} \| {'✅' if v else '❌'} \|") | INFO | Other_NonASCII |
| 207 | ga_certify.py | other_non_ascii | 139 | f"- Success rate: **{bm.get('success_rate', 0) * 100:.2f}%** (target ≥ 99%)", | INFO | Other_NonASCII |
| 208 | GA_RELEASE_NOTES.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Release Notes | INFO | Other_NonASCII |
| 209 | GA_RELEASE_NOTES.md | documentation_text | 4 | > **Status:** GENERAL AVAILABILITY — PRODUCTION READY — SUPPORTED RELEASE | INFO | Other_NonASCII |
| 210 | GA_RELEASE_NOTES.md | documentation_text | 11 | - **Hardened release** — warnings, dead code, and legacy imports cleaned up; 0 critical errors in `quality_report.json`. | INFO | Other_NonASCII |
| 211 | GA_RELEASE_NOTES.md | documentation_text | 12 | - **Cross-platform installers** — Windows (PowerShell), Linux (bash), macOS (bash). Each installs in **under 5 minutes**. | INFO | Other_NonASCII |
| 212 | GA_RELEASE_NOTES.md | documentation_text | 13 | - **Configuration management** — `ConfigManager` with hot-reload, validation, and three profiles (`default`, `development`, `production`). | INFO | Other_NonASCII |
| 213 | GA_RELEASE_NOTES.md | documentation_text | 14 | - **Observability layer** — `core/observability/` provides logger, metrics, health, and diagnostics. Every command exports a JSON snapshot. | INFO | Other_NonASCII |
| 214 | GA_RELEASE_NOTES.md | documentation_text | 15 | - **Health checks** — 11 system-wide checks (`rme health`) producing `health_report.json`. Exit code 0 = healthy. | INFO | Other_NonASCII |
| 215 | GA_RELEASE_NOTES.md | documentation_text | 16 | - **Crash recovery** — `RecoveryManager` checkpoints, atomically writes outputs, and supports rollback. Exports `recovery_report.json`. | INFO | Other_NonASCII |
| 216 | GA_RELEASE_NOTES.md | documentation_text | 17 | - **Production benchmark** — 500 worlds in ~2.2 seconds on a fast machine, **100% success rate**, 227+ worlds/s. | INFO | Other_NonASCII |
| 217 | GA_RELEASE_NOTES.md | documentation_text | 18 | - **CLI production mode** — `--verbose`, `--json`, `--profile` global flags; new commands: `health`, `metrics`, `analyze`, `critic`, `diagnose`, `benc | INFO | Other_NonASCII |
| 218 | GA_RELEASE_NOTES.md | documentation_text | 19 | - **Full documentation** — `README.md`, `INSTALL.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`,  | INFO | Other_NonASCII |
| 219 | GA_RELEASE_NOTES.md | documentation_text | 55 | 2. Re-run the installer for your platform (idempotent — it will not overwrite your `config.json`). | INFO | Other_NonASCII |
| 220 | GA_REPORT.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Certification Report | INFO | Other_NonASCII |
| 221 | GA_REPORT.md | documentation_text | 4 | **Status:** ✅ PASS — GENERAL AVAILABILITY | INFO | Other_NonASCII |
| 222 | GA_REPORT.md | documentation_text | 14 | \| all_tests_pass \| ✅ \| | INFO | Other_NonASCII |
| 223 | GA_REPORT.md | documentation_text | 15 | \| coverage_maintained \| ✅ \| | INFO | Other_NonASCII |
| 224 | GA_REPORT.md | documentation_text | 16 | \| no_crashes \| ✅ \| | INFO | Other_NonASCII |
| 225 | GA_REPORT.md | documentation_text | 17 | \| no_otbm_corruption \| ✅ \| | INFO | Other_NonASCII |
| 226 | GA_REPORT.md | documentation_text | 18 | \| cli_stable \| ✅ \| | INFO | Other_NonASCII |
| 227 | GA_REPORT.md | documentation_text | 19 | \| installer_functional \| ✅ \| | INFO | Other_NonASCII |
| 228 | GA_REPORT.md | documentation_text | 20 | \| health_checks_pass \| ✅ \| | INFO | Other_NonASCII |
| 229 | GA_REPORT.md | documentation_text | 21 | \| recovery_pass \| ✅ \| | INFO | Other_NonASCII |
| 230 | GA_REPORT.md | documentation_text | 22 | \| observability_pass \| ✅ \| | INFO | Other_NonASCII |
| 231 | GA_REPORT.md | documentation_text | 28 | - Success rate: **100.00%** (target ≥ 99%) | INFO | Other_NonASCII |
| 232 | hito26_1_benchmark.py | other_non_ascii | 8 | Prompt: "Crear expansión Issavi + Roshamuul para niveles 300-500 | INFO | Latin_Extended |
| 233 | hito26_1_benchmark.py | other_non_ascii | 35 | PROMPT = """Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 234 | hito26_1_report.md | documentation_text | 1 | # HITO 26.1 — STABILIZATION RELEASE REPORT | INFO | Other_NonASCII |
| 235 | hito26_1_report.md | documentation_text | 3 | **Status:** ✅ **CERTIFIED** | INFO | Other_NonASCII |
| 236 | hito26_1_report.md | documentation_text | 17 | \| OTBM Export fixed \| byte-range bug fixed \| yes — no `struct.error` raised \| ✅ \| | INFO | Other_NonASCII |
| 237 | hito26_1_report.md | documentation_text | 18 | \| OTBM Roundtrip \| export → import → re-export \| yes — works without exceptions \| ✅ \| | INFO | Other_NonASCII |
| 238 | hito26_1_report.md | documentation_text | 19 | \| Lua Export \| both signatures supported \| yes — `generate(world)` and `generate(world, spawn_plan)` \| ✅ \| | INFO | Other_NonASCII |
| 239 | hito26_1_report.md | documentation_text | 20 | \| Agent coverage \| all agents ≥ 80 % \| yes — 81 – 96 % \| ✅ \| | INFO | Other_NonASCII |
| 240 | hito26_1_report.md | documentation_text | 21 | \| Core coverage \| core ≥ 75 % \| yes — 76 % (combined) \| ✅ \| | INFO | Other_NonASCII |
| 241 | hito26_1_report.md | documentation_text | 22 | \| Global coverage \| global ≥ 70 % \| yes — 76 % \| ✅ \| | INFO | Other_NonASCII |
| 242 | hito26_1_report.md | documentation_text | 23 | \| `datetime.utcnow()` removed \| replaced with `datetime.now(timezone.utc)` \| yes — 6 files fixed, 0 remaining \| ✅ \| | INFO | Other_NonASCII |
| 243 | hito26_1_report.md | documentation_text | 24 | \| `campaign.json` always emitted \| never empty \| yes — written every benchmark run \| ✅ \| | INFO | Other_NonASCII |
| 244 | hito26_1_report.md | documentation_text | 25 | \| 5/5 benchmarks successful \| consecutive runs \| yes — 5/5 with all required files \| ✅ \| | INFO | Other_NonASCII |
| 245 | hito26_1_report.md | documentation_text | 26 | \| 0 critical errors \| no unhandled exceptions \| yes — 0 errors in the certification suite \| ✅ \| | INFO | Other_NonASCII |
| 246 | hito26_1_report.md | documentation_text | 30 | ## 1. PRIORITY 1 — OTBM Byte-Range Bug Fix | INFO | Other_NonASCII |
| 247 | hito26_1_report.md | documentation_text | 46 | * `core/otbm/node_encoder.py` — packed raw `int` arguments without | INFO | Other_NonASCII |
| 248 | hito26_1_report.md | documentation_text | 47 | bounds checking (e.g. `tile_flags=0xFFFFFFFF` overflows uint32 → raises). | INFO | Other_NonASCII |
| 249 | hito26_1_report.md | documentation_text | 48 | * `core/otbm/tile_encoder.py` — `offset_x = tile.x - base_x` could be | INFO | Other_NonASCII |
| 250 | hito26_1_report.md | documentation_text | 50 | * `core/otbm/otbm_serializer.py` — `radius=999`, `z=999`, | INFO | Other_NonASCII |
| 251 | hito26_1_report.md | documentation_text | 55 | A new module — **`core/otbm/binary_writer.py`** — centralises every | INFO | Other_NonASCII |
| 252 | hito26_1_report.md | documentation_text | 80 | * `tests/otbm/test_otbm_byte_ranges.py` — 31 tests covering the writer | INFO | Other_NonASCII |
| 253 | hito26_1_report.md | documentation_text | 82 | * `tests/otbm/test_otbm_large_world.py` — 14 tests covering 100×100 | INFO | Other_NonASCII, Latin_Extended |
| 254 | hito26_1_report.md | documentation_text | 84 | * `tests/otbm/test_otbm_export_validation.py` — 9 tests covering the | INFO | Other_NonASCII |
| 255 | hito26_1_report.md | documentation_text | 85 | full export → import → re-export pipeline. | INFO | Other_NonASCII |
| 256 | hito26_1_report.md | documentation_text | 94 | ## 2. PRIORITY 2 — Lua `spawn_plan` Compatibility Fix | INFO | Other_NonASCII |
| 257 | hito26_1_report.md | documentation_text | 103 | `generate(self, hunt_area, spawn_plan, map_name)` — both arguments were | INFO | Other_NonASCII |
| 258 | hito26_1_report.md | documentation_text | 132 | * `generate(world)` — only the world model. | INFO | Other_NonASCII |
| 259 | hito26_1_report.md | documentation_text | 133 | * `generate(world, spawn_plan)` — both. | INFO | Other_NonASCII |
| 260 | hito26_1_report.md | documentation_text | 134 | * `generate(hunt_area=..., spawn_plan=...)` — keyword form. | INFO | Other_NonASCII |
| 261 | hito26_1_report.md | documentation_text | 135 | * `generate(spawn_plan)` — when only the plan is available. | INFO | Other_NonASCII |
| 262 | hito26_1_report.md | documentation_text | 136 | * `generate(None, spawn_plan)` — explicit `None` for the world. | INFO | Other_NonASCII |
| 263 | hito26_1_report.md | documentation_text | 137 | * `generate(dict_with_tiles)` — plain dict world-model. | INFO | Other_NonASCII |
| 264 | hito26_1_report.md | documentation_text | 138 | * `generate(spawn_plan_dict)` — plain dict spawn plan. | INFO | Other_NonASCII |
| 265 | hito26_1_report.md | documentation_text | 147 | * `tests/lua/test_lua_generator.py` — 24 tests for both signatures, | INFO | Other_NonASCII |
| 266 | hito26_1_report.md | documentation_text | 149 | * `tests/lua/test_spawn_plan_generation.py` — 13 tests for the spawn | INFO | Other_NonASCII |
| 267 | hito26_1_report.md | documentation_text | 151 | * `tests/lua/test_lua_export_pipeline.py` — 6 tests for the full | INFO | Other_NonASCII |
| 268 | hito26_1_report.md | documentation_text | 161 | ## 3. PRIORITY 3 — Agent Coverage ≥ 80 % | INFO | Other_NonASCII |
| 269 | hito26_1_report.md | documentation_text | 165 | \| Agent file \| Before \| After \| Δ \| | INFO | Other_NonASCII |
| 270 | hito26_1_report.md | documentation_text | 179 | * `tests/agents/test_architect_agent_coverage.py` — 22 tests covering | INFO | Other_NonASCII |
| 271 | hito26_1_report.md | documentation_text | 182 | * `tests/agents/test_mapper_agent_coverage.py` — 17 tests covering | INFO | Other_NonASCII |
| 272 | hito26_1_report.md | documentation_text | 183 | list/dict tile normalisation, fallback paths, world → dict | INFO | Other_NonASCII |
| 273 | hito26_1_report.md | documentation_text | 185 | * `tests/agents/test_expansion_agent_coverage.py` — 13 tests covering | INFO | Other_NonASCII |
| 274 | hito26_1_report.md | documentation_text | 187 | * `tests/agents/test_quest_agent_coverage.py` — 22 tests covering | INFO | Other_NonASCII |
| 275 | hito26_1_report.md | documentation_text | 190 | * `tests/agents/test_balance_agent_coverage.py` — 14 tests covering | INFO | Other_NonASCII |
| 276 | hito26_1_report.md | documentation_text | 192 | * `tests/agents/test_qa_agent_coverage.py` — 23 tests covering the | INFO | Other_NonASCII |
| 277 | hito26_1_report.md | documentation_text | 201 | All 9 agents are now ≥ 80 % covered. Per-file detail: | INFO | Other_NonASCII |
| 278 | hito26_1_report.md | documentation_text | 217 | ## 4. PRIORITY 4 — Replace `datetime.utcnow()` | INFO | Other_NonASCII |
| 279 | hito26_1_report.md | documentation_text | 250 | `datetime.utcnow()` → `datetime.now(timezone.utc)` | INFO | Other_NonASCII |
| 280 | hito26_1_report.md | documentation_text | 251 | `datetime.datetime.utcnow()` → `datetime.datetime.now(datetime.timezone.utc)` | INFO | Other_NonASCII |
| 281 | hito26_1_report.md | documentation_text | 258 | `tests/common/test_datetime_timezone.py` — 7 tests: | INFO | Other_NonASCII |
| 282 | hito26_1_report.md | documentation_text | 277 | ## 5. PRIORITY 5 — `campaign.json` Always Emitted | INFO | Other_NonASCII |
| 283 | hito26_1_report.md | documentation_text | 309 | `tests/campaign/test_campaign_export.py` — 19 tests covering | INFO | Other_NonASCII |
| 284 | hito26_1_report.md | documentation_text | 326 | Crear expansión Issavi + Roshamuul | INFO | Latin_Extended |
| 285 | hito26_1_report.md | documentation_text | 363 | * `generated.otbm` — full OpenTibia binary map. | INFO | Other_NonASCII |
| 286 | hito26_1_report.md | documentation_text | 364 | * `generated.lua` — RME-compatible Lua script with spawns, monsters, items. | INFO | Other_NonASCII |
| 287 | hito26_1_report.md | documentation_text | 365 | * `campaign.json` — full campaign (theme, lore, factions, NPCs, story, raids, bosses). | INFO | Other_NonASCII |
| 288 | hito26_1_report.md | documentation_text | 366 | * `playtest_report.json` — combat simulation, XP/h, loot/h, survival. | INFO | Other_NonASCII |
| 289 | hito26_1_report.md | documentation_text | 367 | * `qa_report.json` — overall QA verdict with category breakdowns. | INFO | Other_NonASCII |
| 290 | hito26_1_report.md | documentation_text | 368 | * `agent_metrics.json` — per-agent execution time + success rate. | INFO | Other_NonASCII |
| 291 | hito26_1_report.md | documentation_text | 369 | * `preview.png`, `preview.json`, `preview_minimap.png` — preview output. | INFO | Other_NonASCII |
| 292 | hito26_1_report.md | documentation_text | 370 | * `multi_agent_result.json` — consolidated `MultiAgentResult`. | INFO | Other_NonASCII |
| 293 | hito26_1_report.md | documentation_text | 371 | * `workflow_<id>.json` & `workflow_<id>.log` — full audit trail. | INFO | Other_NonASCII |
| 294 | hito26_1_report.md | documentation_text | 384 | * `tests/agents/` — 181 tests (orchestrator, context, registry, | INFO | Other_NonASCII |
| 295 | hito26_1_report.md | documentation_text | 387 | * `tests/otbm/` — 81 tests (byte ranges, large world, export | INFO | Other_NonASCII |
| 296 | hito26_1_report.md | documentation_text | 389 | * `tests/lua/` — 40 tests (generator, spawn plan, export pipeline). | INFO | Other_NonASCII |
| 297 | hito26_1_report.md | documentation_text | 390 | * `tests/common/` — 7 tests (datetime timezone). | INFO | Other_NonASCII |
| 298 | hito26_1_report.md | documentation_text | 391 | * `tests/campaign/` — 19 tests (campaign export). | INFO | Other_NonASCII |
| 299 | hito26_1_report.md | documentation_text | 394 | test that fails is unrelated to HITO 26.1 — it expects specific | INFO | Other_NonASCII |
| 300 | hito26_1_report.md | documentation_text | 415 | ### Agent coverage (target ≥ 80 %) | INFO | Other_NonASCII |
| 301 | hito26_1_report.md | documentation_text | 429 | ### Core coverage (target ≥ 75 %) | INFO | Other_NonASCII |
| 302 | hito26_1_report.md | documentation_text | 450 | * `core/otbm/binary_writer.py` — **NEW** — `BinaryWriter` class | INFO | Other_NonASCII |
| 303 | hito26_1_report.md | documentation_text | 452 | * `core/otbm/node_encoder.py` — refactored to use `BinaryWriter`. | INFO | Other_NonASCII |
| 304 | hito26_1_report.md | documentation_text | 453 | * `core/otbm/tile_encoder.py` — refactored to use `BinaryWriter` | INFO | Other_NonASCII |
| 305 | hito26_1_report.md | documentation_text | 455 | * `core/lua/lua_generator.py` — supports both call signatures. | INFO | Other_NonASCII |
| 306 | hito26_1_report.md | documentation_text | 456 | * `agente_rme/core/agents/orchestrator_agent.py` — threads | INFO | Other_NonASCII |
| 307 | hito26_1_report.md | documentation_text | 458 | * `agente_rme/core/agents/agent_context.py` — `to_dict()` now | INFO | Other_NonASCII |
| 308 | hito26_1_report.md | documentation_text | 460 | * `agente_rme/core/agents/agent_result.py` — `datetime.now(timezone.utc)`. | INFO | Other_NonASCII |
| 309 | hito26_1_report.md | documentation_text | 461 | * `agente_rme/core/agents/contracts/agent_response.py` — | INFO | Other_NonASCII |
| 310 | hito26_1_report.md | documentation_text | 463 | * `agente_rme/core/agents/contracts/agent_task.py` — | INFO | Other_NonASCII |
| 311 | hito26_1_report.md | documentation_text | 465 | * `agente_rme/core/agents/contracts/workflow_state.py` — | INFO | Other_NonASCII |
| 312 | hito26_1_report.md | documentation_text | 467 | * `agente_rme/core/playtest/report_generator.py` — | INFO | Other_NonASCII |
| 313 | hito26_1_report.md | documentation_text | 474 | `tests/common/__init__.py`, `tests/campaign/__init__.py` — test | INFO | Other_NonASCII |
| 314 | hito26_1_report.md | documentation_text | 476 | * `tests/otbm/test_otbm_byte_ranges.py` — 31 tests. | INFO | Other_NonASCII |
| 315 | hito26_1_report.md | documentation_text | 477 | * `tests/otbm/test_otbm_large_world.py` — 14 tests. | INFO | Other_NonASCII |
| 316 | hito26_1_report.md | documentation_text | 478 | * `tests/otbm/test_otbm_export_validation.py` — 9 tests. | INFO | Other_NonASCII |
| 317 | hito26_1_report.md | documentation_text | 479 | * `tests/lua/test_lua_generator.py` — 24 tests. | INFO | Other_NonASCII |
| 318 | hito26_1_report.md | documentation_text | 480 | * `tests/lua/test_spawn_plan_generation.py` — 13 tests. | INFO | Other_NonASCII |
| 319 | hito26_1_report.md | documentation_text | 481 | * `tests/lua/test_lua_export_pipeline.py` — 6 tests. | INFO | Other_NonASCII |
| 320 | hito26_1_report.md | documentation_text | 482 | * `tests/agents/test_architect_agent_coverage.py` — 22 tests. | INFO | Other_NonASCII |
| 321 | hito26_1_report.md | documentation_text | 483 | * `tests/agents/test_mapper_agent_coverage.py` — 17 tests. | INFO | Other_NonASCII |
| 322 | hito26_1_report.md | documentation_text | 484 | * `tests/agents/test_expansion_agent_coverage.py` — 13 tests. | INFO | Other_NonASCII |
| 323 | hito26_1_report.md | documentation_text | 485 | * `tests/agents/test_quest_agent_coverage.py` — 22 tests. | INFO | Other_NonASCII |
| 324 | hito26_1_report.md | documentation_text | 486 | * `tests/agents/test_balance_agent_coverage.py` — 14 tests. | INFO | Other_NonASCII |
| 325 | hito26_1_report.md | documentation_text | 487 | * `tests/agents/test_qa_agent_coverage.py` — 23 tests. | INFO | Other_NonASCII |
| 326 | hito26_1_report.md | documentation_text | 488 | * `tests/common/test_datetime_timezone.py` — 7 tests. | INFO | Other_NonASCII |
| 327 | hito26_1_report.md | documentation_text | 489 | * `tests/campaign/test_campaign_export.py` — 19 tests. | INFO | Other_NonASCII |
| 328 | hito26_1_report.md | documentation_text | 493 | * `hito26_1_benchmark.py` — 5/5 benchmark runner. | INFO | Other_NonASCII |
| 329 | hito26_1_report.md | documentation_text | 494 | * `gen_coverage.py` — generates `coverage_report.json`. | INFO | Other_NonASCII |
| 330 | hito26_1_report.md | documentation_text | 495 | * `show_cov.py` — per-file coverage summary. | INFO | Other_NonASCII |
| 331 | hito26_1_report.md | documentation_text | 496 | * `coverage_report.json` — generated coverage report. | INFO | Other_NonASCII |
| 332 | hito26_1_report.md | documentation_text | 497 | * `coverage.json` — raw coverage.py output. | INFO | Other_NonASCII |
| 333 | hito26_1_report.md | documentation_text | 501 | * `hito26_1_report.md` — this document. | INFO | Other_NonASCII |
| 334 | hito26_1_report.md | documentation_text | 505 | ## 10. Criteria de Aprobación — Resumen Final | INFO | Other_NonASCII, Latin_Extended |
| 335 | hito26_1_report.md | documentation_text | 509 | \| ✓ OTBM Export funcionando \| ✅ \| | INFO | Other_NonASCII |
| 336 | hito26_1_report.md | documentation_text | 510 | \| ✓ OTBM Roundtrip funcionando \| ✅ \| | INFO | Other_NonASCII |
| 337 | hito26_1_report.md | documentation_text | 511 | \| ✓ Lua Export funcionando \| ✅ \| | INFO | Other_NonASCII |
| 338 | hito26_1_report.md | documentation_text | 512 | \| ✓ `campaign.json` generado \| ✅ \| | INFO | Other_NonASCII |
| 339 | hito26_1_report.md | documentation_text | 513 | \| ✓ Cobertura agentes ≥ 80 % \| ✅ (81 – 96 %) \| | INFO | Other_NonASCII |
| 340 | hito26_1_report.md | documentation_text | 514 | \| ✓ Cobertura core ≥ 75 % \| ✅ (76 %) \| | INFO | Other_NonASCII |
| 341 | hito26_1_report.md | documentation_text | 515 | \| ✓ Cobertura global ≥ 70 % \| ✅ (76 %) \| | INFO | Other_NonASCII |
| 342 | hito26_1_report.md | documentation_text | 516 | \| ✓ `datetime.utcnow()` eliminado \| ✅ (6 files fixed) \| | INFO | Other_NonASCII |
| 343 | hito26_1_report.md | documentation_text | 517 | \| ✓ 5/5 benchmarks exitosos \| ✅ \| | INFO | Other_NonASCII |
| 344 | hito26_1_report.md | documentation_text | 518 | \| ✓ 0 errores críticos \| ✅ \| | INFO | Other_NonASCII, Latin_Extended |
| 345 | hito26_1_report.md | documentation_text | 522 | ## 11. Definición de Done | INFO | Latin_Extended |
| 346 | hito26_1_report.md | documentation_text | 524 | **HITO 26.1 CERTIFICADO** — el sistema multiagente queda oficialmente | INFO | Other_NonASCII |
| 347 | hito26_1_report.md | documentation_text | 525 | estabilizado y listo para iniciar **HITO 27 — VISUAL MAP CRITIC AI**. | INFO | Other_NonASCII |
| 348 | hito26_1_report.md | documentation_text | 528 | las correcciones, los tests, el benchmark, y la documentación son | INFO | Latin_Extended |
| 349 | hito26_1_report.md | documentation_text | 529 | implementación funcional verificable. | INFO | Latin_Extended |
| 350 | hito26_certification.md | documentation_text | 1 | # HITO 26 — Certificación del Sistema Multiagente | INFO | Other_NonASCII, Latin_Extended |
| 351 | hito26_certification.md | documentation_text | 10 | Se validó el sistema multiagente completo con el pipeline de 8 agentes: | INFO | Latin_Extended |
| 352 | hito26_certification.md | documentation_text | 11 | OrchestratorAgent → ArchitectAgent → MapperAgent → ExpansionAgent → QuestAgent → PlaytestAgent → BalanceAgent → QAAgent → ExportAgent | INFO | Other_NonASCII |
| 353 | hito26_certification.md | documentation_text | 15 | ## 2. Fase 1 — Prueba E2E Real | INFO | Other_NonASCII |
| 354 | hito26_certification.md | documentation_text | 19 | Crear expansión Issavi + Roshamuul para niveles 300-500 con: | INFO | Latin_Extended |
| 355 | hito26_certification.md | documentation_text | 27 | - **Éxito:** ✅ SI (5/5 runs exitosos) | INFO | Other_NonASCII, Latin_Extended |
| 356 | hito26_certification.md | documentation_text | 30 | - **Tasa de éxito agentes:** 100% | INFO | Latin_Extended |
| 357 | hito26_certification.md | documentation_text | 35 | \| preview.png \| ✅ Generado \| 15,172 bytes \| | INFO | Other_NonASCII |
| 358 | hito26_certification.md | documentation_text | 36 | \| preview_minimap.png \| ✅ Generado \| 7,600 bytes \| | INFO | Other_NonASCII |
| 359 | hito26_certification.md | documentation_text | 37 | \| preview.json \| ✅ Generado \| 391 bytes \| | INFO | Other_NonASCII |
| 360 | hito26_certification.md | documentation_text | 38 | \| playtest_report.json \| ✅ Generado \| Válido \| | INFO | Other_NonASCII, Latin_Extended |
| 361 | hito26_certification.md | documentation_text | 39 | \| qa_report.json \| ✅ Generado \| Válido \| | INFO | Other_NonASCII, Latin_Extended |
| 362 | hito26_certification.md | documentation_text | 40 | \| report.json \| ✅ Generado \| Consolidado \| | INFO | Other_NonASCII |
| 363 | hito26_certification.md | documentation_text | 41 | \| generated.otbm \| ❌ Falló \| Error: 'B' format requires 0 <= number <= 255 \| | INFO | Other_NonASCII, Latin_Extended |
| 364 | hito26_certification.md | documentation_text | 42 | \| generated.lua \| ❌ Falló \| Error: falta argumento 'spawn_plan' \| | INFO | Other_NonASCII, Latin_Extended |
| 365 | hito26_certification.md | documentation_text | 43 | \| campaign.json \| ⚠️ No generado \| Balance agent falló \| | INFO | Other_NonASCII, Latin_Extended |
| 366 | hito26_certification.md | documentation_text | 44 | \| agent_metrics.json \| ✅ Generado \| Por run en output_benchmark/run_N \| | INFO | Other_NonASCII |
| 367 | hito26_certification.md | documentation_text | 48 | ## 3. Fase 2 — Benchmark (5 Ejecuciones Consecutivas) | INFO | Other_NonASCII |
| 368 | hito26_certification.md | documentation_text | 51 | \| Run \| Éxito \| Tiempo (s) \| Tiles \| Success Rate \| | INFO | Latin_Extended |
| 369 | hito26_certification.md | documentation_text | 53 | \| 1 \| ✅ \| 3.15 \| 10,517 \| 100% \| | INFO | Other_NonASCII |
| 370 | hito26_certification.md | documentation_text | 54 | \| 2 \| ✅ \| 2.16 \| 10,517 \| 100% \| | INFO | Other_NonASCII |
| 371 | hito26_certification.md | documentation_text | 55 | \| 3 \| ✅ \| 2.06 \| 10,517 \| 100% \| | INFO | Other_NonASCII |
| 372 | hito26_certification.md | documentation_text | 56 | \| 4 \| ✅ \| 2.08 \| 10,517 \| 100% \| | INFO | Other_NonASCII |
| 373 | hito26_certification.md | documentation_text | 57 | \| 5 \| ✅ \| 2.26 \| 10,517 \| 100% \| | INFO | Other_NonASCII |
| 374 | hito26_certification.md | documentation_text | 59 | ### Estadísticas | INFO | Latin_Extended |
| 375 | hito26_certification.md | documentation_text | 62 | - **Tiempo mínimo:** 2.06s | INFO | Latin_Extended |
| 376 | hito26_certification.md | documentation_text | 63 | - **Tiempo máximo:** 3.15s | INFO | Latin_Extended |
| 377 | hito26_certification.md | documentation_text | 64 | - **Diferentes workflow IDs:** 5 (cada run único) | INFO | Latin_Extended |
| 378 | hito26_certification.md | documentation_text | 65 | - **Consistencia tiles:** 10,517 (mismo valor, sin variación) | INFO | Latin_Extended |
| 379 | hito26_certification.md | documentation_text | 71 | 4. **Balance agent:** no generó campaign.json | INFO | Latin_Extended |
| 380 | hito26_certification.md | documentation_text | 75 | ## 4. Fase 3 — Validación de Métricas | INFO | Other_NonASCII, Latin_Extended |
| 381 | hito26_certification.md | documentation_text | 97 | - ✅ execution_time | INFO | Other_NonASCII |
| 382 | hito26_certification.md | documentation_text | 98 | - ✅ agent_times | INFO | Other_NonASCII |
| 383 | hito26_certification.md | documentation_text | 99 | - ✅ agent_success_rate | INFO | Other_NonASCII |
| 384 | hito26_certification.md | documentation_text | 100 | - ✅ agent_failures | INFO | Other_NonASCII |
| 385 | hito26_certification.md | documentation_text | 101 | - ⚠️ agent_execution_order (no explícito, pero implícito en pipeline) | INFO | Other_NonASCII, Latin_Extended |
| 386 | hito26_certification.md | documentation_text | 105 | ## 5. Fase 4 — Cobertura de Código | INFO | Other_NonASCII, Latin_Extended |
| 387 | hito26_certification.md | documentation_text | 116 | \| orchestrator_agent.py \| 91.0% \| ✅ PASS \| | INFO | Other_NonASCII |
| 388 | hito26_certification.md | documentation_text | 117 | \| architect_agent.py \| 64.8% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 389 | hito26_certification.md | documentation_text | 118 | \| mapper_agent.py \| 78.0% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 390 | hito26_certification.md | documentation_text | 119 | \| expansion_agent.py \| 79.0% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 391 | hito26_certification.md | documentation_text | 120 | \| quest_agent.py \| 63.6% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 392 | hito26_certification.md | documentation_text | 121 | \| playtest_agent.py \| 81.0% \| ✅ PASS \| | INFO | Other_NonASCII |
| 393 | hito26_certification.md | documentation_text | 122 | \| balance_agent.py \| 78.8% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 394 | hito26_certification.md | documentation_text | 123 | \| qa_agent.py \| 63.0% \| ❌ FAIL \| | INFO | Other_NonASCII |
| 395 | hito26_certification.md | documentation_text | 124 | \| export_agent.py \| 82.3% \| ✅ PASS \| | INFO | Other_NonASCII |
| 396 | hito26_certification.md | documentation_text | 131 | ## 6. Criterios de Aprobación | INFO | Latin_Extended |
| 397 | hito26_certification.md | documentation_text | 135 | \| E2E exitoso \| ✅ CUMPLE \| Pipeline completo ejecutado \| | INFO | Other_NonASCII |
| 398 | hito26_certification.md | documentation_text | 136 | \| 5/5 benchmarks exitosos \| ✅ CUMPLE \| Todos exitosos, sin crashes \| | INFO | Other_NonASCII |
| 399 | hito26_certification.md | documentation_text | 137 | \| Artefactos válidos \| ⚠️ PARCIAL \| OTBM y Lua fallaron por bugs conocidos \| | INFO | Other_NonASCII, Latin_Extended |
| 400 | hito26_certification.md | documentation_text | 138 | \| Métricas válidas \| ✅ CUMPLE \| agent_metrics.json válido \| | INFO | Other_NonASCII, Latin_Extended |
| 401 | hito26_certification.md | documentation_text | 139 | \| Cobertura >= 80% agentes \| ❌ NO CUMPLE \| Solo 3/9 agentes cumplen \| | INFO | Other_NonASCII |
| 402 | hito26_certification.md | documentation_text | 140 | \| Cero excepciones críticas \| ⚠️ PARCIAL \| Excepciones manejadas pero presentes \| | INFO | Other_NonASCII, Latin_Extended |
| 403 | hito26_certification.md | documentation_text | 146 | ### Críticos (bloquean generación completa) | INFO | Latin_Extended |
| 404 | hito26_certification.md | documentation_text | 153 | 5. **Deprecaciones:** datetime.utcnow() usado en múltiples módulos | INFO | Latin_Extended |
| 405 | hito26_certification.md | documentation_text | 157 | ## 8. Conclusión | INFO | Latin_Extended |
| 406 | hito26_certification.md | documentation_text | 160 | - ✅ Los 8 agentes se ejecutan en secuencia | INFO | Other_NonASCII |
| 407 | hito26_certification.md | documentation_text | 161 | - ✅ No hay crashes ni excepciones no manejadas | INFO | Other_NonASCII |
| 408 | hito26_certification.md | documentation_text | 162 | - ✅ Las métricas se generan correctamente | INFO | Other_NonASCII, Latin_Extended |
| 409 | hito26_certification.md | documentation_text | 163 | - ✅ El benchmark es estable y reproducible | INFO | Other_NonASCII |
| 410 | hito26_certification.md | documentation_text | 173 | ## 9. Autorización | INFO | Latin_Extended |
| 411 | hito26_certification.md | documentation_text | 177 | Se autoriza el inicio de **HITO 27 — Visual Map Critic AI** | INFO | Other_NonASCII |
| 412 | hito26_certification.md | documentation_text | 179 | Los bugs conocidos son menores y no impiden la validación del pipeline multiagente. La arquitectura está probada y funcional. | INFO | Latin_Extended |
| 413 | hito30_report.md | documentation_text | 1 | # HITO 30 — Autonomous World Designer | INFO | Other_NonASCII |
| 414 | hito30_report.md | documentation_text | 3 | ## Status: ✅ COMPLETE | INFO | Other_NonASCII |
| 415 | hito30_report.md | documentation_text | 14 | \| `autonomous_world_designer.py` \| Main façade — composes the full pipeline \| | INFO | Other_NonASCII, Latin_Extended |
| 416 | hito30_report.md | documentation_text | 18 | \| `autonomous_optimizer.py` \| Runs the iterative Generate → Critic → Evolve loop \| | INFO | Other_NonASCII |
| 417 | hito30_report.md | documentation_text | 35 | tests/autonomous/                           — 113 tests  (97 original + 16 new) | INFO | Other_NonASCII |
| 418 | hito30_report.md | documentation_text | 38 | tests/integration/test_autonomous_blueprint_int…    2 tests | INFO | Other_NonASCII |
| 419 | hito30_report.md | documentation_text | 39 | tests/integration/test_autonomous_knowledge_inte…   2 tests | INFO | Other_NonASCII |
| 420 | hito30_report.md | documentation_text | 47 | - `__init__.py` — 100% | INFO | Other_NonASCII |
| 421 | hito30_report.md | documentation_text | 48 | - `autonomous_decision_engine.py` — 92% | INFO | Other_NonASCII |
| 422 | hito30_report.md | documentation_text | 49 | - `autonomous_director.py` — 96% | INFO | Other_NonASCII |
| 423 | hito30_report.md | documentation_text | 50 | - `autonomous_optimizer.py` — 69% (only the real-engine branches that | INFO | Other_NonASCII |
| 424 | hito30_report.md | documentation_text | 53 | - `autonomous_planner.py` — 98% | INFO | Other_NonASCII |
| 425 | hito30_report.md | documentation_text | 54 | - `autonomous_visualizer.py` — 95% | INFO | Other_NonASCII |
| 426 | hito30_report.md | documentation_text | 55 | - `autonomous_world_designer.py` — 86% | INFO | Other_NonASCII |
| 427 | hito30_report.md | documentation_text | 56 | - `goal_manager.py` — 90% | INFO | Other_NonASCII |
| 428 | hito30_report.md | documentation_text | 57 | - `models/__init__.py` — 100% | INFO | Other_NonASCII |
| 429 | hito30_report.md | documentation_text | 58 | - `models/design_decision.py` — 77% | INFO | Other_NonASCII |
| 430 | hito30_report.md | documentation_text | 59 | - `models/design_goal.py` — 86% | INFO | Other_NonASCII |
| 431 | hito30_report.md | documentation_text | 60 | - `models/design_iteration.py` — 82% | INFO | Other_NonASCII |
| 432 | hito30_report.md | documentation_text | 61 | - `models/design_plan.py` — 87% | INFO | Other_NonASCII |
| 433 | hito30_report.md | documentation_text | 62 | - `models/design_result.py` — 63% | INFO | Other_NonASCII |
| 434 | hito30_report.md | documentation_text | 63 | - `models/region_plan.py` — 86% | INFO | Other_NonASCII |
| 435 | hito30_report.md | documentation_text | 64 | - `world_objective.py` — 96% | INFO | Other_NonASCII |
| 436 | hito30_report.md | documentation_text | 65 | - `world_strategy.py` — 98% | INFO | Other_NonASCII |
| 437 | hito30_report.md | documentation_text | 85 | `report` — already wired in `cli.py` and exercised in the integration | INFO | Other_NonASCII |
| 438 | hito30_report.md | documentation_text | 105 | \| 1 \| Issavi + Roshamuul nivel 300-500, 3 hunts 2 bosses 1 raid \| critic > 0 (real) ✅ \| | INFO | Other_NonASCII |
| 439 | hito30_report.md | documentation_text | 106 | \| 2 \| Compact desert city Issavi style \| city-focused plan, critic > 0 ✅ \| | INFO | Other_NonASCII |
| 440 | hito30_report.md | documentation_text | 107 | \| 3 \| Large endgame continent 3 cities 8 hunts 5 bosses 2 raids \| all 4 region types generated ✅ \| | INFO | Other_NonASCII |
| 441 | hito30_report.md | documentation_text | 108 | \| 4 \| Run 50 autonomous generations \| report, no exceptions ✅ \| | INFO | Other_NonASCII |
| 442 | HOTFIX_CLI_STABILITY.json | export_value | 138 | "stdout_tail": "===============\n  RME Map AI Agent v2.0 — Production Release\n  AI-powered Tibia map generator for RME\n============================= | WARNING | Other_NonASCII |
| 443 | HOTFIX_CLI_STABILITY.json | export_value | 222 | "stdout_tail": "============================================================\n  RME Map AI Agent v2.0 — Production Release\n  AI-powered Tibia map gen | WARNING | Other_NonASCII |
| 444 | HOTFIX_CLI_STABILITY.json | export_value | 235 | "stdout_tail": "========================================\n  RME Map AI Agent v2.0 — Production Release\n  AI-powered Tibia map generator for RME\n==== | WARNING | Other_NonASCII |
| 445 | INSTALL.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Installation Guide | INFO | Other_NonASCII |
| 446 | INSTALL.md | documentation_text | 15 | > Ollama is **optional** for v1.0.0 GA — the agent runs the full generation pipeline locally without it. Ollama is only used to enrich prompts when an | INFO | Other_NonASCII |
| 447 | INSTALL.md | documentation_text | 110 | - **Python not found** — install Python 3.10+ and ensure it is on `PATH`. | INFO | Other_NonASCII |
| 448 | INSTALL.md | documentation_text | 111 | - **`No module named yaml`** — `pip install -r requirements-lock.txt`. | INFO | Other_NonASCII |
| 449 | INSTALL.md | documentation_text | 112 | - **OTBM export is slow** — lower `generation.max_tiles` in `config/production.yaml`. | INFO | Other_NonASCII |
| 450 | INSTALL.md | documentation_text | 113 | - **Tests fail on Windows** — run from PowerShell, not `cmd.exe`. | INFO | Other_NonASCII |
| 451 | main.py | other_non_ascii | 3 | Agente IA de Diseño de Mapas para Remere's Map Editor | INFO | Latin_Extended |
| 452 | main.py | other_non_ascii | 4 | GUI built with customtkinter — dark industrial aesthetic. | INFO | Other_NonASCII |
| 453 | main.py | comment | 23 | # ── Theme ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 454 | main.py | comment | 53 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 455 | main.py | comment | 55 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 456 | main.py | other_non_ascii | 67 | self.title("RME Agent — Asistente de Configuración") | INFO | Other_NonASCII, Latin_Extended |
| 457 | main.py | other_non_ascii | 86 | text="⚙  CONFIGURACIÓN INICIAL", | INFO | Other_NonASCII, Latin_Extended |
| 458 | main.py | other_non_ascii | 119 | ("mounts_folder", "5. Carpeta de Monturas  (data/mounts/) — OPCIONAL", "carpeta", True), | INFO | Other_NonASCII |
| 459 | main.py | other_non_ascii | 136 | self.status_box.insert("end", "Estado: esperando validación...\n") | INFO | Latin_Extended |
| 460 | main.py | other_non_ascii | 253 | sl.configure(text=f"✓ {msg}", text_color=TEXT_GREEN) | INFO | Other_NonASCII |
| 461 | main.py | other_non_ascii | 256 | sl.configure(text=f"✗ {msg}", text_color=TEXT_RED) | INFO | Other_NonASCII |
| 462 | main.py | other_non_ascii | 265 | self._set_status("\n".join(log_lines) + "\n\n✓ Configuración guardada exitosamente.") | INFO | Other_NonASCII, Latin_Extended |
| 463 | main.py | other_non_ascii | 268 | self._set_status("\n".join(log_lines) + "\n\n✗ Corrige los errores antes de continuar.") | INFO | Other_NonASCII |
| 464 | main.py | other_non_ascii | 280 | "La configuración no está completa.\n¿Deseas cerrar la aplicación?", | INFO | Other_NonASCII, Latin_Extended |
| 465 | main.py | comment | 286 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 466 | main.py | comment | 288 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 467 | main.py | comment | 316 | # ── UI Construction ──────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 468 | main.py | other_non_ascii | 326 | text="▣  RME MAP AI AGENT", | INFO | Other_NonASCII |
| 469 | main.py | other_non_ascii | 341 | text="⚙ Reconfigurar", | INFO | Other_NonASCII |
| 470 | main.py | other_non_ascii | 370 | text="● Listo", | INFO | Other_NonASCII |
| 471 | main.py | other_non_ascii | 408 | text="↺", | INFO | Other_NonASCII |
| 472 | main.py | other_non_ascii | 427 | ctk.CTkLabel(card2, text="DESCRIPCIÓN DEL MAPA", font=FONT_SMALL, text_color=ACCENT).pack( | INFO | Latin_Extended |
| 473 | main.py | other_non_ascii | 445 | "Crea una mazmorra subterránea de 30x30 para nivel 100.\n" | INFO | Latin_Extended |
| 474 | main.py | other_non_ascii | 451 | ctk.CTkLabel(card2, text="Ejemplos rápidos:", font=FONT_SMALL, text_color=TEXT_DIM).pack( | INFO | Latin_Extended |
| 475 | main.py | other_non_ascii | 459 | "🐉 Mazmorra", | INFO | Other_NonASCII |
| 476 | main.py | other_non_ascii | 463 | "🌲 Bosque", | INFO | Other_NonASCII |
| 477 | main.py | other_non_ascii | 464 | "Genera un área boscosa de 40x40 con árboles, caminos de tierra y decoraciones naturales.", | INFO | Latin_Extended |
| 478 | main.py | other_non_ascii | 467 | "🏰 Castillo", | INFO | Other_NonASCII |
| 479 | main.py | other_non_ascii | 468 | "Diseña el interior de un castillo con sala del trono, paredes de ladrillo y puertas.", | INFO | Latin_Extended |
| 480 | main.py | other_non_ascii | 471 | "🌊 Puerto", | INFO | Other_NonASCII |
| 481 | main.py | other_non_ascii | 472 | "Crea un área portuaria con muelles de madera, agua y decoraciones marinas.", | INFO | Latin_Extended |
| 482 | main.py | other_non_ascii | 510 | text="▶  GENERAR SCRIPT LUA", | INFO | Other_NonASCII |
| 483 | main.py | other_non_ascii | 547 | text="💾 Guardar .lua", | INFO | Other_NonASCII |
| 484 | main.py | other_non_ascii | 561 | text="🗑 Limpiar", | INFO | Other_NonASCII |
| 485 | main.py | comment | 586 | # ── Data Loading ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 486 | main.py | other_non_ascii | 603 | f"✓ {total_items:,} items analizados\n" | INFO | Other_NonASCII |
| 487 | main.py | other_non_ascii | 604 | f"✓ {total_items:,} entradas indexadas\n" | INFO | Other_NonASCII |
| 488 | main.py | other_non_ascii | 605 | f"✓ RAG base construida para generación de mapas" | INFO | Other_NonASCII, Latin_Extended |
| 489 | main.py | other_non_ascii | 615 | text="⚠ items.xml no configurado. Reconfigura la app.", | INFO | Other_NonASCII |
| 490 | main.py | other_non_ascii | 635 | f"✓ Datos cargados — {len(self._monster_names)} monstruos, {len(self._npc_names)} NPCs" | INFO | Other_NonASCII |
| 491 | main.py | other_non_ascii | 643 | text=f"✗ Error al cargar datos:\n{msg}", text_color=TEXT_RED | INFO | Other_NonASCII |
| 492 | main.py | comment | 653 | # ── Model Management ─────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 493 | main.py | other_non_ascii | 657 | self.ollama_status.configure(text="⚠ Cargando RME Studio...", text_color=TEXT_RED) | INFO | Other_NonASCII |
| 494 | main.py | other_non_ascii | 663 | self.ollama_status.configure(text="● Ollama disponible", text_color=TEXT_GREEN) | INFO | Other_NonASCII |
| 495 | main.py | other_non_ascii | 671 | self.ollama_status.configure(text="✗ Ollama no disponible", text_color=TEXT_RED) | INFO | Other_NonASCII |
| 496 | main.py | comment | 675 | # ── Generation ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 497 | main.py | other_non_ascii | 683 | messagebox.showwarning("Prompt vacío", "Escribe una descripción del mapa.", parent=self) | INFO | Latin_Extended |
| 498 | main.py | other_non_ascii | 689 | "Modelo no disponible", "Selecciona un modelo de Ollama válido.", parent=self | INFO | Latin_Extended |
| 499 | main.py | other_non_ascii | 695 | "Datos no cargados", "Los datos del estudio AI aún no están listos.", parent=self | INFO | Latin_Extended |
| 500 | main.py | other_non_ascii | 700 | self.gen_btn.configure(state="disabled", text="⏳ Generando...") | INFO | Other_NonASCII |
| 501 | main.py | other_non_ascii | 710 | f"-- Generado por AI OpenTibia Map Studio  [{timestamp}]\n-- Modelo: {model}\n-- Descripción: {prompt[:80]}...\n\n", | INFO | Latin_Extended |
| 502 | main.py | other_non_ascii | 749 | self.gen_btn.configure(state="normal", text="▶  GENERAR SCRIPT LUA") | INFO | Other_NonASCII |
| 503 | main.py | other_non_ascii | 750 | self._set_status("✓ Script generado exitosamente. Usa 'Guardar .lua' para exportarlo.") | INFO | Other_NonASCII |
| 504 | main.py | other_non_ascii | 756 | self.gen_btn.configure(state="normal", text="▶  GENERAR SCRIPT LUA") | INFO | Other_NonASCII |
| 505 | main.py | other_non_ascii | 759 | self._set_status(f"✗ Error: {msg}") | INFO | Other_NonASCII |
| 506 | main.py | comment | 768 | # ── UI Helpers ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 507 | main.py | other_non_ascii | 778 | "-- El script Lua generado aparecerá aquí.\n" | INFO | Latin_Extended |
| 508 | main.py | other_non_ascii | 779 | "-- Configura los archivos de datos y escribe una descripción\n" | INFO | Latin_Extended |
| 509 | main.py | other_non_ascii | 781 | "-- Ejemplo de lo que se generará:\n" | INFO | Latin_Extended |
| 510 | main.py | other_non_ascii | 804 | if not content or content.startswith("-- El script Lua generado aparecerá"): | INFO | Latin_Extended |
| 511 | main.py | other_non_ascii | 818 | self._set_status(f"✓ Script guardado en: {path}") | INFO | Other_NonASCII |
| 512 | main.py | other_non_ascii | 830 | self._set_status("Configuración actualizada. Recargando datos...") | INFO | Latin_Extended |
| 513 | main.py | comment | 839 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 514 | main.py | comment | 841 | # ═══════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 515 | mkall.py | other_non_ascii | 1 | ﻿ | INFO | Other_NonASCII |
| 516 | ollama_client.py | other_non_ascii | 3 | Comunicación con Ollama para generar scripts Lua válidos para OpenTibiaBR RME. | INFO | Latin_Extended |
| 517 | ollama_client.py | other_non_ascii | 24 | Usa únicamente: | INFO | Latin_Extended |
| 518 | ollama_client.py | other_non_ascii | 48 | Responde únicamente con el script Lua, sin explicaciones adicionales y sin bloques markdown. | INFO | Latin_Extended |
| 519 | ollama_client.py | other_non_ascii | 68 | return False, f"Ollama respondió HTTP {response.status_code}" | INFO | Latin_Extended |
| 520 | ollama_client.py | other_non_ascii | 70 | return False, "No se pudo conectar a Ollama en localhost:11434. ¿Está iniciado?" | INFO | Other_NonASCII, Latin_Extended |
| 521 | ollama_client.py | other_non_ascii | 108 | f"Genera un script Lua válido para OpenTibiaBR RME con esta información." | INFO | Latin_Extended |
| 522 | ollama_client.py | other_non_ascii | 163 | f"Error de Ollama: HTTP {response.status_code} — {response.text[:200]}" | INFO | Other_NonASCII |
| 523 | ollama_client.py | other_non_ascii | 182 | on_error("Conexión perdida con Ollama. ¿Sigue en ejecución?") | INFO | Other_NonASCII, Latin_Extended |
| 524 | ollama_client.py | other_non_ascii | 184 | on_error("Tiempo de espera agotado. El modelo tardó demasiado.") | INFO | Latin_Extended |
| 525 | pipeline_runner.py | other_non_ascii | 2 | MVP V0.1 — Pipeline Runner | INFO | Other_NonASCII |
| 526 | pipeline_runner.py | comment | 102 | # Stage 4: Convertir City → WorldModel | WARNING | Other_NonASCII |
| 527 | pipeline_runner.py | comment | 113 | # Validación (skipped for city) | WARNING | Latin_Extended |
| 528 | pipeline_runner.py | other_non_ascii | 143 | ascii_preview = "(city — sin preview ASCII)" | INFO | Other_NonASCII |
| 529 | pipeline_runner.py | other_non_ascii | 208 | ascii_preview = "(dungeon multinivel — sin preview ASCII)" | INFO | Other_NonASCII |
| 530 | pyproject.toml | config_text | 8 | description = "OpenTibiaBR RME Map Agent — AI-powered Tibia map generator for RME" | INFO | Other_NonASCII |
| 531 | quality_report.json | export_value | 40 | "issue": "datetime.utcnow() — use datetime.now(timezone.utc)" | WARNING | Other_NonASCII |
| 532 | quality_report.json | export_value | 45 | "issue": "datetime.utcnow() — use datetime.now(timezone.utc)" | WARNING | Other_NonASCII |
| 533 | README.md | documentation_text | 15 | **Compatible con:** RME · OTBM · Canary · TFS · OTClient | INFO | Other_NonASCII |
| 534 | README.md | documentation_text | 19 | ## 📋 Descripción General | INFO | Other_NonASCII, Latin_Extended |
| 535 | README.md | documentation_text | 23 | El sistema toma una **descripción en lenguaje natural** del mapa deseado y genera automáticamente: | INFO | Latin_Extended |
| 536 | README.md | documentation_text | 30 | Todo el contenido es **100% oficial** de OpenTibia (extraído directamente de `items.xml`, `monster.xml` y `npc.xml`). | INFO | Latin_Extended |
| 537 | README.md | documentation_text | 32 | > *"La IA diseña. RME construye. Tu servidor cobra vida."* | INFO | Latin_Extended |
| 538 | README.md | documentation_text | 36 | ## ✨ Características Principales | INFO | Other_NonASCII, Latin_Extended |
| 539 | README.md | documentation_text | 38 | ### Generación de Mapas | INFO | Latin_Extended |
| 540 | README.md | documentation_text | 39 | - 🏰 **Ciudades** completas (calles, edificios, templos, NPCs) | INFO | Other_NonASCII |
| 541 | README.md | documentation_text | 40 | - 🗡️ **Mazmorras** (salas, pasillos, jefes, trampas) | INFO | Other_NonASCII |
| 542 | README.md | documentation_text | 41 | - 🌲 **Zonas de hunt** con spawns progresivos y balanceados | INFO | Other_NonASCII |
| 543 | README.md | documentation_text | 42 | - 🏝️ **Islas** y terrenos naturales | INFO | Other_NonASCII |
| 544 | README.md | documentation_text | 43 | - 🔄 **Mapas híbridos** (ciudad + mazmorra) | INFO | Other_NonASCII, Latin_Extended |
| 545 | README.md | documentation_text | 46 | - 🧠 **AIPlanner**: Convierte texto en planes de construcción detallados | INFO | Other_NonASCII, Latin_Extended |
| 546 | README.md | documentation_text | 47 | - 📐 **WorldBrain**: Sistema de razonamiento con objetivos y restricciones | INFO | Other_NonASCII |
| 547 | README.md | documentation_text | 48 | - 🔍 **RAG embebido**: Recuperación semántica de items, monstruos y NPCs | INFO | Other_NonASCII, Latin_Extended |
| 548 | README.md | documentation_text | 49 | - 🧬 **PatternLibrary**: Aprendizaje de patrones arquitectónicos reales | INFO | Other_NonASCII, Latin_Extended |
| 549 | README.md | documentation_text | 51 | ### Exportación Profesional | INFO | Latin_Extended |
| 550 | README.md | documentation_text | 52 | - 📄 **Scripts Lua** para RME (Tools > Run Script) | INFO | Other_NonASCII |
| 551 | README.md | documentation_text | 53 | - 💾 **Archivos OTBM v4** (formato binario oficial) | INFO | Other_NonASCII |
| 552 | README.md | documentation_text | 54 | - 📋 **XML** de spawns y NPCs | INFO | Other_NonASCII |
| 553 | README.md | documentation_text | 55 | - 🗺️ **Zonas y waypoints** | INFO | Other_NonASCII |
| 554 | README.md | documentation_text | 56 | - 📸 **Previews** (ASCII, minimapa PNG y JSON) | INFO | Other_NonASCII |
| 555 | README.md | documentation_text | 60 | ## 🛠️ Stack Tecnológico | INFO | Other_NonASCII, Latin_Extended |
| 556 | README.md | documentation_text | 62 | \| Componente              \| Tecnología                          \| | INFO | Latin_Extended |
| 557 | README.md | documentation_text | 69 | \| Imágenes               \| Pillow                              \| | INFO | Latin_Extended |
| 558 | README.md | documentation_text | 71 | \| Configuración          \| PyYAML + JSON                       \| | INFO | Latin_Extended |
| 559 | README.md | documentation_text | 75 | ## 📦 Requisitos Previos | INFO | Other_NonASCII |
| 560 | README.md | documentation_text | 78 | - **Ollama** instalado y ejecutándose con al menos un modelo | INFO | Latin_Extended |
| 561 | README.md | documentation_text | 87 | 1. **Instalación** | INFO | Latin_Extended |
| 562 | README.md | documentation_text | 91 | 2. **Ejecución** | INFO | Latin_Extended |
| 563 | README.md | documentation_text | 95 | 3. **Documentación** | INFO | Latin_Extended |
| 564 | README.md | documentation_text | 97 | - Extensión del agente: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md). | INFO | Latin_Extended |
| 565 | README.md | documentation_text | 99 | ## Versión Actual | INFO | Latin_Extended |
| 566 | README.md | documentation_text | 103 | ### Flujo básico | INFO | Latin_Extended |
| 567 | README.md | documentation_text | 111 | ## 📁 Estructura de Salida | INFO | Other_NonASCII |
| 568 | README.md | documentation_text | 115 | ├── map.otbm              # Mapa binario para servidor | INFO | Other_NonASCII |
| 569 | README.md | documentation_text | 116 | ├── map.lua               # Script para RME | INFO | Other_NonASCII |
| 570 | README.md | documentation_text | 117 | ├── map.monster.xml       # Spawns | INFO | Other_NonASCII |
| 571 | README.md | documentation_text | 118 | ├── map.npc.xml           # NPCs | INFO | Other_NonASCII |
| 572 | README.md | documentation_text | 119 | ├── map.zones.xml         # Waypoints y zonas | INFO | Other_NonASCII |
| 573 | README.md | documentation_text | 120 | ├── preview.png           # Vista previa | INFO | Other_NonASCII |
| 574 | README.md | documentation_text | 121 | ├── preview_minimap.png   # Minimapa | INFO | Other_NonASCII |
| 575 | README.md | documentation_text | 122 | └── preview_ascii.txt     # Representación textual | INFO | Other_NonASCII, Latin_Extended |
| 576 | README.md | documentation_text | 127 | ## 🏗️ Arquitectura | INFO | Other_NonASCII |
| 577 | README.md | documentation_text | 130 | - **AIPlanner**: Planificación inteligente | INFO | Latin_Extended |
| 578 | README.md | documentation_text | 132 | - **WorldModel + WorldEngine**: Núcleo del mundo (Tiles, Chunks, Regions) | INFO | Latin_Extended |
| 579 | README.md | documentation_text | 138 | ## 🗺️ Mapas de Referencia Soportados | INFO | Other_NonASCII |
| 580 | README.md | documentation_text | 146 | ## 🤝 Cómo Contribuir | INFO | Other_NonASCII, Latin_Extended |
| 581 | README.md | documentation_text | 155 | **Estándares:** | INFO | Latin_Extended |
| 582 | README.md | documentation_text | 163 | **La IA diseña. RME construye. Tu servidor cobra vida.** | INFO | Latin_Extended |
| 583 | README.md | documentation_text | 169 | Generado con ❤️ por <strong>Ricker</strong> • Kruger Developers • Comunidad OpenTibia | INFO | Other_NonASCII |
| 584 | README.md | documentation_text | 174 | ## 📜 Licencia | INFO | Other_NonASCII |
| 585 | README.md | documentation_text | 176 | Este proyecto está licenciado bajo la **MIT License**. | INFO | Latin_Extended |
| 586 | rme.py | other_non_ascii | 2 | rme.py — Agente RME v1.0.0 GA unified CLI entry point. | INFO | Other_NonASCII |
| 587 | rme.py | comment | 40 | # ── GA commands (v1.0.0) ──────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 588 | rme.py | docstring | 44 | """rme health — system health checks.""" | WARNING | Other_NonASCII |
| 589 | rme.py | docstring | 72 | """rme metrics — runtime metrics.""" | WARNING | Other_NonASCII |
| 590 | rme.py | docstring | 105 | """rme analyze — analyze a world or OTBM file.""" | WARNING | Other_NonASCII |
| 591 | rme.py | docstring | 145 | """rme critic — run the critic on a world.""" | WARNING | Other_NonASCII |
| 592 | rme.py | docstring | 188 | """rme benchmark — run a production benchmark.""" | WARNING | Other_NonASCII |
| 593 | rme.py | docstring | 212 | """rme diagnose — run diagnostics and export report.""" | WARNING | Other_NonASCII |
| 594 | rme.py | comment | 232 | # ── Wrapper: delegate to cli.py for legacy commands ────────────────────────── | WARNING | Other_NonASCII |
| 595 | rme.py | comment | 256 | # ── main ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 596 | setup_init.py | other_non_ascii | 1 | ﻿import os | INFO | Other_NonASCII |
| 597 | task_progress.md | documentation_text | 24 | - [ ] `autonomous_world_designer.py` (main façade) | INFO | Latin_Extended |
| 598 | TROUBLESHOOTING.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Troubleshooting | INFO | Other_NonASCII |
| 599 | TROUBLESHOOTING.md | documentation_text | 62 | - Verify the prompt — try `"Issavi hunt level 300"` directly. | INFO | Other_NonASCII |
| 600 | TROUBLESHOOTING.md | documentation_text | 128 | - Use the `production` profile: `python rme.py --profile production …` | INFO | Other_NonASCII |
| 601 | UI_DASHBOARD_REPORT.md | documentation_text | 1 | # UI Dashboard Report — HITO UI-3: Dashboard Command Center | INFO | Other_NonASCII |
| 602 | UI_DASHBOARD_REPORT.md | documentation_text | 54 | \| MetricCard (Knowledge Entries) \| `knowledge_metrics.json` → `total_entries` \| | INFO | Other_NonASCII |
| 603 | UI_DASHBOARD_REPORT.md | documentation_text | 55 | \| MetricCard (Critic Score) \| `critic.json` → `score` \| | INFO | Other_NonASCII |
| 604 | UI_DASHBOARD_REPORT.md | documentation_text | 56 | \| MetricCard (Success Rate) \| `agent_metrics.json` → `agent_success_rate` \| | INFO | Other_NonASCII |
| 605 | UI_DASHBOARD_REPORT.md | documentation_text | 59 | \| HealthWidget \| `health_report.json` → `status` \| | INFO | Other_NonASCII |
| 606 | UI_DASHBOARD_REPORT.md | documentation_text | 98 | 1. **Missing JSON files**: Handled gracefully — shows "No Data" | INFO | Other_NonASCII |
| 607 | UI_DASHBOARD_REPORT.md | documentation_text | 105 | - ✅ 0 changes to `core/` | INFO | Other_NonASCII |
| 608 | UI_DASHBOARD_REPORT.md | documentation_text | 106 | - ✅ 0 changes to `agents/` | INFO | Other_NonASCII |
| 609 | UI_DASHBOARD_REPORT.md | documentation_text | 107 | - ✅ 0 changes to `architect/` | INFO | Other_NonASCII |
| 610 | UI_DASHBOARD_REPORT.md | documentation_text | 108 | - ✅ 0 changes to `autonomous/` | INFO | Other_NonASCII |
| 611 | UI_DASHBOARD_REPORT.md | documentation_text | 109 | - ✅ 0 changes to `critic/` | INFO | Other_NonASCII |
| 612 | UI_DASHBOARD_REPORT.md | documentation_text | 110 | - ✅ 0 changes to `knowledge/` | INFO | Other_NonASCII |
| 613 | UI_DASHBOARD_REPORT.md | documentation_text | 111 | - ✅ 0 changes to `blueprint_intelligence/` | INFO | Other_NonASCII |
| 614 | UI_DASHBOARD_REPORT.md | documentation_text | 112 | - ✅ 0 changes to `campaign/` | INFO | Other_NonASCII |
| 615 | UI_DASHBOARD_REPORT.md | documentation_text | 113 | - ✅ 0 changes to `export/` | INFO | Other_NonASCII |
| 616 | UI_DASHBOARD_REPORT.md | documentation_text | 114 | - ✅ 0 changes to `otbm/` | INFO | Other_NonASCII |
| 617 | UI_DASHBOARD_REPORT.md | documentation_text | 115 | - ✅ 0 changes to `playtest/` | INFO | Other_NonASCII |
| 618 | UI_DASHBOARD_REPORT.md | documentation_text | 116 | - ✅ 0 changes to `world/` | INFO | Other_NonASCII |
| 619 | UI_DASHBOARD_REPORT.md | documentation_text | 122 | \| Dashboard loads correctly \| ✅ \| | INFO | Other_NonASCII |
| 620 | UI_DASHBOARD_REPORT.md | documentation_text | 123 | \| Metric Cards visible \| ✅ \| | INFO | Other_NonASCII |
| 621 | UI_DASHBOARD_REPORT.md | documentation_text | 124 | \| Health Widget functional \| ✅ \| | INFO | Other_NonASCII |
| 622 | UI_DASHBOARD_REPORT.md | documentation_text | 125 | \| Recent Artifacts functional \| ✅ \| | INFO | Other_NonASCII |
| 623 | UI_DASHBOARD_REPORT.md | documentation_text | 126 | \| Recent Activity functional \| ✅ \| | INFO | Other_NonASCII |
| 624 | UI_DASHBOARD_REPORT.md | documentation_text | 127 | \| Auto Refresh functional \| ✅ \| | INFO | Other_NonASCII |
| 625 | UI_DASHBOARD_REPORT.md | documentation_text | 128 | \| Coverage >80% \| ✅ \| | INFO | Other_NonASCII |
| 626 | UI_DASHBOARD_REPORT.md | documentation_text | 129 | \| Tests green \| ✅ \| | INFO | Other_NonASCII |
| 627 | UI_DASHBOARD_REPORT.md | documentation_text | 130 | \| 0 changes in core \| ✅ \| | INFO | Other_NonASCII |
| 628 | UI_DASHBOARD_REPORT.md | documentation_text | 131 | \| UI_DASHBOARD_REPORT.md generated \| ✅ \| | INFO | Other_NonASCII |
| 629 | UI_FOUNDATION_REPORT.md | documentation_text | 1 | # UI Foundation Report — Agente RME Studio | INFO | Other_NonASCII |
| 630 | UI_FOUNDATION_REPORT.md | documentation_text | 5 | > **Status:** ✅ **GA Freeze Compliant** — No core modules modified or imported. | INFO | Other_NonASCII |
| 631 | UI_FOUNDATION_REPORT.md | documentation_text | 15 | \| 2 \| `ui/app.py` \| `RMEStudioApp` — QApplication wrapper, event loop entry point \| | INFO | Other_NonASCII |
| 632 | UI_FOUNDATION_REPORT.md | documentation_text | 38 | │ | INFO | Other_NonASCII |
| 633 | UI_FOUNDATION_REPORT.md | documentation_text | 39 | ▼ | INFO | Other_NonASCII |
| 634 | UI_FOUNDATION_REPORT.md | documentation_text | 40 | Services  (ui/services/*.py)   ← interfaces only | INFO | Other_NonASCII |
| 635 | UI_FOUNDATION_REPORT.md | documentation_text | 41 | │ | INFO | Other_NonASCII |
| 636 | UI_FOUNDATION_REPORT.md | documentation_text | 42 | ▼ | INFO | Other_NonASCII |
| 637 | UI_FOUNDATION_REPORT.md | documentation_text | 43 | Adapters  (ui/adapters/*.py)   ← interfaces only | INFO | Other_NonASCII |
| 638 | UI_FOUNDATION_REPORT.md | documentation_text | 44 | │ | INFO | Other_NonASCII |
| 639 | UI_FOUNDATION_REPORT.md | documentation_text | 45 | ▼ | INFO | Other_NonASCII |
| 640 | UI_FOUNDATION_REPORT.md | documentation_text | 46 | Core      (FROZEN — NOT TOUCHED) | INFO | Other_NonASCII |
| 641 | UI_FOUNDATION_REPORT.md | documentation_text | 72 | \| `PySide6` \| ≥6.11.1 \| Runtime \| ✅ Installed \| | INFO | Other_NonASCII |
| 642 | UI_FOUNDATION_REPORT.md | documentation_text | 73 | \| `shiboken6` \| 6.11.1 \| Runtime (bundled) \| ✅ Installed \| | INFO | Other_NonASCII |
| 643 | UI_FOUNDATION_REPORT.md | documentation_text | 95 | \| No modifications to `core/` \| ✅ Pass \| `git diff --name-only` shows only new `ui/` files \| | INFO | Other_NonASCII |
| 644 | UI_FOUNDATION_REPORT.md | documentation_text | 96 | \| No modifications to `agents/` \| ✅ Pass \| Same \| | INFO | Other_NonASCII |
| 645 | UI_FOUNDATION_REPORT.md | documentation_text | 97 | \| No modifications to `architect/`, `autonomous/`, `critic/`, `knowledge/`, `blueprint_intelligence/`, `campaign/`, `export/`, `otbm/`, `playtest/`,  | INFO | Other_NonASCII |
| 646 | UI_FOUNDATION_REPORT.md | documentation_text | 98 | \| No changes to existing APIs \| ✅ Pass \| Existing `.py` files untouched \| | INFO | Other_NonASCII |
| 647 | UI_FOUNDATION_REPORT.md | documentation_text | 99 | \| No changes to certified tests \| ✅ Pass \| `tests/` directory untouched \| | INFO | Other_NonASCII |
| 648 | UI_SHELL_REPORT.md | documentation_text | 1 | # UI Shell Report — HITO UI-2: Application Shell | INFO | Other_NonASCII |
| 649 | UI_SHELL_REPORT.md | documentation_text | 56 | **Target coverage on `ui/navigation.py`: >= 80% → Achieved: 100%** | INFO | Other_NonASCII |
| 650 | UI_SHELL_REPORT.md | documentation_text | 75 | ┌─────────────────────────────┐ | INFO | Other_NonASCII |
| 651 | UI_SHELL_REPORT.md | documentation_text | 76 | │ TitleBar                    │ | INFO | Other_NonASCII |
| 652 | UI_SHELL_REPORT.md | documentation_text | 77 | ├──────┬──────────────────────┤ | INFO | Other_NonASCII |
| 653 | UI_SHELL_REPORT.md | documentation_text | 78 | │ Side │                      │ | INFO | Other_NonASCII |
| 654 | UI_SHELL_REPORT.md | documentation_text | 79 | │ Bar  │ Workspace            │ | INFO | Other_NonASCII |
| 655 | UI_SHELL_REPORT.md | documentation_text | 80 | │      │ (QStackedWidget)     │ | INFO | Other_NonASCII |
| 656 | UI_SHELL_REPORT.md | documentation_text | 81 | ├──────┴──────────────────────┤ | INFO | Other_NonASCII |
| 657 | UI_SHELL_REPORT.md | documentation_text | 82 | │ Console                    │ | INFO | Other_NonASCII |
| 658 | UI_SHELL_REPORT.md | documentation_text | 83 | ├─────────────────────────────┤ | INFO | Other_NonASCII |
| 659 | UI_SHELL_REPORT.md | documentation_text | 84 | │ Status Bar                 │ | INFO | Other_NonASCII |
| 660 | UI_SHELL_REPORT.md | documentation_text | 85 | └─────────────────────────────┘ | INFO | Other_NonASCII |
| 661 | UI_SHELL_REPORT.md | documentation_text | 109 | \| No import from `core/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 662 | UI_SHELL_REPORT.md | documentation_text | 110 | \| No import from `agents/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 663 | UI_SHELL_REPORT.md | documentation_text | 111 | \| No import from `architect/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 664 | UI_SHELL_REPORT.md | documentation_text | 112 | \| No import from `autonomous/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 665 | UI_SHELL_REPORT.md | documentation_text | 113 | \| No import from `critic/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 666 | UI_SHELL_REPORT.md | documentation_text | 114 | \| No import from `knowledge/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 667 | UI_SHELL_REPORT.md | documentation_text | 115 | \| No import from `blueprint_intelligence/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 668 | UI_SHELL_REPORT.md | documentation_text | 116 | \| No import from `campaign/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 669 | UI_SHELL_REPORT.md | documentation_text | 117 | \| No import from `export/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 670 | UI_SHELL_REPORT.md | documentation_text | 118 | \| No import from `otbm/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 671 | UI_SHELL_REPORT.md | documentation_text | 119 | \| No import from `playtest/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 672 | UI_SHELL_REPORT.md | documentation_text | 120 | \| No import from `world/` \| ✅ Verified \| | INFO | Other_NonASCII |
| 673 | UI_SHELL_REPORT.md | documentation_text | 121 | \| No real services consumed \| ✅ Verified \| | INFO | Other_NonASCII |
| 674 | UI_SHELL_REPORT.md | documentation_text | 122 | \| No business logic \| ✅ Verified \| | INFO | Other_NonASCII |
| 675 | UI_SHELL_REPORT.md | documentation_text | 123 | \| Only Shell UI code \| ✅ Verified \| | INFO | Other_NonASCII |
| 676 | UI_SHELL_REPORT.md | documentation_text | 140 | - **Agente RME v1.0.0 GA** remains **frozen** — no core modules modified | INFO | Other_NonASCII |
| 677 | USER_GUIDE.md | documentation_text | 1 | # Agente RME v1.0.0 GA — User Guide | INFO | Other_NonASCII |
| 678 | USER_GUIDE.md | documentation_text | 15 | ├── generated.lua | INFO | Other_NonASCII |
| 679 | USER_GUIDE.md | documentation_text | 16 | ├── generated.otbm | INFO | Other_NonASCII |
| 680 | USER_GUIDE.md | documentation_text | 17 | ├── generated_preview.png | INFO | Other_NonASCII |
| 681 | USER_GUIDE.md | documentation_text | 18 | ├── generated.monster.xml      (if spawns) | INFO | Other_NonASCII |
| 682 | USER_GUIDE.md | documentation_text | 19 | ├── generated.houses.xml       (if houses) | INFO | Other_NonASCII |
| 683 | USER_GUIDE.md | documentation_text | 20 | ├── generated.waypoints.xml    (if waypoints) | INFO | Other_NonASCII |
| 684 | USER_GUIDE.md | documentation_text | 21 | └── generated_report.json | INFO | Other_NonASCII |
| 685 | USER_GUIDE.md | documentation_text | 78 | - **system** — Python version, platform, memory, disk | INFO | Other_NonASCII |
| 686 | USER_GUIDE.md | documentation_text | 79 | - **module** — one check per core module (generators, exporters, otbm, preview, knowledge, critic, blueprint_intelligence) | INFO | Other_NonASCII |
| 687 | USER_GUIDE.md | documentation_text | 80 | - **pipeline** — a tiny generation succeeds | INFO | Other_NonASCII |
| 688 | USER_GUIDE.md | documentation_text | 81 | - **knowledge** — dataset present and loadable | INFO | Other_NonASCII |
| 689 | USER_GUIDE.md | documentation_text | 82 | - **blueprints** — at least one blueprint file present | INFO | Other_NonASCII |
| 690 | USER_GUIDE.md | documentation_text | 94 | - success rate (target ≥ 99%) | INFO | Other_NonASCII |
| 691 | USER_GUIDE.md | documentation_text | 122 | - `default.yaml` — neutral | INFO | Other_NonASCII |
| 692 | USER_GUIDE.md | documentation_text | 123 | - `development.yaml` — debug logging, no minification | INFO | Other_NonASCII |
| 693 | USER_GUIDE.md | documentation_text | 124 | - `production.yaml` — INFO logging, optimization on, validation strict | INFO | Other_NonASCII |
| 694 | validate_hito_26_1b.py | other_non_ascii | 2 | HITO 26.1B — End-to-end pipeline validation. | INFO | Other_NonASCII |
| 695 | validate_hito_26_1b.py | other_non_ascii | 5 | ↓ | INFO | Other_NonASCII |
| 696 | validate_hito_26_1b.py | other_non_ascii | 7 | ↓ | INFO | Other_NonASCII |
| 697 | validate_hito_26_1b.py | other_non_ascii | 9 | ↓ | INFO | Other_NonASCII |
| 698 | validate_hito_26_1b.py | other_non_ascii | 14 | * archivo no vacío | INFO | Latin_Extended |
| 699 | validate_hito_26_1b.py | other_non_ascii | 15 | * sintaxis válida | INFO | Latin_Extended |
| 700 | validate_hito_26_1b.py | comment | 86 | # ---- Step 1: Prompt → WorldModel ---- | WARNING | Other_NonASCII |
| 701 | validate_hito_26_1b.py | comment | 94 | # ---- Step 2: WorldModel → LuaGenerator (no spawn_plan) ---- | WARNING | Other_NonASCII |
| 702 | validate_hito_26_1b.py | comment | 116 | # archivo no vacío | WARNING | Latin_Extended |
| 703 | validate_hito_26_1b.py | other_non_ascii | 118 | assert size > 0, f"archivo no vacío: FAIL (size={size})" | INFO | Latin_Extended |
| 704 | validate_hito_26_1b.py | print_string | 119 | print(f"[OK] archivo no vacío ({size} bytes)") | WARNING | Latin_Extended |
| 705 | validate_hito_26_1b.py | comment | 121 | # sintaxis válida | WARNING | Latin_Extended |
| 706 | validate_hito_26_1b.py | other_non_ascii | 122 | assert is_balanced(script.code), "sintaxis válida: FAIL" | INFO | Latin_Extended |
| 707 | validate_hito_26_1b.py | print_string | 123 | print("[OK] sintaxis válida (parens balanced, function/end match)") | WARNING | Latin_Extended |
| 708 | validate_hito_26_1b.py | print_string | 145 | print("\n=== DEFINICIÓN DE DONE — ALL GREEN ===\n") | WARNING | Other_NonASCII, Latin_Extended |
| 709 | validate_hito_26_1e.py | other_non_ascii | 2 | HITO 26.1E — Final Validation Script | INFO | Other_NonASCII |
| 710 | validate_hito_26_1e.py | print_string | 84 | print(f"RESULT: {errors} file(s) with datetime.utcnow() — FAIL") | WARNING | Other_NonASCII |
| 711 | validate_hito_26_1e.py | print_string | 87 | print("RESULT: ALL CLEAN — No datetime.utcnow() found") | WARNING | Other_NonASCII |
| 712 | _quality_report.py | docstring | 1 | """_quality_report.py — Generate quality_report.json for the GA release.""" | WARNING | Other_NonASCII |
| 713 | _quality_report.py | other_non_ascii | 31 | r"\bdatetime\.utcnow\(\)": "datetime.utcnow() — use datetime.now(timezone.utc)", | INFO | Other_NonASCII |
| 714 | _quality_report.py | other_non_ascii | 32 | r"\bos\.popen\b": "os.popen — use subprocess", | INFO | Other_NonASCII |
| 715 | _quality_report.py | other_non_ascii | 33 | r"\bimp\.find_module\b": "imp module — use importlib", | INFO | Other_NonASCII |
| 716 | _wf.py | docstring | 1 | """BlueprintFusion model — vector representation of a blueprint.""" | WARNING | Other_NonASCII |
| 717 | ai\ollama_client.py | other_non_ascii | 32 | return False, f"Ollama respondió con HTTP {response.status_code}" | INFO | Latin_Extended |
| 718 | ai\prompt_builder.py | other_non_ascii | 10 | "Tu salida debe ser un script Lua válido para RME que use la API real de OpenTibiaBR. " | INFO | Latin_Extended |
| 719 | ai\prompt_builder.py | other_non_ascii | 11 | "No incluyas explicaciones, solo el código Lua necesario en la respuesta final.\n" | INFO | Latin_Extended |
| 720 | ai\prompt_builder.py | other_non_ascii | 12 | "Usa preferentemente funciones de transacción y validación de mapa como app.transaction() y app.hasMap()." | INFO | Latin_Extended |
| 721 | ai\prompt_builder.py | other_non_ascii | 23 | "Genera un script Lua para RME basado en la descripción del mapa y los datos del juego. " | INFO | Latin_Extended |
| 722 | ai\prompt_builder.py | other_non_ascii | 29 | "Reglas de generación:\n" | INFO | Latin_Extended |
| 723 | ai\prompt_builder.py | other_non_ascii | 33 | "4) Evita comentarios explicativos largos en el código. Usa comentarios mínimos si es necesario.\n" | INFO | Latin_Extended |
| 724 | ai\prompt_builder.py | other_non_ascii | 37 | f"Descripción del mapa: {description}", | INFO | Latin_Extended |
| 725 | baseline\golden_maps\Falcon\critic_report.json | export_value | 244 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 726 | baseline\golden_maps\Falcon\critic_report.json | export_value | 253 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 727 | baseline\golden_maps\Falcon\critic_report.json | export_value | 262 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 728 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 1 | # Critic Report — falcon_150 | INFO | Other_NonASCII |
| 729 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.923061  •  Version: 1.0_ | INFO | Other_NonASCII |
| 730 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 731 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (24,24,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 732 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 37 | \| warning \| bottleneck \| pathfinding \| (24,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 733 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 42 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 734 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 47 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 735 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 52 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 736 | baseline\golden_maps\Falcon\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 737 | baseline\golden_maps\Ferumbras\critic_report.json | export_value | 189 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 738 | baseline\golden_maps\Ferumbras\critic_report.json | export_value | 198 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 739 | baseline\golden_maps\Ferumbras\critic_report.json | export_value | 207 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 740 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 1 | # Critic Report — ancient_temple_300 | INFO | Other_NonASCII |
| 741 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.180597  •  Version: 1.0_ | INFO | Other_NonASCII |
| 742 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 30 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 743 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 31 | \| warning \| bottleneck \| pathfinding \| (34,34,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 744 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,34,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 745 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 37 | _Priority: medium  •  Category: spawn_ | INFO | Other_NonASCII |
| 746 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 42 | _Priority: low  •  Category: hunt_ | INFO | Other_NonASCII |
| 747 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 47 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 748 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 52 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 749 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 750 | baseline\golden_maps\Ferumbras\critic_report.md | documentation_text | 62 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 751 | baseline\golden_maps\Issavi\critic_report.json | export_value | 223 | "message": "Hunts 0 and 2 are 120 tiles apart — consider adding a closer hunt", | WARNING | Other_NonASCII |
| 752 | baseline\golden_maps\Issavi\critic_report.json | export_value | 234 | "message": "Only 3 unique decoration types — map looks repetitive", | WARNING | Other_NonASCII |
| 753 | baseline\golden_maps\Issavi\critic_report.json | export_value | 303 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 754 | baseline\golden_maps\Issavi\critic_report.json | export_value | 312 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 755 | baseline\golden_maps\Issavi\critic_report.json | export_value | 321 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 756 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 1 | # Critic Report — issavi_300_500 | INFO | Other_NonASCII |
| 757 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:20.909206  •  Version: 1.0_ | INFO | Other_NonASCII |
| 758 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 32 | \| warning \| hunt_gap \| hunt \| - \| Hunts 0 and 2 are 120 tiles apart — consider adding a closer hunt \| | INFO | Other_NonASCII |
| 759 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 33 | \| warning \| underdecorated_area \| decor \| - \| Only 3 unique decoration types — map looks repetitive \| | INFO | Other_NonASCII |
| 760 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 40 | \| warning \| bottleneck \| pathfinding \| (180,180,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 761 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 41 | \| warning \| bottleneck \| pathfinding \| (219,180,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 762 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 42 | \| warning \| bottleneck \| pathfinding \| (180,219,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 763 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 47 | _Priority: high  •  Category: navigation_ | INFO | Other_NonASCII |
| 764 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 52 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 765 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: decor_ | INFO | Other_NonASCII |
| 766 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 62 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 767 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 67 | _Priority: critical  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 768 | baseline\golden_maps\Issavi\critic_report.md | documentation_text | 72 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 769 | baseline\golden_maps\Library\critic_report.json | export_value | 199 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 770 | baseline\golden_maps\Library\critic_report.json | export_value | 208 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 771 | baseline\golden_maps\Library\critic_report.json | export_value | 217 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 772 | baseline\golden_maps\Library\critic_report.md | documentation_text | 1 | # Critic Report — library_200 | INFO | Other_NonASCII |
| 773 | baseline\golden_maps\Library\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.827241  •  Version: 1.0_ | INFO | Other_NonASCII |
| 774 | baseline\golden_maps\Library\critic_report.md | documentation_text | 31 | \| warning \| bottleneck \| pathfinding \| (19,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 775 | baseline\golden_maps\Library\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 776 | baseline\golden_maps\Library\critic_report.md | documentation_text | 33 | \| warning \| bottleneck \| pathfinding \| (0,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 777 | baseline\golden_maps\Library\critic_report.md | documentation_text | 38 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 778 | baseline\golden_maps\Library\critic_report.md | documentation_text | 43 | _Priority: low  •  Category: hunt_ | INFO | Other_NonASCII |
| 779 | baseline\golden_maps\Library\critic_report.md | documentation_text | 48 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 780 | baseline\golden_maps\Library\critic_report.md | documentation_text | 53 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 781 | baseline\golden_maps\Library\critic_report.md | documentation_text | 58 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 782 | baseline\golden_maps\Library\critic_report.md | documentation_text | 63 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 783 | baseline\golden_maps\Roshamuul\critic_report.json | export_value | 214 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 784 | baseline\golden_maps\Roshamuul\critic_report.json | export_value | 223 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 785 | baseline\golden_maps\Roshamuul\critic_report.json | export_value | 232 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 786 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 1 | # Critic Report — roshamuul_400_600 | INFO | Other_NonASCII |
| 787 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.538040  •  Version: 1.0_ | INFO | Other_NonASCII |
| 788 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,39,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 789 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 33 | \| warning \| bottleneck \| pathfinding \| (39,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 790 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 791 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 39 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 792 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 44 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 793 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 49 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 794 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 54 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 795 | baseline\golden_maps\Roshamuul\critic_report.md | documentation_text | 59 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 796 | baseline\golden_maps\Soul War\critic_report.json | export_value | 232 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 797 | baseline\golden_maps\Soul War\critic_report.json | export_value | 241 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 798 | baseline\golden_maps\Soul War\critic_report.json | export_value | 250 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 799 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 1 | # Critic Report — soul_war_300 | INFO | Other_NonASCII |
| 800 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.723507  •  Version: 1.0_ | INFO | Other_NonASCII |
| 801 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (29,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 802 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 803 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (0,29,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 804 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 41 | _Priority: medium  •  Category: visual_ | INFO | Other_NonASCII |
| 805 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 46 | _Priority: medium  •  Category: density_ | INFO | Other_NonASCII |
| 806 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 51 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 807 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 56 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 808 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 61 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 809 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 66 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 810 | baseline\golden_maps\Soul War\critic_report.md | documentation_text | 71 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 811 | baseline\golden_reports\critic_report.json | export_value | 256 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 812 | baseline\golden_reports\critic_report.json | export_value | 265 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 813 | baseline\golden_reports\critic_report.json | export_value | 274 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 814 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Release Notes | INFO | Other_NonASCII |
| 815 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 4 | > **Status:** GENERAL AVAILABILITY — PRODUCTION READY — SUPPORTED RELEASE | INFO | Other_NonASCII |
| 816 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 11 | - **Hardened release** — warnings, dead code, and legacy imports cleaned up; 0 critical errors in `quality_report.json`. | INFO | Other_NonASCII |
| 817 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 12 | - **Cross-platform installers** — Windows (PowerShell), Linux (bash), macOS (bash). Each installs in **under 5 minutes**. | INFO | Other_NonASCII |
| 818 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 13 | - **Configuration management** — `ConfigManager` with hot-reload, validation, and three profiles (`default`, `development`, `production`). | INFO | Other_NonASCII |
| 819 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 14 | - **Observability layer** — `core/observability/` provides logger, metrics, health, and diagnostics. Every command exports a JSON snapshot. | INFO | Other_NonASCII |
| 820 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 15 | - **Health checks** — 11 system-wide checks (`rme health`) producing `health_report.json`. Exit code 0 = healthy. | INFO | Other_NonASCII |
| 821 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 16 | - **Crash recovery** — `RecoveryManager` checkpoints, atomically writes outputs, and supports rollback. Exports `recovery_report.json`. | INFO | Other_NonASCII |
| 822 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 17 | - **Production benchmark** — 500 worlds in ~2.2 seconds on a fast machine, **100% success rate**, 227+ worlds/s. | INFO | Other_NonASCII |
| 823 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 18 | - **CLI production mode** — `--verbose`, `--json`, `--profile` global flags; new commands: `health`, `metrics`, `analyze`, `critic`, `diagnose`, `benc | INFO | Other_NonASCII |
| 824 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 19 | - **Full documentation** — `README.md`, `INSTALL.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`,  | INFO | Other_NonASCII |
| 825 | baseline\golden_reports\GA_RELEASE_NOTES.md | documentation_text | 55 | 2. Re-run the installer for your platform (idempotent — it will not overwrite your `config.json`). | INFO | Other_NonASCII |
| 826 | baseline\golden_reports\GA_REPORT.md | documentation_text | 1 | # Agente RME v1.0.0 GA — Certification Report | INFO | Other_NonASCII |
| 827 | baseline\golden_reports\GA_REPORT.md | documentation_text | 4 | **Status:** ✅ PASS — GENERAL AVAILABILITY | INFO | Other_NonASCII |
| 828 | baseline\golden_reports\GA_REPORT.md | documentation_text | 14 | \| all_tests_pass \| ✅ \| | INFO | Other_NonASCII |
| 829 | baseline\golden_reports\GA_REPORT.md | documentation_text | 15 | \| coverage_maintained \| ✅ \| | INFO | Other_NonASCII |
| 830 | baseline\golden_reports\GA_REPORT.md | documentation_text | 16 | \| no_crashes \| ✅ \| | INFO | Other_NonASCII |
| 831 | baseline\golden_reports\GA_REPORT.md | documentation_text | 17 | \| no_otbm_corruption \| ✅ \| | INFO | Other_NonASCII |
| 832 | baseline\golden_reports\GA_REPORT.md | documentation_text | 18 | \| cli_stable \| ✅ \| | INFO | Other_NonASCII |
| 833 | baseline\golden_reports\GA_REPORT.md | documentation_text | 19 | \| installer_functional \| ✅ \| | INFO | Other_NonASCII |
| 834 | baseline\golden_reports\GA_REPORT.md | documentation_text | 20 | \| health_checks_pass \| ✅ \| | INFO | Other_NonASCII |
| 835 | baseline\golden_reports\GA_REPORT.md | documentation_text | 21 | \| recovery_pass \| ✅ \| | INFO | Other_NonASCII |
| 836 | baseline\golden_reports\GA_REPORT.md | documentation_text | 22 | \| observability_pass \| ✅ \| | INFO | Other_NonASCII |
| 837 | baseline\golden_reports\GA_REPORT.md | documentation_text | 28 | - Success rate: **100.00%** (target ≥ 99%) | INFO | Other_NonASCII |
| 838 | config\debug.yaml | config_text | 1 | # OpenTibiaBR RME Agent — Debug Configuration | INFO | Other_NonASCII |
| 839 | config\default.yaml | config_text | 1 | # OpenTibiaBR RME Agent — Default Configuration | INFO | Other_NonASCII |
| 840 | config\default.yaml | config_text | 2 | # V1.0.0 GA — Agente RME General Availability | INFO | Other_NonASCII |
| 841 | config\development.yaml | config_text | 1 | # OpenTibiaBR RME Agent — Development Configuration | INFO | Other_NonASCII |
| 842 | config\production.yaml | config_text | 1 | # OpenTibiaBR RME Agent — Production Configuration | INFO | Other_NonASCII |
| 843 | core\config_manager.py | other_non_ascii | 4 | ConfigManager — centralized configuration for Agente RME v1.0.0 GA. | INFO | Other_NonASCII |
| 844 | core\config_manager.py | comment | 38 | # Schema — minimal validation for top-level keys | WARNING | Other_NonASCII |
| 845 | core\config_manager.py | comment | 244 | # ── Helpers ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 846 | core\enterprise.py | other_non_ascii | 100 | match = re.search(r"(\d{2,4})\s*[-–to]+\s*(\d{2,4})", prompt) | INFO | Other_NonASCII |
| 847 | core\prompt_interpreter.py | other_non_ascii | 2 | MVP V0.1 — Prompt Interpreter | INFO | Other_NonASCII |
| 848 | core\prompt_interpreter.py | other_non_ascii | 93 | r"(?:nivel\|level)\s*(\d+)\s*[-–a]+\s*(\d+)", | INFO | Other_NonASCII |
| 849 | core\prompt_interpreter.py | other_non_ascii | 94 | r"(\d{2,4})\s*[-–]\s*(\d{2,4})", | INFO | Other_NonASCII |
| 850 | core\studio.py | other_non_ascii | 71 | on_error(f"Plan inválido: {errors}") | INFO | Latin_Extended |
| 851 | core\agents\agent_registry.py | docstring | 1 | """core.agents.agent_registry — Base agent class and registry.""" | WARNING | Other_NonASCII |
| 852 | core\agents\architect_agent.py | docstring | 1 | """core.agents.architect_agent — Real architect agent using core.architect.AIArchitect.""" | WARNING | Other_NonASCII |
| 853 | core\agents\balance_agent.py | docstring | 1 | """core.agents.balance_agent — Real balance agent.""" | WARNING | Other_NonASCII |
| 854 | core\agents\critic_agent.py | docstring | 1 | """core.agents.critic_agent — Real critic agent using core.critic.VisualCritic.""" | WARNING | Other_NonASCII |
| 855 | core\agents\expansion_agent.py | docstring | 1 | """core.agents.expansion_agent — Real expansion agent.""" | WARNING | Other_NonASCII |
| 856 | core\agents\export_agent.py | docstring | 1 | """core.agents.export_agent — Real export agent.""" | WARNING | Other_NonASCII |
| 857 | core\agents\mapper_agent.py | docstring | 1 | """core.agents.mapper_agent — Real mapper agent using AI mapper engines.""" | WARNING | Other_NonASCII |
| 858 | core\agents\orchestrator_agent.py | docstring | 1 | """core.agents.orchestrator_agent — Real orchestrator agent.""" | WARNING | Other_NonASCII |
| 859 | core\agents\playtest_agent.py | docstring | 1 | """core.agents.playtest_agent — Real playtest agent using core.playtest.PlaytestEngine.""" | WARNING | Other_NonASCII |
| 860 | core\agents\qa_agent.py | docstring | 1 | """core.agents.qa_agent — Real QA agent.""" | WARNING | Other_NonASCII |
| 861 | core\agents\quest_agent.py | docstring | 1 | """core.agents.quest_agent — Real quest agent using core.campaign.""" | WARNING | Other_NonASCII |
| 862 | core\agents\__init__.py | other_non_ascii | 2 | core.agents — Real multi-agent pipeline for Agente RME. | INFO | Other_NonASCII |
| 863 | core\analyzer\architecture_analyzer.py | other_non_ascii | 2 | HITO 12 — Architecture Analyzer: analiza la arquitectura del mapa: | INFO | Other_NonASCII |
| 864 | core\analyzer\architecture_analyzer.py | other_non_ascii | 3 | distribución de estructuras, ciudades, zonas, patrón de construcción. | INFO | Latin_Extended |
| 865 | core\analyzer\architecture_analyzer.py | other_non_ascii | 100 | Dict con análisis arquitectónico. | INFO | Latin_Extended |
| 866 | core\analyzer\architecture_analyzer.py | comment | 116 | # Composición estructural | WARNING | Latin_Extended |
| 867 | core\analyzer\architecture_analyzer.py | docstring | 121 | """Analiza la composición de tipos de suelo.""" | WARNING | Latin_Extended |
| 868 | core\analyzer\architecture_analyzer.py | comment | 185 | # Análisis de muros | WARNING | Latin_Extended |
| 869 | core\analyzer\architecture_analyzer.py | docstring | 190 | """Analiza la distribución de muros.""" | WARNING | Latin_Extended |
| 870 | core\analyzer\architecture_analyzer.py | comment | 212 | # Análisis de puertas | WARNING | Latin_Extended |
| 871 | core\analyzer\architecture_analyzer.py | docstring | 217 | """Analiza la distribución de puertas.""" | WARNING | Latin_Extended |
| 872 | core\analyzer\architecture_analyzer.py | comment | 239 | # Clasificación de edificios | WARNING | Latin_Extended |
| 873 | core\analyzer\architecture_analyzer.py | docstring | 248 | """Clasifica el tipo de construcción del mapa.""" | WARNING | Latin_Extended |
| 874 | core\analyzer\architecture_analyzer.py | comment | 323 | # Clasificación de zonas | WARNING | Latin_Extended |
| 875 | core\analyzer\architecture_analyzer.py | docstring | 333 | """Clasifica zonas del mapa en categorías.""" | WARNING | Latin_Extended |
| 876 | core\analyzer\architecture_analyzer.py | comment | 373 | # Métricas de complejidad | WARNING | Latin_Extended |
| 877 | core\analyzer\architecture_analyzer.py | docstring | 384 | """Calcula métricas de complejidad del mapa.""" | WARNING | Latin_Extended |
| 878 | core\analyzer\dataset_builder.py | other_non_ascii | 28 | raise ValueError(f"Categoría no soportada: {category}") | INFO | Latin_Extended |
| 879 | core\analyzer\density_analyzer.py | other_non_ascii | 2 | HITO 12 — Density Analyzer: analiza densidad de tiles, items, spawns | INFO | Other_NonASCII |
| 880 | core\analyzer\density_analyzer.py | other_non_ascii | 3 | y población en el mapa. | INFO | Latin_Extended |
| 881 | core\analyzer\density_analyzer.py | other_non_ascii | 31 | Dict con métricas de densidad. | INFO | Latin_Extended |
| 882 | core\analyzer\density_analyzer.py | comment | 53 | # Distribución por floors | WARNING | Latin_Extended |
| 883 | core\analyzer\density_analyzer.py | comment | 143 | # Zona de concentración | WARNING | Latin_Extended |
| 884 | core\analyzer\density_analyzer.py | comment | 151 | # Monstruos únicos | WARNING | Latin_Extended |
| 885 | core\analyzer\density_analyzer.py | docstring | 217 | """Distribución de spawns por floor.""" | WARNING | Latin_Extended |
| 886 | core\analyzer\density_analyzer.py | docstring | 254 | """Categoriza la densidad según score.""" | WARNING | Latin_Extended |
| 887 | core\analyzer\map_analyzer.py | other_non_ascii | 2 | HITO 12 — Map Analyzer: analiza tiles, items, spawns, houses y waypoints | INFO | Other_NonASCII |
| 888 | core\analyzer\map_analyzer.py | docstring | 30 | """Resultado completo de análisis de un mapa.""" | WARNING | Latin_Extended |
| 889 | core\analyzer\map_analyzer.py | docstring | 50 | """Exporta el análisis como diccionario serializable a JSON.""" | WARNING | Latin_Extended |
| 890 | core\analyzer\map_analyzer.py | other_non_ascii | 82 | otbm_importer: Instancia opcional de OTBMImporter para análisis OTBM completo. | INFO | Latin_Extended |
| 891 | core\analyzer\map_analyzer.py | other_non_ascii | 83 | Si no se proporciona, se usará análisis básico de bytes. | INFO | Latin_Extended |
| 892 | core\analyzer\map_analyzer.py | comment | 115 | # Ejecutar análisis derivados | WARNING | Latin_Extended |
| 893 | core\analyzer\map_analyzer.py | comment | 121 | # Análisis OTBM (usando pipeline completo cuando esté disponible) | WARNING | Latin_Extended |
| 894 | core\analyzer\map_analyzer.py | docstring | 134 | """Análisis usando OTBMImporter + NodeDecoder para extracción completa.""" | WARNING | Latin_Extended |
| 895 | core\analyzer\map_analyzer.py | comment | 177 | # Patrón | WARNING | Latin_Extended |
| 896 | core\analyzer\map_analyzer.py | comment | 190 | # Fallback a análisis directo | WARNING | Latin_Extended |
| 897 | core\analyzer\map_analyzer.py | docstring | 195 | """Análisis directo de bytes OTBM (fallback sin importer).""" | WARNING | Latin_Extended |
| 898 | core\analyzer\map_analyzer.py | docstring | 239 | """Extrae estadísticas de tiles e items desde world_dict.""" | WARNING | Latin_Extended |
| 899 | core\analyzer\map_analyzer.py | comment | 265 | # Análisis XML | WARNING | Latin_Extended |
| 900 | core\analyzer\map_analyzer.py | comment | 273 | # Tamaño del mapa | WARNING | Latin_Extended |
| 901 | core\analyzer\map_analyzer.py | comment | 317 | # Análisis derivados (path, density, architecture) | WARNING | Latin_Extended |
| 902 | core\analyzer\map_analyzer.py | docstring | 321 | """Ejecuta análisis derivados: path, density, architecture.""" | WARNING | Latin_Extended |
| 903 | core\analyzer\map_analyzer.py | comment | 353 | # Métodos de extracción binaria mejorados | WARNING | Latin_Extended |
| 904 | core\analyzer\map_analyzer.py | docstring | 358 | """Lee un archivo como bytes, retorna vacío si no existe.""" | WARNING | Latin_Extended |
| 905 | core\analyzer\map_analyzer.py | docstring | 365 | """Extrae tiles desde binario con detección mejorada.""" | WARNING | Latin_Extended |
| 906 | core\analyzer\map_analyzer.py | comment | 500 | # Métodos de extracción XML (mantenidos e igualados) | WARNING | Latin_Extended |
| 907 | core\analyzer\map_analyzer.py | docstring | 567 | """Normaliza waypoints a formato estándar.""" | WARNING | Latin_Extended |
| 908 | core\analyzer\map_analyzer.py | comment | 621 | # Helpers a nivel módulo | WARNING | Latin_Extended |
| 909 | core\analyzer\path_analyzer.py | other_non_ascii | 2 | HITO 12 — Path Analyzer: analiza rutas, conectividad y distancias | INFO | Other_NonASCII |
| 910 | core\analyzer\path_analyzer.py | other_non_ascii | 3 | entre waypoints, spawns y puntos de interés en un mapa. | INFO | Latin_Extended |
| 911 | core\analyzer\path_analyzer.py | other_non_ascii | 28 | Dict con análisis de rutas. | INFO | Latin_Extended |
| 912 | core\analyzer\path_analyzer.py | comment | 60 | # Cálculos de distancia | WARNING | Latin_Extended |
| 913 | core\analyzer\path_analyzer.py | docstring | 114 | """Encuentra el waypoint más cercano para cada spawn.""" | WARNING | Latin_Extended |
| 914 | core\analyzer\path_analyzer.py | comment | 192 | # Resúmenes | WARNING | Latin_Extended |
| 915 | core\analyzer\path_analyzer.py | docstring | 214 | """Encuentra el par de waypoints más distantes.""" | WARNING | Latin_Extended |
| 916 | core\analyzer\path_analyzer.py | docstring | 222 | """Encuentra el par de waypoints más cercanos.""" | WARNING | Latin_Extended |
| 917 | core\analyzer\path_analyzer.py | other_non_ascii | 240 | max_distance: Distancia máxima para agrupar. | INFO | Latin_Extended |
| 918 | core\analyzer\spawn_analyzer.py | other_non_ascii | 2 | HITO 12 — Spawn Analyzer: analiza spawns desde .otbm (vía pipeline) y .xml. | INFO | Other_NonASCII, Latin_Extended |
| 919 | core\analyzer\spawn_analyzer.py | other_non_ascii | 3 | Soporta análisis binario directo y vía OTBMImporter/NodeDecoder. | INFO | Latin_Extended |
| 920 | core\analyzer\spawn_analyzer.py | comment | 29 | # Análisis desde OTBM (world_dict) | WARNING | Latin_Extended |
| 921 | core\analyzer\spawn_analyzer.py | other_non_ascii | 33 | """Analiza spawns desde lista extraída del world_dict. | INFO | Latin_Extended |
| 922 | core\analyzer\spawn_analyzer.py | comment | 64 | # Análisis OTBM directo (bytes) | WARNING | Latin_Extended |
| 923 | core\analyzer\spawn_analyzer.py | comment | 96 | # Buscar hijos MONSTER dentro del área | WARNING | Latin_Extended |
| 924 | core\analyzer\spawn_analyzer.py | comment | 150 | # Análisis XML | WARNING | Latin_Extended |
| 925 | core\analyzer\spawn_analyzer.py | comment | 182 | # Clasificación y agregación | WARNING | Latin_Extended |
| 926 | core\analyzer\spawn_analyzer.py | docstring | 200 | """Genera resumen estadístico de spawns.""" | WARNING | Latin_Extended |
| 927 | core\architect\ai_architect.py | other_non_ascii | 14 | ↓ | INFO | Other_NonASCII |
| 928 | core\architect\ai_architect.py | other_non_ascii | 16 | ↓ | INFO | Other_NonASCII |
| 929 | core\architect\ai_architect.py | other_non_ascii | 18 | ↓ | INFO | Other_NonASCII |
| 930 | core\architect\architect.py | other_non_ascii | 38 | Responde: "¿Qué debería existir aquí?" ANTES de "¿Qué tile colocar aquí?" | INFO | Other_NonASCII, Latin_Extended |
| 931 | core\architect\architect.py | other_non_ascii | 41 | Prompt → Style Detection → Design Rules → Zone Decisions → Rationale | INFO | Other_NonASCII |
| 932 | core\architect\architect.py | other_non_ascii | 110 | question="¿Qué estrategia de layout usar?", | INFO | Other_NonASCII, Latin_Extended |
| 933 | core\architect\architect.py | other_non_ascii | 111 | answer="Simétrica radial", | INFO | Latin_Extended |
| 934 | core\architect\architect.py | other_non_ascii | 120 | question="¿Qué estrategia de layout usar?", | INFO | Other_NonASCII, Latin_Extended |
| 935 | core\architect\architect.py | other_non_ascii | 121 | answer="Orgánica natural", | INFO | Latin_Extended |
| 936 | core\architect\architect.py | other_non_ascii | 124 | alternatives=["Simétrica radial", "Grid-based"], | INFO | Latin_Extended |
| 937 | core\architect\architect.py | other_non_ascii | 130 | question="¿Qué estrategia de layout usar?", | INFO | Other_NonASCII, Latin_Extended |
| 938 | core\architect\architect.py | other_non_ascii | 134 | alternatives=["Simétrica radial", "Orgánica"], | INFO | Latin_Extended |
| 939 | core\architect\architect.py | other_non_ascii | 141 | question="¿Cuántas zonas crear?", | INFO | Other_NonASCII, Latin_Extended |
| 940 | core\architect\architect.py | other_non_ascii | 154 | question="¿Cuántos pisos usar?", | INFO | Other_NonASCII, Latin_Extended |
| 941 | core\architect\architect.py | other_non_ascii | 164 | question="¿Cuántos pisos usar?", | INFO | Other_NonASCII, Latin_Extended |
| 942 | core\architect\architect.py | other_non_ascii | 166 | reason="Three floors provides good progression: entrance → combat → boss.", | INFO | Other_NonASCII |
| 943 | core\architect\architect.py | other_non_ascii | 175 | question="¿Cómo distribuir los spawns?", | INFO | Other_NonASCII, Latin_Extended |
| 944 | core\architect\architect.py | other_non_ascii | 176 | answer="Alta densidad con progresión", | INFO | Latin_Extended |
| 945 | core\architect\architect.py | other_non_ascii | 185 | question="¿Cómo distribuir los spawns?", | INFO | Other_NonASCII, Latin_Extended |
| 946 | core\architect\architect.py | other_non_ascii | 196 | question="¿Qué evitar en el diseño?", | INFO | Other_NonASCII, Latin_Extended |
| 947 | core\architect\architect.py | other_non_ascii | 197 | answer=f"{len(avoids)} patrones anti-diseño", | INFO | Latin_Extended |
| 948 | core\architect\architect.py | other_non_ascii | 208 | question="¿Dónde colocar la entrada?", | INFO | Other_NonASCII, Latin_Extended |
| 949 | core\architect\architect.py | other_non_ascii | 219 | question="¿Dónde colocar el boss room?", | INFO | Other_NonASCII, Latin_Extended |
| 950 | core\architect\architect.py | other_non_ascii | 220 | answer="Último piso, punto más alejado de la entrada", | INFO | Latin_Extended |
| 951 | core\architect\architect.py | other_non_ascii | 312 | Example: "¿Por qué este templo está aquí?" | INFO | Other_NonASCII, Latin_Extended |
| 952 | core\architect\architect.py | other_non_ascii | 316 | return f"Decisión: {decision.answer}\nRazón: {decision.reason}" | INFO | Latin_Extended |
| 953 | core\architect\architect.py | other_non_ascii | 319 | f"las decisiones se basan en reglas de diseño que priorizan " | INFO | Latin_Extended |
| 954 | core\architect\architect.py | other_non_ascii | 320 | f"{'funcionalidad urbana' if rationale.map_type == 'city' else 'progresión de dificultad' if rationale.map_type == 'dungeon' else 'flujo de caza óptim | INFO | Latin_Extended |
| 955 | core\architect\composition_engine.py | other_non_ascii | 25 | 70% Issavi + 30% Roshamuul  → open+dark hybrid | INFO | Other_NonASCII |
| 956 | core\architect\composition_engine.py | other_non_ascii | 26 | 50% Library + 50% Soul War   → ornate+dark hybrid | INFO | Other_NonASCII |
| 957 | core\architect\design_rules.py | other_non_ascii | 42 | Responde: "¿Qué debería existir aquí?" | INFO | Other_NonASCII, Latin_Extended |
| 958 | core\architect\difficulty_planner.py | other_non_ascii | 2 | HITO 15 — AI Architect: Difficulty Planner | INFO | Other_NonASCII |
| 959 | core\architect\difficulty_planner.py | other_non_ascii | 8 | they should escalate smoothly: warmup hunts → mid hunts → elite hunts → boss. | INFO | Other_NonASCII |
| 960 | core\architect\difficulty_planner.py | other_non_ascii | 23 | ↓ | INFO | Other_NonASCII |
| 961 | core\architect\difficulty_planner.py | other_non_ascii | 25 | ↓ | INFO | Other_NonASCII |
| 962 | core\architect\difficulty_planner.py | other_non_ascii | 27 | ├── zone_kind: str | INFO | Other_NonASCII |
| 963 | core\architect\difficulty_planner.py | other_non_ascii | 28 | ├── level_min: int | INFO | Other_NonASCII |
| 964 | core\architect\difficulty_planner.py | other_non_ascii | 29 | ├── level_max: int | INFO | Other_NonASCII |
| 965 | core\architect\difficulty_planner.py | other_non_ascii | 30 | ├── band: str   ("easy" \| "medium" \| ... \| "legendary") | INFO | Other_NonASCII |
| 966 | core\architect\difficulty_planner.py | other_non_ascii | 31 | ├── spawn_density: str  ("low" \| "medium" \| "high" \| "extreme") | INFO | Other_NonASCII |
| 967 | core\architect\difficulty_planner.py | other_non_ascii | 32 | └── monster_subset: List[str] | INFO | Other_NonASCII |
| 968 | core\architect\difficulty_planner.py | comment | 56 | # ZoneDifficulty — one window in a multi-zone progression | WARNING | Other_NonASCII |
| 969 | core\architect\difficulty_planner.py | other_non_ascii | 372 | notes.append(f"Final encounter — band={band} with boss mechanics") | INFO | Other_NonASCII |
| 970 | core\architect\difficulty_planner.py | other_non_ascii | 376 | notes.append("Safe zone — low monster density") | INFO | Other_NonASCII |
| 971 | core\architect\layout_engine.py | other_non_ascii | 36 | Decides DÓNDE construir, QUÉ construir, y QUÉ evitar. | INFO | Latin_Extended |
| 972 | core\architect\layout_engine.py | other_non_ascii | 40 | This is the architectural "blueprint" phase — no tiles yet. | INFO | Other_NonASCII |
| 973 | core\architect\layout_planner.py | other_non_ascii | 2 | HITO 15 — AI Architect: Layout Planner | INFO | Other_NonASCII |
| 974 | core\architect\layout_planner.py | other_non_ascii | 22 | ↓ | INFO | Other_NonASCII |
| 975 | core\architect\layout_planner.py | other_non_ascii | 24 | ↓ | INFO | Other_NonASCII |
| 976 | core\architect\layout_planner.py | other_non_ascii | 26 | ├── zones:  List[PlacedZone] | INFO | Other_NonASCII |
| 977 | core\architect\layout_planner.py | other_non_ascii | 27 | ├── roads:  List[Dict] | INFO | Other_NonASCII |
| 978 | core\architect\layout_planner.py | other_non_ascii | 28 | ├── teleports: List[Dict] | INFO | Other_NonASCII |
| 979 | core\architect\layout_planner.py | other_non_ascii | 29 | ├── waypoints: List[Dict] | INFO | Other_NonASCII |
| 980 | core\architect\layout_planner.py | other_non_ascii | 30 | └── bounds: Tuple[int, int, int, int] | INFO | Other_NonASCII |
| 981 | core\architect\layout_planner.py | comment | 43 | # PlacedZone — a zone plus its concrete position inside the world | WARNING | Other_NonASCII |
| 982 | core\architect\layout_planner.py | comment | 84 | # WorldLayout — the complete spatial arrangement | WARNING | Other_NonASCII |
| 983 | core\architect\mapper_ai.py | other_non_ascii | 31 | Prompt → Architect → DesignRules → StyleEngine → LayoutEngine → WorldPlan | INFO | Other_NonASCII |
| 984 | core\architect\mapper_ai.py | other_non_ascii | 150 | "¿Por qué este templo está aquí?" | INFO | Other_NonASCII, Latin_Extended |
| 985 | core\architect\mapper_ai.py | other_non_ascii | 151 | "¿Por qué esta hunt funciona?" | INFO | Other_NonASCII, Latin_Extended |
| 986 | core\architect\mapper_ai.py | other_non_ascii | 187 | lines.append("POR QUÉ ESTE DISEÑO:") | INFO | Latin_Extended |
| 987 | core\architect\mapper_ai.py | other_non_ascii | 190 | lines.append("POR QUÉ ESTE ESTILO:") | INFO | Latin_Extended |
| 988 | core\architect\mapper_ai.py | other_non_ascii | 193 | lines.append("POR QUÉ ESTAS ZONAS:") | INFO | Latin_Extended |
| 989 | core\architect\mapper_ai.py | other_non_ascii | 204 | lines.append(f"     Razón: {dec.reason}") | INFO | Latin_Extended |
| 990 | core\architect\mapper_ai.py | other_non_ascii | 209 | lines.append("COMPOSICIÓN DE ESTILOS:") | INFO | Latin_Extended |
| 991 | core\architect\mapper_ai.py | other_non_ascii | 212 | lines.append(f"  Descripción: {decision.composition.description}") | INFO | Latin_Extended |
| 992 | core\architect\mapper_ai.py | other_non_ascii | 218 | lines.append(f"     Posición: ({z.position[0]}, {z.position[1]})") | INFO | Latin_Extended |
| 993 | core\architect\mapper_ai.py | other_non_ascii | 219 | lines.append(f"     Tamaño: {z.size[0]}x{z.size[1]}") | INFO | Latin_Extended |
| 994 | core\architect\mapper_ai.py | other_non_ascii | 220 | lines.append(f"     Propósito: {z.zone.purpose}") | INFO | Latin_Extended |
| 995 | core\architect\mapper_ai.py | other_non_ascii | 221 | lines.append(f"     Razón: {z.reason}") | INFO | Latin_Extended |
| 996 | core\architect\theme_resolver.py | other_non_ascii | 2 | HITO 15 — AI Architect: Theme Resolver | INFO | Other_NonASCII |
| 997 | core\architect\theme_resolver.py | other_non_ascii | 19 | ↓ | INFO | Other_NonASCII |
| 998 | core\architect\theme_resolver.py | other_non_ascii | 21 | ↓ | INFO | Other_NonASCII |
| 999 | core\architect\theme_resolver.py | other_non_ascii | 23 | ├── grounds: [415, 393, ...] | INFO | Other_NonASCII |
| 1000 | core\architect\theme_resolver.py | other_non_ascii | 24 | ├── walls:   [1495, 1496, ...] | INFO | Other_NonASCII |
| 1001 | core\architect\theme_resolver.py | other_non_ascii | 25 | ├── decorations: [2153, 2117, ...] | INFO | Other_NonASCII |
| 1002 | core\architect\theme_resolver.py | other_non_ascii | 26 | ├── monsters: ["Frazzlemaw", ...] | INFO | Other_NonASCII |
| 1003 | core\architect\theme_resolver.py | other_non_ascii | 27 | ├── blueprints: {temple: {...}, depot: {...}} | INFO | Other_NonASCII |
| 1004 | core\architect\theme_resolver.py | other_non_ascii | 28 | └── metadata: {biome, era, difficulty, ...} | INFO | Other_NonASCII |
| 1005 | core\architect\theme_resolver.py | other_non_ascii | 33 | resolve_theme(name) → ThemeAssets | INFO | Other_NonASCII |
| 1006 | core\architect\theme_resolver.py | other_non_ascii | 34 | resolve_themes([...]) → [ThemeAssets, ...] | INFO | Other_NonASCII |
| 1007 | core\architect\theme_resolver.py | other_non_ascii | 35 | merge_themes([...]) → ThemeAssets | INFO | Other_NonASCII |
| 1008 | core\architect\theme_resolver.py | comment | 47 | # ThemeAssets — value object returned by the resolver | WARNING | Other_NonASCII |
| 1009 | core\architect\theme_resolver.py | other_non_ascii | 769 | (theme-prefixed names like "issavi_temple" → structure_type "temple"). | INFO | Other_NonASCII |
| 1010 | core\architect\world_planner.py | other_non_ascii | 66 | m = re.search(r"(?:level\|nivel)\s*(\d+)\s*[-–]\s*(\d+)", lower) | INFO | Other_NonASCII |
| 1011 | core\architect\world_planner.py | other_non_ascii | 91 | if "quest" in lower or "mision" in lower or "misión" in lower: | INFO | Latin_Extended |
| 1012 | core\architect\zone_planner.py | other_non_ascii | 2 | HITO 15 — AI Architect: Zone Planner | INFO | Other_NonASCII |
| 1013 | core\architect\zone_planner.py | other_non_ascii | 19 | ↓ | INFO | Other_NonASCII |
| 1014 | core\architect\zone_planner.py | other_non_ascii | 21 | ↓ | INFO | Other_NonASCII |
| 1015 | core\assets\asset_cache.py | other_non_ascii | 2 | AssetCache — Cachea datos indexados en disco para evitar reindexar cada ejecución. | INFO | Other_NonASCII, Latin_Extended |
| 1016 | core\assets\asset_classifier.py | other_non_ascii | 305 | 'ground' → ['nature', 'decoration'] | INFO | Other_NonASCII |
| 1017 | core\assets\asset_classifier.py | other_non_ascii | 306 | 'wall' → ['decoration', 'light_source'] | INFO | Other_NonASCII |
| 1018 | core\assets\asset_indexer.py | other_non_ascii | 81 | - items.xml  → IndexedItem entries | INFO | Other_NonASCII |
| 1019 | core\assets\asset_indexer.py | other_non_ascii | 82 | - monsters/  → IndexedMonster entries | INFO | Other_NonASCII |
| 1020 | core\assets\asset_indexer.py | other_non_ascii | 83 | - NPC files  → basic NPC registry | INFO | Other_NonASCII |
| 1021 | core\assets\asset_indexer.py | other_non_ascii | 84 | - Theme templates → theme-to-item associations | INFO | Other_NonASCII |
| 1022 | core\assets\asset_indexer.py | comment | 270 | self._theme_items: Dict[str, Set[int]] = {}  # theme → set of item IDs | WARNING | Other_NonASCII |
| 1023 | core\assets\asset_indexer.py | comment | 271 | self._theme_monsters: Dict[str, Set[str]] = {}  # theme → set of monster names | WARNING | Other_NonASCII |
| 1024 | core\assets\asset_recommender.py | other_non_ascii | 58 | - "¿Qué decoración combina con Issavi?" | INFO | Other_NonASCII, Latin_Extended |
| 1025 | core\assets\asset_recommender.py | other_non_ascii | 59 | - "¿Qué paredes se parecen a Roshamuul?" | INFO | Other_NonASCII, Latin_Extended |
| 1026 | core\assets\asset_recommender.py | other_non_ascii | 60 | - "Recomiéndame grounds para una ciudad jungla" | INFO | Latin_Extended |
| 1027 | core\assets\asset_recommender.py | other_non_ascii | 61 | - "¿Qué antorchas usar para un templo oscuro?" | INFO | Other_NonASCII, Latin_Extended |
| 1028 | core\assets\asset_recommender.py | other_non_ascii | 65 | Indexer → Classifier → Similarity → Recommender | INFO | Other_NonASCII |
| 1029 | core\assets\asset_recommender.py | other_non_ascii | 80 | "decoración": "decorate_for", | INFO | Latin_Extended |
| 1030 | core\assets\asset_recommender.py | other_non_ascii | 95 | "iluminación": "light_for", | INFO | Latin_Extended |
| 1031 | core\assets\asset_recommender.py | other_non_ascii | 120 | recommender.recommend("¿Qué decoración combina con Issavi?") | INFO | Other_NonASCII, Latin_Extended |
| 1032 | core\assets\asset_recommender.py | other_non_ascii | 121 | recommender.recommend("¿Qué paredes se parecen a Roshamuul?") | INFO | Other_NonASCII, Latin_Extended |
| 1033 | core\assets\asset_recommender.py | other_non_ascii | 122 | recommender.recommend("Recomiéndame grounds para una ciudad jungla") | INFO | Latin_Extended |
| 1034 | core\assets\asset_recommender.py | other_non_ascii | 189 | "decoración": "decoration", | INFO | Latin_Extended |
| 1035 | core\assets\asset_registry.py | other_non_ascii | 2 | AssetRegistry — Fuente de verdad única para items, monsters y NPCs. | INFO | Other_NonASCII, Latin_Extended |
| 1036 | core\assets\asset_similarity.py | other_non_ascii | 53 | 1. Category match (ground→ground, wall→wall, etc.) | INFO | Other_NonASCII |
| 1037 | core\assets\asset_similarity.py | other_non_ascii | 169 | find_compatible(stone_wall, "decoration") → torches, banners, etc. | INFO | Other_NonASCII |
| 1038 | core\assets\item_indexer.py | other_non_ascii | 2 | ItemIndexer — Indexa items de Tibia desde items.xml o lista conocida. | INFO | Other_NonASCII |
| 1039 | core\assets\monster_indexer.py | other_non_ascii | 2 | MonsterIndexer — Indexa monstruos de Tibia desde monster.xml o lista conocida. | INFO | Other_NonASCII |
| 1040 | core\assets\monster_indexer.py | comment | 10 | # Fallback monsters — usados si no hay monster.xml disponible | WARNING | Other_NonASCII |
| 1041 | core\assets\npc_indexer.py | other_non_ascii | 2 | NpcIndexer — Indexa NPCs de Tibia desde npc.xml o lista conocida. | INFO | Other_NonASCII |
| 1042 | core\autonomous\autonomous_decision_engine.py | other_non_ascii | 2 | Autonomous Decision Engine — selects blueprints, patterns, clusters and | INFO | Other_NonASCII |
| 1043 | core\autonomous\autonomous_decision_engine.py | other_non_ascii | 7 | * ``KnowledgeEngine`` — entry similarity & search. | INFO | Other_NonASCII |
| 1044 | core\autonomous\autonomous_decision_engine.py | other_non_ascii | 8 | * ``BlueprintIntelligenceEngine`` — embedding-based recommendations. | INFO | Other_NonASCII |
| 1045 | core\autonomous\autonomous_decision_engine.py | other_non_ascii | 9 | * ``EvolutionEngine`` — to bias decisions based on recent critic | INFO | Other_NonASCII |
| 1046 | core\autonomous\autonomous_decision_engine.py | comment | 33 | # ── Score weights for the multi-objective ranking ────────────────────────── | WARNING | Other_NonASCII |
| 1047 | core\autonomous\autonomous_director.py | other_non_ascii | 2 | Autonomous Director — decides what to build and how to build it. | INFO | Other_NonASCII |
| 1048 | core\autonomous\autonomous_director.py | other_non_ascii | 11 | * ``KnowledgeEngine`` — to retrieve similar hunts, cities, boss rooms, … | INFO | Other_NonASCII |
| 1049 | core\autonomous\autonomous_director.py | other_non_ascii | 12 | * ``BlueprintIntelligenceEngine`` — to recommend blueprints and patterns. | INFO | Other_NonASCII |
| 1050 | core\autonomous\autonomous_director.py | other_non_ascii | 13 | * ``VisualCritic`` — to bias decisions based on previous critic outcomes. | INFO | Other_NonASCII |
| 1051 | core\autonomous\autonomous_director.py | comment | 35 | # ── Theme → archetype hints used by the heuristics ────────────────────────── | WARNING | Other_NonASCII |
| 1052 | core\autonomous\autonomous_director.py | other_non_ascii | 227 | m = re.search(r"(?:nivel\|level)\s*(\d+)\s*[-–]\s*(\d+)", text) | INFO | Other_NonASCII |
| 1053 | core\autonomous\autonomous_director.py | comment | 231 | # "level 300" → ± 50 | WARNING | Other_NonASCII |
| 1054 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 2 | Autonomous Optimizer — runs the iterative design loop. | INFO | Other_NonASCII |
| 1055 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 6 | generate → critic → evaluate → improve → repeat | INFO | Other_NonASCII |
| 1056 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 10 | * :class:`core.critic.VisualCritic` — overall critic score. | INFO | Other_NonASCII |
| 1057 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 11 | * :class:`core.playtest.PlaytestEngine` — playability & quality. | INFO | Other_NonASCII |
| 1058 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 12 | * :class:`core.balance.BalanceEngine` — balance, XP, loot, difficulty. | INFO | Other_NonASCII |
| 1059 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 13 | * :class:`core.evolution.MapEvolver` — quality-driven improvement. | INFO | Other_NonASCII |
| 1060 | core\autonomous\autonomous_optimizer.py | other_non_ascii | 14 | * :class:`core.otbm.OTBMExporter` — final export to .otbm. | INFO | Other_NonASCII |
| 1061 | core\autonomous\autonomous_optimizer.py | comment | 83 | # Engine references (to be injected) — these are optional and lazily created. | WARNING | Other_NonASCII |
| 1062 | core\autonomous\autonomous_optimizer.py | comment | 116 | # ── 1. Generate world from the current plan ───────────────────── | WARNING | Other_NonASCII |
| 1063 | core\autonomous\autonomous_optimizer.py | comment | 119 | # ── 2. Evaluate (critic + playtest + balance) ────────────────── | WARNING | Other_NonASCII |
| 1064 | core\autonomous\autonomous_optimizer.py | comment | 122 | # ── 3. Record iteration ──────────────────────────────────────── | WARNING | Other_NonASCII |
| 1065 | core\autonomous\autonomous_optimizer.py | comment | 136 | # ── 4. Check stop conditions ─────────────────────────────────── | WARNING | Other_NonASCII |
| 1066 | core\autonomous\autonomous_optimizer.py | comment | 140 | # ── 5. Improve the plan for the next iteration ───────────────── | WARNING | Other_NonASCII |
| 1067 | core\autonomous\autonomous_visualizer.py | other_non_ascii | 2 | Autonomous Visualizer — produces matplotlib visualisations of the | INFO | Other_NonASCII |
| 1068 | core\autonomous\autonomous_visualizer.py | other_non_ascii | 9 | * ``iteration_scores.png`` — bar chart of every per-iteration score | INFO | Other_NonASCII |
| 1069 | core\autonomous\autonomous_visualizer.py | other_non_ascii | 10 | * ``critic_progress.png``  — line chart of the critic score across | INFO | Other_NonASCII |
| 1070 | core\autonomous\autonomous_visualizer.py | other_non_ascii | 12 | * ``optimization_curve.png`` — combined plot of all five scores | INFO | Other_NonASCII |
| 1071 | core\autonomous\autonomous_visualizer.py | other_non_ascii | 66 | ax.set_title(f"Per-iteration scores — result {result.result_id[:8]}") | INFO | Other_NonASCII |
| 1072 | core\autonomous\autonomous_world_designer.py | other_non_ascii | 2 | Autonomous World Designer — main façade for autonomous world generation. | INFO | Other_NonASCII, Latin_Extended |
| 1073 | core\autonomous\autonomous_world_designer.py | comment | 32 | # ── Lazy subsystem imports (kept optional for testability) ────────────────── | WARNING | Other_NonASCII |
| 1074 | core\autonomous\autonomous_world_designer.py | docstring | 46 | """Main façade for autonomous world generation.""" | WARNING | Latin_Extended |
| 1075 | core\autonomous\goal_manager.py | comment | 71 | # Don't trigger convergence-based stop too early — let the loop | WARNING | Other_NonASCII |
| 1076 | core\balance\balance_engine.py | comment | 105 | # No regions — balance globally using all spawns as one zone | WARNING | Other_NonASCII |
| 1077 | core\balance\difficulty_analyzer.py | other_non_ascii | 128 | monster_difficulties: Dict mapping monster name → difficulty. | INFO | Other_NonASCII |
| 1078 | core\balance\difficulty_analyzer.py | comment | 379 | # Zone is too hard → reduce difficulty | WARNING | Other_NonASCII |
| 1079 | core\balance\difficulty_analyzer.py | comment | 396 | # Zone is too easy → increase difficulty | WARNING | Other_NonASCII |
| 1080 | core\balance\loot_analyzer.py | other_non_ascii | 108 | loot_tables: Dict mapping monster name → list of loot entries. | INFO | Other_NonASCII |
| 1081 | core\balance\loot_analyzer.py | other_non_ascii | 110 | monster_difficulties: Dict mapping monster name → difficulty. | INFO | Other_NonASCII |
| 1082 | core\balance\loot_balancer.py | comment | 11 | # Loot table reference: monster → list of drops | WARNING | Other_NonASCII |
| 1083 | core\balance\loot_balancer.py | other_non_ascii | 147 | loot_tables: Loot table dict (monster → drops). | INFO | Other_NonASCII |
| 1084 | core\balance\xp_analyzer.py | comment | 12 | xp_per_kill: Dict[str, int] = field(default_factory=dict)  # monster → XP | WARNING | Other_NonASCII |
| 1085 | core\balance\xp_analyzer.py | other_non_ascii | 91 | monsters: Dict mapping monster name → XP value. | INFO | Other_NonASCII |
| 1086 | core\blueprints\blueprint_extractor.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 1087 | core\blueprints\blueprint_extractor.py | other_non_ascii | 2 | HITO 13 â€” Blueprint Extractor: orquesta todo el pipeline de extraccion | INFO | Other_NonASCII, Latin_Extended |
| 1088 | core\blueprints\blueprint_extractor.py | other_non_ascii | 3 | de blueprints desde datos OTBM â†’ WorldModel â†’ Blueprint. | INFO | Other_NonASCII, Latin_Extended |
| 1089 | core\blueprints\blueprint_extractor.py | other_non_ascii | 6 | 1. OTBM Importer: lee .otbm â†’ WorldModel dict | INFO | Other_NonASCII, Latin_Extended |
| 1090 | core\blueprints\blueprint_extractor.py | other_non_ascii | 71 | OTBM â†’ WorldModel â†’ Blueprint | INFO | Other_NonASCII, Latin_Extended |
| 1091 | core\blueprints\blueprint_extractor.py | other_non_ascii | 96 | Pipeline completo: OTBM â†’ WorldModel â†’ MapAnalysis â†’ Blueprint. | INFO | Other_NonASCII, Latin_Extended |
| 1092 | core\blueprints\blueprint_extractor.py | comment | 114 | # 1. Importar OTBM â†’ WorldModel dict | WARNING | Other_NonASCII, Latin_Extended |
| 1093 | core\blueprints\blueprint_mixer.py | comment | 16 | mix_ratio: Tuple[float, float]  # e.g., (0.6, 0.4) → 60% A, 40% B | WARNING | Other_NonASCII |
| 1094 | core\blueprints\blueprint_mixer.py | other_non_ascii | 200 | f"Blueprint híbrido: {base_category} con tema {theme_a} " f"fusionado con {theme_b}" | INFO | Latin_Extended |
| 1095 | core\blueprints\blueprint_mixer.py | comment | 232 | # Default: overlay — B's theme layered onto A's structure | WARNING | Other_NonASCII |
| 1096 | core\blueprints\blueprint_registry.py | comment | 70 | # Query API — the main interface | WARNING | Other_NonASCII |
| 1097 | core\blueprints\blueprint_search.py | comment | 56 | # Keyword → category mapping for Spanish and English | WARNING | Other_NonASCII |
| 1098 | core\blueprints\blueprint_search.py | other_non_ascii | 66 | "depósito": "depot", | INFO | Latin_Extended |
| 1099 | core\blueprints\blueprint_search.py | other_non_ascii | 85 | "cacería": "hunt", | INFO | Latin_Extended |
| 1100 | core\blueprints\blueprint_search.py | other_non_ascii | 108 | "pequeño", | INFO | Latin_Extended |
| 1101 | core\blueprints\blueprint_search.py | other_non_ascii | 141 | "prisión": "roshamuul", | INFO | Latin_Extended |
| 1102 | core\blueprints\blueprint_search.py | comment | 147 | self._blueprints: Dict[str, List[Dict[str, Any]]] = {}  # category → [blueprints] | WARNING | Other_NonASCII |
| 1103 | core\blueprints\blueprint_search.py | other_non_ascii | 189 | "Quiero un puente estilo roshamuul pequeño" | INFO | Latin_Extended |
| 1104 | core\blueprints\blueprint_search.py | other_non_ascii | 254 | "balcón", | INFO | Latin_Extended |
| 1105 | core\blueprints\blueprint_search.py | other_non_ascii | 323 | reasons.append(f"Categoría '{category}' coincide") | INFO | Latin_Extended |
| 1106 | core\blueprints\blueprint_search.py | other_non_ascii | 337 | reasons.append(f"Tamaño grande ({area} tiles²)") | INFO | Other_NonASCII, Latin_Extended |
| 1107 | core\blueprints\blueprint_search.py | other_non_ascii | 339 | elif sk in ("pequeño", "pequeno", "small", "tiny", "chico") and area <= 200: | INFO | Latin_Extended |
| 1108 | core\blueprints\blueprint_search.py | other_non_ascii | 341 | reasons.append(f"Tamaño pequeño ({area} tiles²)") | INFO | Other_NonASCII, Latin_Extended |
| 1109 | core\blueprints\blueprint_search.py | other_non_ascii | 345 | reasons.append(f"Tamaño mediano ({area} tiles²)") | INFO | Other_NonASCII, Latin_Extended |
| 1110 | core\blueprints\pattern_detector.py | other_non_ascii | 2 | HITO 13 — Pattern Detector: detecta patrones constructivos repetitivos | INFO | Other_NonASCII |
| 1111 | core\blueprints\structure_detector.py | other_non_ascii | 2 | HITO 13 — Structure Detector: detecta estructuras constructivas complejas | INFO | Other_NonASCII |
| 1112 | core\blueprints\theme_classifier.py | other_non_ascii | 2 | HITO 13 — Theme Classifier: clasifica el tema/estilo de un mapa | INFO | Other_NonASCII |
| 1113 | core\blueprints\__init__.py | comment | 11 | # HITO 13 — Blueprint Extractor pipeline | WARNING | Other_NonASCII |
| 1114 | core\blueprints\__init__.py | comment | 35 | # HITO 13 — Extractor pipeline | WARNING | Other_NonASCII |
| 1115 | core\blueprint_intelligence\blueprint_embedding_engine.py | other_non_ascii | 2 | BlueprintEmbeddingEngine — converts any blueprint to a vector embedding. | INFO | Other_NonASCII |
| 1116 | core\blueprint_intelligence\blueprint_evolution_engine.py | other_non_ascii | 2 | BlueprintEvolutionEngine — generates new versions via mutations. | INFO | Other_NonASCII |
| 1117 | core\blueprint_intelligence\blueprint_fusion_engine.py | other_non_ascii | 2 | BlueprintFusionEngine — fuses two blueprints into a hybrid. | INFO | Other_NonASCII |
| 1118 | core\blueprint_intelligence\blueprint_generator.py | other_non_ascii | 2 | BlueprintGenerator — generates blueprints from prompts. | INFO | Other_NonASCII |
| 1119 | core\blueprint_intelligence\blueprint_intelligence_engine.py | other_non_ascii | 2 | BlueprintIntelligenceEngine — main orchestrator. | INFO | Other_NonASCII |
| 1120 | core\blueprint_intelligence\blueprint_ranker.py | other_non_ascii | 2 | BlueprintRanker — ranks blueprints based on multiple criteria. | INFO | Other_NonASCII |
| 1121 | core\blueprint_intelligence\blueprint_recommender.py | other_non_ascii | 2 | BlueprintRecommender — suggests patterns and designs. | INFO | Other_NonASCII |
| 1122 | core\blueprint_intelligence\blueprint_similarity_engine.py | other_non_ascii | 2 | BlueprintSimilarityEngine — similarity search across blueprints. | INFO | Other_NonASCII |
| 1123 | core\blueprint_intelligence\__init__.py | other_non_ascii | 2 | Blueprint Intelligence Engine — HITO 29 | INFO | Other_NonASCII |
| 1124 | core\blueprint_intelligence\models\blueprint_cluster.py | docstring | 1 | """BlueprintCluster model — cluster of similar blueprints.""" | WARNING | Other_NonASCII |
| 1125 | core\blueprint_intelligence\models\blueprint_embedding.py | docstring | 1 | """BlueprintEmbedding model — vector representation of a blueprint.""" | WARNING | Other_NonASCII |
| 1126 | core\blueprint_intelligence\models\blueprint_evolution.py | docstring | 1 | """BlueprintEvolution model — a mutated version of a blueprint.""" | WARNING | Other_NonASCII |
| 1127 | core\blueprint_intelligence\models\blueprint_fusion.py | docstring | 1 | """HybridBlueprint model — result of fusing two blueprints.""" | WARNING | Other_NonASCII |
| 1128 | core\blueprint_intelligence\models\blueprint_pattern.py | docstring | 1 | """BlueprintPattern model — detected structural patterns.""" | WARNING | Other_NonASCII |
| 1129 | core\campaign\campaign_generator.py | other_non_ascii | 61 | - LoreGenerator → world backstory | INFO | Other_NonASCII |
| 1130 | core\campaign\campaign_generator.py | other_non_ascii | 62 | - FactionGenerator → factions and relationships | INFO | Other_NonASCII |
| 1131 | core\campaign\campaign_generator.py | other_non_ascii | 63 | - NPCGenerator → characters with roles | INFO | Other_NonASCII |
| 1132 | core\campaign\campaign_generator.py | other_non_ascii | 64 | - StoryGenerator → quest arcs and main story | INFO | Other_NonASCII |
| 1133 | core\campaign\campaign_generator.py | other_non_ascii | 65 | - DialogGenerator → NPC conversations | INFO | Other_NonASCII |
| 1134 | core\campaign\campaign_generator.py | other_non_ascii | 66 | - EconomyGenerator → pricing and trade | INFO | Other_NonASCII |
| 1135 | core\campaign\campaign_generator.py | other_non_ascii | 103 | for bad input — falls back to a minimal Campaign instead. | INFO | Other_NonASCII |
| 1136 | core\campaign\campaign_generator.py | comment | 128 | except Exception as exc:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1137 | core\campaign\campaign_generator.py | other_non_ascii | 241 | Hito 26.1C contract: never raises — returns a minimal | INFO | Other_NonASCII |
| 1138 | core\campaign\campaign_generator.py | comment | 265 | except Exception as exc:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1139 | core\campaign\campaign_generator.py | docstring | 272 | """Last-resort minimal campaign — never None.""" | WARNING | Other_NonASCII |
| 1140 | core\campaign\package.py | other_non_ascii | 2 | CampaignPackage — mandatory wrapper that guarantees a campaign is *always* | INFO | Other_NonASCII |
| 1141 | core\campaign\package.py | other_non_ascii | 5 | Hito 26.1C — Campaign Export Fix. | INFO | Other_NonASCII |
| 1142 | core\campaign\package.py | other_non_ascii | 18 | * QuestAgent      → builds the package | INFO | Other_NonASCII |
| 1143 | core\campaign\package.py | other_non_ascii | 19 | * ExportAgent     → always writes ``campaign.json`` from it | INFO | Other_NonASCII |
| 1144 | core\campaign\package.py | other_non_ascii | 20 | * Tests           → validate the contract | INFO | Other_NonASCII |
| 1145 | core\campaign\package.py | comment | 129 | except Exception:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1146 | core\campaign\package.py | comment | 135 | except Exception:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1147 | core\campaign\package.py | comment | 296 | except Exception:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1148 | core\campaign\validator.py | other_non_ascii | 2 | CampaignValidator — validates a ``CampaignPackage`` (or raw dict) for | INFO | Other_NonASCII |
| 1149 | core\campaign\validator.py | other_non_ascii | 6 | * ``quests``  — list of quest dicts | INFO | Other_NonASCII |
| 1150 | core\campaign\validator.py | other_non_ascii | 7 | * ``bosses``  — list of boss dicts | INFO | Other_NonASCII |
| 1151 | core\campaign\validator.py | other_non_ascii | 8 | * ``raids``   — list of raid dicts | INFO | Other_NonASCII |
| 1152 | core\campaign\validator.py | other_non_ascii | 9 | * ``story``   — dict with main-story content | INFO | Other_NonASCII |
| 1153 | core\campaign\validator.py | other_non_ascii | 10 | * ``rewards`` — dict with reward summary | INFO | Other_NonASCII |
| 1154 | core\campaign\validator.py | other_non_ascii | 12 | The validator never raises — it returns a ``ValidationResult`` carrying | INFO | Other_NonASCII |
| 1155 | core\campaign\validator.py | other_non_ascii | 200 | result.add_error("root", "Campaign is None — pipeline must never produce None") | INFO | Other_NonASCII |
| 1156 | core\campaign\__init__.py | other_non_ascii | 2 | core.campaign — Campaign generation pipeline. | INFO | Other_NonASCII |
| 1157 | core\campaign\__init__.py | other_non_ascii | 5 | Campaign           — main campaign data object | INFO | Other_NonASCII |
| 1158 | core\campaign\__init__.py | other_non_ascii | 6 | CampaignGenerator  — orchestrator for lore/story/npc/faction/etc. | INFO | Other_NonASCII |
| 1159 | core\campaign\__init__.py | other_non_ascii | 7 | CampaignPackage    — mandatory wrapper guaranteed to never be None | INFO | Other_NonASCII |
| 1160 | core\campaign\__init__.py | other_non_ascii | 8 | CampaignValidator  — validates CampaignPackage structure | INFO | Other_NonASCII |
| 1161 | core\content\boss_generator.py | other_non_ascii | 2 | BossGenerator — Generates boss encounter content as QuestPackage objects. | INFO | Other_NonASCII |
| 1162 | core\content\map_designer.py | other_non_ascii | 2 | MapDesigner — Location resolver for content generators. | INFO | Other_NonASCII |
| 1163 | core\content\map_designer.py | comment | 21 | # Zone definitions: theme → level band and room metadata | WARNING | Other_NonASCII |
| 1164 | core\content\mission_generator.py | other_non_ascii | 2 | MissionGenerator — Generates mission content as QuestPackage objects. | INFO | Other_NonASCII |
| 1165 | core\content\quest_generator.py | other_non_ascii | 2 | QuestGenerator — Generates quest content as QuestPackage objects. | INFO | Other_NonASCII |
| 1166 | core\content\quest_generator.py | other_non_ascii | 88 | f"Enemies patrol the area — defeat {enemy_count} foes to proceed." | INFO | Other_NonASCII |
| 1167 | core\content\quest_package.py | other_non_ascii | 2 | QuestPackage — the universal output type for all content generators. | INFO | Other_NonASCII |
| 1168 | core\content\raid_generator.py | other_non_ascii | 2 | RaidGenerator — Generates raid content as QuestPackage objects. | INFO | Other_NonASCII |
| 1169 | core\content\reward_generator.py | other_non_ascii | 2 | RewardGenerator — Generates reward packages as QuestPackage objects. | INFO | Other_NonASCII |
| 1170 | core\content\__init__.py | other_non_ascii | 2 | Content Generator Package — Automatic playable content generation. | INFO | Other_NonASCII |
| 1171 | core\critic\critic_engine.py | other_non_ascii | 2 | CriticEngine — orchestrates all analyzers and produces a CriticResult. | INFO | Other_NonASCII |
| 1172 | core\critic\critic_engine.py | comment | 118 | except Exception as exc:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1173 | core\critic\critic_engine.py | other_non_ascii | 237 | title="Critical issues detected — full map review", | INFO | Other_NonASCII |
| 1174 | core\critic\critic_report.py | other_non_ascii | 2 | CriticReport — represents the structured critic output and provides | INFO | Other_NonASCII |
| 1175 | core\critic\critic_report.py | comment | 72 | lines.append(f"# Critic Report — {r.map_name or 'untitled map'}") | WARNING | Other_NonASCII |
| 1176 | core\critic\critic_report.py | other_non_ascii | 74 | lines.append(f"_Generated: {self.generated_at}  •  Version: {self.version}_") | INFO | Other_NonASCII |
| 1177 | core\critic\critic_report.py | other_non_ascii | 122 | lines.append(f"_Priority: {rec.priority.value}  •  Category: {rec.category}_") | INFO | Other_NonASCII |
| 1178 | core\critic\heatmap_renderer.py | other_non_ascii | 2 | HeatmapRenderer — produces per-category heatmaps (PNGs) for the visual critic. | INFO | Other_NonASCII |
| 1179 | core\critic\score_calculator.py | other_non_ascii | 2 | ScoreCalculator — combines per-category scores into a final overall_score. | INFO | Other_NonASCII |
| 1180 | core\critic\score_calculator.py | comment | 55 | # No known categories — fall back to simple mean. | WARNING | Other_NonASCII |
| 1181 | core\critic\visual_critic.py | other_non_ascii | 2 | VisualCritic — high-level orchestrator for the Visual Map Critic AI. | INFO | Other_NonASCII |
| 1182 | core\critic\visual_critic.py | comment | 157 | except Exception as exc:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1183 | core\critic\__init__.py | other_non_ascii | 2 | Visual Map Critic AI — analyzes OpenTibia maps generated by Agente RME. | INFO | Other_NonASCII |
| 1184 | core\critic\analyzers\base_analyzer.py | other_non_ascii | 2 | BaseAnalyzer — common helpers and types for all critic analyzers. | INFO | Other_NonASCII |
| 1185 | core\critic\analyzers\boss_room_analyzer.py | other_non_ascii | 2 | BossRoomAnalyzer — analyzes boss arenas for access, space, escape, and combat flow. | INFO | Other_NonASCII |
| 1186 | core\critic\analyzers\boss_room_analyzer.py | comment | 242 | # many boundary exits — treat as having an escape route | WARNING | Other_NonASCII |
| 1187 | core\critic\analyzers\city_analyzer.py | other_non_ascii | 2 | CityAnalyzer — analyzes city infrastructure: streets, depot, temple, NPCs, connectivity. | INFO | Other_NonASCII |
| 1188 | core\critic\analyzers\decor_analyzer.py | other_non_ascii | 2 | DecorAnalyzer — analyzes decorative content: variety, repetition, overuse, void zones. | INFO | Other_NonASCII |
| 1189 | core\critic\analyzers\decor_analyzer.py | other_non_ascii | 127 | message=f"Only {variety} unique decoration types — map looks repetitive", | INFO | Other_NonASCII |
| 1190 | core\critic\analyzers\density_analyzer.py | other_non_ascii | 2 | DensityAnalyzer — analyzes tile density and content concentration. | INFO | Other_NonASCII |
| 1191 | core\critic\analyzers\density_analyzer.py | other_non_ascii | 150 | message=f"Average items per tile is {avg_items:.1f} — possibly over-decorated", | INFO | Other_NonASCII |
| 1192 | core\critic\analyzers\hunt_analyzer.py | other_non_ascii | 2 | HuntAnalyzer — analyzes hunt zones for farming flow, rotation, and respawn. | INFO | Other_NonASCII |
| 1193 | core\critic\analyzers\hunt_analyzer.py | other_non_ascii | 113 | message=f"Hunts {i} and {j} are {d} tiles apart — consider adding a closer hunt", | INFO | Other_NonASCII |
| 1194 | core\critic\analyzers\hunt_analyzer.py | comment | 203 | # 3. respawn health — average respawn time vs target | WARNING | Other_NonASCII |
| 1195 | core\critic\analyzers\hunt_analyzer.py | comment | 211 | # 4. spatial flow — average nearest neighbor distance | WARNING | Other_NonASCII |
| 1196 | core\critic\analyzers\navigation_analyzer.py | other_non_ascii | 2 | NavigationAnalyzer — analyzes path connectivity, dead-ends, and bottlenecks. | INFO | Other_NonASCII |
| 1197 | core\critic\analyzers\navigation_analyzer.py | other_non_ascii | 27 | Uses only structural analysis (no A* / Dijkstra) — the heavy | INFO | Other_NonASCII |
| 1198 | core\critic\analyzers\pathfinding_analyzer.py | other_non_ascii | 2 | PathfindingAnalyzer — A*, BFS, Dijkstra-based analysis. | INFO | Other_NonASCII |
| 1199 | core\critic\analyzers\pathfinding_analyzer.py | docstring | 35 | """Breadth-First Search — uniform cost grid expansion.""" | WARNING | Other_NonASCII |
| 1200 | core\critic\analyzers\pathfinding_analyzer.py | docstring | 65 | """Dijkstra — weighted shortest path (cost 1 for cardinal, sqrt(2) for diagonal).""" | WARNING | Other_NonASCII |
| 1201 | core\critic\analyzers\pathfinding_analyzer.py | docstring | 100 | """A* — best-first search with heuristic.""" | WARNING | Other_NonASCII |
| 1202 | core\critic\analyzers\pathfinding_analyzer.py | comment | 257 | # PathfindingAnalyzer — produces pathfinding_score | WARNING | Other_NonASCII |
| 1203 | core\critic\analyzers\pathfinding_analyzer.py | other_non_ascii | 412 | message="Navigation bottleneck detected — routes funnel through this tile", | INFO | Other_NonASCII |
| 1204 | core\critic\analyzers\region_analyzer.py | other_non_ascii | 2 | RegionAnalyzer — analyzes named regions: emptiness, level ranges, coverage. | INFO | Other_NonASCII |
| 1205 | core\critic\analyzers\region_analyzer.py | other_non_ascii | 27 | This analyzer is a meta-analyzer — it does not produce its own | INFO | Other_NonASCII |
| 1206 | core\critic\analyzers\spawn_analyzer.py | other_non_ascii | 2 | SpawnAnalyzer — analyzes monster spawn distribution and density. | INFO | Other_NonASCII |
| 1207 | core\critic\analyzers\visual_analyzer.py | other_non_ascii | 2 | VisualAnalyzer — analyzes the visual quality of the map: tile quantity, | INFO | Other_NonASCII |
| 1208 | core\critic\analyzers\__init__.py | other_non_ascii | 2 | Critic analyzers — modular, pluggable analyzers that each contribute a score. | INFO | Other_NonASCII |
| 1209 | core\critic\models\critic_issue.py | other_non_ascii | 2 | CriticIssue — represents a detected problem in a map. | INFO | Other_NonASCII |
| 1210 | core\critic\models\critic_recommendation.py | other_non_ascii | 2 | CriticRecommendation — concrete actions to improve a map. | INFO | Other_NonASCII |
| 1211 | core\critic\models\critic_result.py | other_non_ascii | 2 | CriticResult — aggregated critic output for a map. | INFO | Other_NonASCII |
| 1212 | core\critic\models\critic_score.py | other_non_ascii | 2 | CriticScore — represents a numeric quality score in the 0-100 range. | INFO | Other_NonASCII |
| 1213 | core\critic\models\__init__.py | other_non_ascii | 2 | Critic models — data structures for the Visual Map Critic AI. | INFO | Other_NonASCII |
| 1214 | core\evolution\expansion_engine.py | other_non_ascii | 142 | f"Expansión completada: {len(applied_plans)} nuevas zonas creadas, " | INFO | Latin_Extended |
| 1215 | core\evolution\expansion_engine.py | other_non_ascii | 143 | f"{tiles_added} tiles añadidos. " | INFO | Latin_Extended |
| 1216 | core\evolution\expansion_engine.py | other_non_ascii | 174 | summary=f"Expansión con {len(applied)} plan(es) predefinidos.", | INFO | Latin_Extended |
| 1217 | core\evolution\improvement_engine.py | other_non_ascii | 126 | f"Mejora completada: {score_before} → {score_after} " | INFO | Other_NonASCII |
| 1218 | core\evolution\improvement_engine.py | other_non_ascii | 167 | if "decoración" in lower or "suelo" in lower: | INFO | Latin_Extended |
| 1219 | core\evolution\map_evolver.py | other_non_ascii | 66 | f"  Score: {self.overall_score_before} → {self.overall_score_after} " | INFO | Other_NonASCII |
| 1220 | core\evolution\map_evolver.py | other_non_ascii | 70 | lines.append(f"  Success: {'✅' if self.success else '❌'}") | INFO | Other_NonASCII |
| 1221 | core\evolution\map_evolver.py | other_non_ascii | 89 | OTBM → Analyzer → Quality Detector → Improvement Engine | INFO | Other_NonASCII |
| 1222 | core\evolution\map_evolver.py | other_non_ascii | 90 | → Expansion Engine → Modernization Engine → Architect AI → OTBM | INFO | Other_NonASCII |
| 1223 | core\evolution\map_evolver.py | other_non_ascii | 167 | result.pipeline_log.append(f"       ⚠ {issue}") | INFO | Other_NonASCII |
| 1224 | core\evolution\map_evolver.py | other_non_ascii | 208 | result.pipeline_log.append(f"EVOLUTION COMPLETE ✅") | INFO | Other_NonASCII |
| 1225 | core\evolution\map_evolver.py | other_non_ascii | 210 | f"Score: {result.overall_score_before} → {result.overall_score_after}" | INFO | Other_NonASCII |
| 1226 | core\evolution\map_evolver.py | other_non_ascii | 217 | result.pipeline_log.append(f"❌ EVOLUTION FAILED: {e}") | INFO | Other_NonASCII |
| 1227 | core\evolution\modernization_engine.py | other_non_ascii | 51 | - Item ID migration (8.6 → 13.x/14.x mapping) | INFO | Other_NonASCII |
| 1228 | core\evolution\modernization_engine.py | other_non_ascii | 56 | - Spawn format conversion (old radius-based → modern) | INFO | Other_NonASCII |
| 1229 | core\evolution\modernization_engine.py | comment | 70 | # Item ID migration map: old IDs (8.6/10.x) → modern IDs (13.x+) | WARNING | Other_NonASCII |
| 1230 | core\evolution\modernization_engine.py | comment | 74 | 101: 102,  # old dirt → new dirt | WARNING | Other_NonASCII |
| 1231 | core\evolution\modernization_engine.py | comment | 80 | 1000: 1126,  # old stone wall → new stone wall | WARNING | Other_NonASCII |
| 1232 | core\evolution\modernization_engine.py | comment | 81 | 1002: 1127,  # old wooden wall → new wooden wall | WARNING | Other_NonASCII |
| 1233 | core\evolution\modernization_engine.py | comment | 109 | 104: 102,  # old soil → dirt | WARNING | Other_NonASCII |
| 1234 | core\evolution\modernization_engine.py | comment | 110 | 105: 103,  # old grass tile → grass | WARNING | Other_NonASCII |
| 1235 | core\evolution\modernization_engine.py | comment | 111 | 106: 231,  # old pavement → cobblestone | WARNING | Other_NonASCII |
| 1236 | core\evolution\modernization_engine.py | comment | 112 | 400: 398,  # old cave wall → cave wall | WARNING | Other_NonASCII |
| 1237 | core\evolution\modernization_engine.py | comment | 113 | 401: 398,  # old underground wall → cave wall | WARNING | Other_NonASCII |
| 1238 | core\evolution\modernization_engine.py | comment | 114 | 430: 1284,  # old stone floor → stone | WARNING | Other_NonASCII |
| 1239 | core\evolution\modernization_engine.py | comment | 147 | # 8.6 → modern renames | WARNING | Other_NonASCII |
| 1240 | core\evolution\modernization_engine.py | other_non_ascii | 259 | f"Modernización {from_version.value} → {to_version}: " | INFO | Other_NonASCII, Latin_Extended |
| 1241 | core\evolution\modernization_engine.py | other_non_ascii | 413 | report.changes_applied.append(f"OTBM header actualizado: v{old_otbm} → v{target_otbm}") | INFO | Other_NonASCII |
| 1242 | core\evolution\quality_detector.py | other_non_ascii | 523 | suggestions.append("Añadir pasillos o puentes para mejorar la conectividad") | INFO | Latin_Extended |
| 1243 | core\evolution\quality_detector.py | other_non_ascii | 531 | suggestions.append("Añadir más tiles transitables o contenido jugable") | INFO | Latin_Extended |
| 1244 | core\evolution\quality_detector.py | other_non_ascii | 533 | issues.append(f"Densidad excesiva — mapa saturado") | INFO | Other_NonASCII |
| 1245 | core\evolution\quality_detector.py | other_non_ascii | 541 | f"Añadir al menos {self.MIN_MONSTER_TYPES_PER_HUNT - metrics.monster_types} tipo(s) de monstruo adicional(es)" | INFO | Latin_Extended |
| 1246 | core\evolution\quality_detector.py | other_non_ascii | 546 | f"Añadir al menos {self.MIN_SPAWNS_PER_HUNT_ZONE - metrics.spawn_count} spawn(s)" | INFO | Latin_Extended |
| 1247 | core\evolution\quality_detector.py | other_non_ascii | 551 | issues.append(f"Decoración pobre ({metrics.decoration_score:.0f}/100)") | INFO | Latin_Extended |
| 1248 | core\evolution\quality_detector.py | other_non_ascii | 553 | "Añadir más elementos decorativos: antorchas, estatuas, alfombras, etc." | INFO | Latin_Extended |
| 1249 | core\evolution\quality_detector.py | other_non_ascii | 557 | suggestions.append("Variar los tiles de suelo para mejorar la estética") | INFO | Latin_Extended |
| 1250 | core\evolution\quality_detector.py | other_non_ascii | 561 | issues.append(f"Problemas arquitectónicos ({metrics.architecture_score:.0f}/100)") | INFO | Latin_Extended |
| 1251 | core\evolution\quality_detector.py | other_non_ascii | 577 | "global_issues": ["Mapa vacío"], | INFO | Latin_Extended |
| 1252 | core\evolution\quality_detector.py | other_non_ascii | 590 | global_issues.append(f"Zonas vacías detectadas: {', '.join(empty_zones)}") | INFO | Latin_Extended |
| 1253 | core\evolution\quality_detector.py | other_non_ascii | 591 | global_suggestions.append("Rellenar zonas vacías con hunts, quests o decoración") | INFO | Latin_Extended |
| 1254 | core\evolution\quality_detector.py | other_non_ascii | 596 | global_issues.append("No se detectó ninguna ciudad") | INFO | Latin_Extended |
| 1255 | core\evolution\quality_detector.py | other_non_ascii | 597 | global_suggestions.append("Añadir al menos una ciudad con temple, depot y NPCs") | INFO | Latin_Extended |
| 1256 | core\evolution\quality_detector.py | other_non_ascii | 612 | global_suggestions.append("Considerar añadir una boss room para contenido end-game") | INFO | Latin_Extended |
| 1257 | core\evolution\quality_detector.py | other_non_ascii | 617 | global_suggestions.append("Considerar añadir zonas de quest para progresión") | INFO | Latin_Extended |
| 1258 | core\export\release_builder.py | other_non_ascii | 14 | npc.xml, zones.xml, report.json, preview.png — in one operation. | INFO | Other_NonASCII |
| 1259 | core\exporters\lua_exporter.py | other_non_ascii | 2 | Lua Exporter — converts a WorldModel into a complete RME-compatible Lua script. | INFO | Other_NonASCII |
| 1260 | core\exporters\lua_exporter.py | other_non_ascii | 9 | WorldModel → LuaExporter → Lua script → LuaValidator → QA Pipeline | INFO | Other_NonASCII |
| 1261 | core\exporters\lua_formatter.py | other_non_ascii | 2 | Lua Formatter — normaliza indentación, saltos de línea y espacios en | INFO | Other_NonASCII, Latin_Extended |
| 1262 | core\exporters\lua_formatter.py | other_non_ascii | 3 | código Lua generado. | INFO | Latin_Extended |
| 1263 | core\exporters\lua_formatter.py | other_non_ascii | 16 | Normaliza código Lua generado. | INFO | Latin_Extended |
| 1264 | core\exporters\lua_formatter.py | other_non_ascii | 19 | 1. Indentación consistente (4 espacios por nivel) | INFO | Latin_Extended |
| 1265 | core\exporters\lua_formatter.py | other_non_ascii | 20 | 2. Sin espacios al final de línea | INFO | Latin_Extended |
| 1266 | core\exporters\lua_formatter.py | other_non_ascii | 21 | 3. Saltos de línea UNIX (\\n) | INFO | Latin_Extended |
| 1267 | core\exporters\lua_formatter.py | other_non_ascii | 22 | 4. Línea final en blanco | INFO | Latin_Extended |
| 1268 | core\exporters\lua_formatter.py | other_non_ascii | 32 | Normaliza código Lua. | INFO | Latin_Extended |
| 1269 | core\exporters\lua_formatter.py | other_non_ascii | 35 | lua_code: Código Lua sin formatear. | INFO | Latin_Extended |
| 1270 | core\exporters\lua_formatter.py | other_non_ascii | 38 | Código formateado. | INFO | Latin_Extended |
| 1271 | core\exporters\lua_formatter.py | comment | 43 | # Normalizar saltos de línea a UNIX | WARNING | Latin_Extended |
| 1272 | core\exporters\lua_formatter.py | comment | 46 | # Eliminar espacios al final de cada línea | WARNING | Latin_Extended |
| 1273 | core\exporters\lua_formatter.py | comment | 49 | # Reconstruir con indentación estándar | WARNING | Latin_Extended |
| 1274 | core\exporters\lua_formatter.py | comment | 52 | # Asegurar línea final | WARNING | Latin_Extended |
| 1275 | core\exporters\lua_formatter.py | other_non_ascii | 59 | Re-indenta líneas de código basado en palabras clave. | INFO | Latin_Extended |
| 1276 | core\exporters\lua_formatter.py | other_non_ascii | 61 | Incrementa indentación después de: | INFO | Latin_Extended |
| 1277 | core\exporters\lua_formatter.py | other_non_ascii | 67 | Decrementa indentación antes de: | INFO | Latin_Extended |
| 1278 | core\exporters\lua_formatter.py | comment | 81 | # Comentarios se mantienen sin cambios de indentación | WARNING | Latin_Extended |
| 1279 | core\exporters\lua_formatter.py | comment | 86 | # Palabras clave que decrementan indentación | WARNING | Latin_Extended |
| 1280 | core\exporters\lua_formatter.py | comment | 90 | # Aplicar indentación actual | WARNING | Latin_Extended |
| 1281 | core\exporters\lua_formatter.py | comment | 93 | # Palabras clave que incrementan indentación | WARNING | Latin_Extended |
| 1282 | core\exporters\lua_validator.py | other_non_ascii | 2 | Lua Validator — valida código Lua generado contra reglas RME. | INFO | Other_NonASCII, Latin_Extended |
| 1283 | core\exporters\lua_validator.py | other_non_ascii | 13 | → Export abortado | INFO | Other_NonASCII |
| 1284 | core\exporters\lua_validator.py | docstring | 25 | """Resultado de la validación de código Lua.""" | WARNING | Latin_Extended |
| 1285 | core\exporters\lua_validator.py | other_non_ascii | 58 | Valida código Lua generado para compatibilidad con RME. | INFO | Latin_Extended |
| 1286 | core\exporters\lua_validator.py | other_non_ascii | 69 | Valida código Lua contra reglas RME. | INFO | Latin_Extended |
| 1287 | core\exporters\lua_validator.py | other_non_ascii | 72 | lua_code: Código Lua generado. | INFO | Latin_Extended |
| 1288 | core\exporters\lua_validator.py | other_non_ascii | 124 | (r"tile:addGround\b", "tile:addGround — use tile.ground = <id>"), | INFO | Other_NonASCII |
| 1289 | core\exporters\lua_validator.py | other_non_ascii | 125 | (r"tile:setGround\b", "tile:setGround — use tile.ground = <id>"), | INFO | Other_NonASCII |
| 1290 | core\exporters\lua_validator.py | other_non_ascii | 126 | (r"setGround\(", "setGround() — use tile.ground = <id>"), | INFO | Other_NonASCII |
| 1291 | core\exporters\lua_validator.py | other_non_ascii | 127 | (r"addGround\(", "addGround() — use tile.ground = <id>"), | INFO | Other_NonASCII |
| 1292 | core\exporters\lua_validator.py | other_non_ascii | 128 | (r"map\.setTile\b", "map:setTile — use map:getOrCreateTile"), | INFO | Other_NonASCII |
| 1293 | core\exporters\lua_validator.py | other_non_ascii | 129 | (r"removeMap\b", "removeMap — forbidden"), | INFO | Other_NonASCII |
| 1294 | core\exporters\lua_validator.py | other_non_ascii | 130 | (r"app\.createMap\b", "app:createMap — forbidden"), | INFO | Other_NonASCII |
| 1295 | core\exporters\lua_validator.py | other_non_ascii | 142 | result.add_error("Forbidden API: bare 'createTile' — use map:getOrCreateTile()") | INFO | Other_NonASCII |
| 1296 | core\exporters\lua_validator.py | docstring | 146 | """Verifica paréntesis balanceados.""" | WARNING | Latin_Extended |
| 1297 | core\exporters\lua_validator.py | docstring | 165 | """Verifica nombres de criatura no vacíos.""" | WARNING | Latin_Extended |
| 1298 | core\exporters\lua_writer.py | other_non_ascii | 2 | Lua Writer — responsible for writing Lua scripts for RME. | INFO | Other_NonASCII |
| 1299 | core\exporters\__init__.py | other_non_ascii | 2 | core.exporters — WorldModel → Lua → QA → OTBM pipeline. | INFO | Other_NonASCII |
| 1300 | core\exporters\__init__.py | other_non_ascii | 5 | WorldModel → Lua Exporter → Lua Code → QA Pipeline → OTBM Exporter | INFO | Other_NonASCII |
| 1301 | core\exporters\__init__.py | other_non_ascii | 8 | - LuaWriter       — Low-level Lua code generation | INFO | Other_NonASCII |
| 1302 | core\exporters\__init__.py | other_non_ascii | 9 | - LuaValidator    — Validates generated Lua code | INFO | Other_NonASCII |
| 1303 | core\exporters\__init__.py | other_non_ascii | 10 | - LuaExporter     — Converts WorldModel to complete Lua script | INFO | Other_NonASCII |
| 1304 | core\generators\base_generator.py | other_non_ascii | 2 | Base Generator — abstract base class for all WorldModel generators. | INFO | Other_NonASCII |
| 1305 | core\generators\base_generator.py | other_non_ascii | 9 | ├── ThemeGenerator   — resolves theme strings into ThemeDefinition | INFO | Other_NonASCII |
| 1306 | core\generators\base_generator.py | other_non_ascii | 10 | ├── SpawnGenerator   — places monster spawns on existing tiles | INFO | Other_NonASCII |
| 1307 | core\generators\base_generator.py | other_non_ascii | 11 | ├── HuntGenerator    — generates complete hunt zones | INFO | Other_NonASCII |
| 1308 | core\generators\base_generator.py | other_non_ascii | 12 | ├── CityGenerator    — generates city layouts | INFO | Other_NonASCII |
| 1309 | core\generators\base_generator.py | other_non_ascii | 13 | ├── DungeonGenerator — generates dungeon layouts | INFO | Other_NonASCII |
| 1310 | core\generators\base_generator.py | other_non_ascii | 14 | └── WorldGenerator   — orchestrates all generators from a prompt | INFO | Other_NonASCII |
| 1311 | core\generators\city_generator.py | other_non_ascii | 2 | City Generator — generates city layouts (temple, depot, market, houses, roads) | INFO | Other_NonASCII |
| 1312 | core\generators\city_generator.py | comment | 281 | # (x1, y1, x2, y2) — offsets from origin | WARNING | Other_NonASCII |
| 1313 | core\generators\dungeon_generator.py | other_non_ascii | 2 | Dungeon Generator — generates underground dungeon layouts (entrance, loops, | INFO | Other_NonASCII |
| 1314 | core\generators\dungeon_generator.py | comment | 187 | # Add staircase item (ID 130 — typical staircase down) | WARNING | Other_NonASCII |
| 1315 | core\generators\dungeon_generator.py | comment | 422 | # Add staircase up item (ID 138 — typical staircase up) | WARNING | Other_NonASCII |
| 1316 | core\generators\hunt_generator.py | other_non_ascii | 2 | Hunt Generator — generates complete hunt zones as WorldModel instances. | INFO | Other_NonASCII |
| 1317 | core\generators\spawn_generator.py | other_non_ascii | 2 | Spawn Generator — places monster spawns into a WorldModel. | INFO | Other_NonASCII |
| 1318 | core\generators\spawn_generator.py | other_non_ascii | 96 | - area: tuple (x1, y1, x2, y2) — restrict spawns to this area | INFO | Other_NonASCII |
| 1319 | core\generators\theme_generator.py | other_non_ascii | 2 | Theme Generator — resolves theme strings into ThemeDefinition objects. | INFO | Other_NonASCII |
| 1320 | core\generators\world_generator.py | other_non_ascii | 2 | World Generator — main orchestrator for all generators. | INFO | Other_NonASCII |
| 1321 | core\generators\world_generator.py | other_non_ascii | 10 | ↓ | INFO | Other_NonASCII |
| 1322 | core\generators\world_generator.py | other_non_ascii | 11 | Theme Resolver  ─→ ThemeDefinition | INFO | Other_NonASCII |
| 1323 | core\generators\world_generator.py | other_non_ascii | 12 | ↓ | INFO | Other_NonASCII |
| 1324 | core\generators\world_generator.py | other_non_ascii | 13 | Generator       ─→ WorldModel | INFO | Other_NonASCII |
| 1325 | core\generators\world_generator.py | other_non_ascii | 14 | ↓ | INFO | Other_NonASCII |
| 1326 | core\generators\world_generator.py | other_non_ascii | 15 | Validator       ─→ Validated WorldModel | INFO | Other_NonASCII |
| 1327 | core\generators\world_generator.py | other_non_ascii | 182 | "Generate Issavi hunt level 300" → | INFO | Other_NonASCII |
| 1328 | core\generators\world_generator.py | other_non_ascii | 196 | range_match = re.search(r"level\s*(\d+)\s*[-–]\s*(\d+)", prompt_lower) | INFO | Other_NonASCII |
| 1329 | core\generators\__init__.py | other_non_ascii | 2 | core.generators — procedural world generators that produce WorldModel instances. | INFO | Other_NonASCII |
| 1330 | core\generators\__init__.py | other_non_ascii | 7 | Asset Registry → Blueprint Registry → World Model → World Generator | INFO | Other_NonASCII |
| 1331 | core\generators\__init__.py | other_non_ascii | 8 | → QA → Lua Export → OTBM Export | INFO | Other_NonASCII |
| 1332 | core\generators\__init__.py | other_non_ascii | 11 | - BaseGenerator      — abstract base class for all generators | INFO | Other_NonASCII |
| 1333 | core\generators\__init__.py | other_non_ascii | 12 | - ThemeGenerator     — resolves theme strings into ThemeDefinition | INFO | Other_NonASCII |
| 1334 | core\generators\__init__.py | other_non_ascii | 13 | - SpawnGenerator     — places monster spawns on existing tiles | INFO | Other_NonASCII |
| 1335 | core\generators\__init__.py | other_non_ascii | 14 | - HuntGenerator      — complete hunt zones with terrain and spawns | INFO | Other_NonASCII |
| 1336 | core\generators\__init__.py | other_non_ascii | 15 | - CityGenerator      — city layout with streets, buildings, districts | INFO | Other_NonASCII |
| 1337 | core\generators\__init__.py | other_non_ascii | 16 | - DungeonGenerator   — underground dungeon with rooms and corridors | INFO | Other_NonASCII |
| 1338 | core\generators\__init__.py | other_non_ascii | 17 | - WorldGenerator     — orchestrates all generators from a prompt | INFO | Other_NonASCII |
| 1339 | core\generators\city\building_generator.py | other_non_ascii | 68 | name="Casa Pequeña", | INFO | Latin_Extended |
| 1340 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 3 | en un WorldModel para exportación directa a OTBM. | INFO | Latin_Extended |
| 1341 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 25 | - District tiles → WorldModel tiles | INFO | Other_NonASCII |
| 1342 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 26 | - Roads → ground tiles with road ID | INFO | Other_NonASCII |
| 1343 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 27 | - Temple / Depot / Market / Harbor → special item layouts | INFO | Other_NonASCII |
| 1344 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 28 | - Buildings → wall-bordered structures | INFO | Other_NonASCII |
| 1345 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 29 | - Waypoints → waypoints array in WorldModel | INFO | Other_NonASCII |
| 1346 | core\generators\city\city_to_worldmodel.py | other_non_ascii | 30 | - Spawns → spawns array in WorldModel | INFO | Other_NonASCII |
| 1347 | core\generators\city\district_generator.py | other_non_ascii | 60 | description="Depósito con lockers, inbox y acceso rápido.", | INFO | Latin_Extended |
| 1348 | core\generators\city\district_generator.py | other_non_ascii | 69 | description="Viviendas pequeñas y medianas para habitantes.", | INFO | Latin_Extended |
| 1349 | core\generators\dungeon\shortcut_generator.py | other_non_ascii | 17 | "description": "Acceso rápido entre entrada y arena del jefe.", | INFO | Latin_Extended |
| 1350 | core\knowledge\dataset_builder.py | other_non_ascii | 2 | DatasetBuilder — orchestrates extraction + indexing + dataset generation. | INFO | Other_NonASCII |
| 1351 | core\knowledge\dataset_builder.py | comment | 227 | # WorldModel-like — try .to_dict() | WARNING | Other_NonASCII |
| 1352 | core\knowledge\dataset_builder.py | comment | 235 | # Blueprint-like — flatten via to_dict | WARNING | Other_NonASCII |
| 1353 | core\knowledge\dataset_builder.py | comment | 248 | # Campaign-like — try to_dict, else to a generic dict | WARNING | Other_NonASCII |
| 1354 | core\knowledge\knowledge_catalog.py | other_non_ascii | 2 | KnowledgeCatalog — high-level metadata about the dataset. | INFO | Other_NonASCII |
| 1355 | core\knowledge\knowledge_catalog.py | comment | 81 | # top_themes — most common biomes / themes | WARNING | Other_NonASCII |
| 1356 | core\knowledge\knowledge_engine.py | other_non_ascii | 2 | KnowledgeEngine — the public API for the knowledge subsystem. | INFO | Other_NonASCII |
| 1357 | core\knowledge\knowledge_engine.py | comment | 92 | # Public API — find similar | WARNING | Other_NonASCII |
| 1358 | core\knowledge\knowledge_index.py | other_non_ascii | 2 | KnowledgeIndex — bundle of per-type indexers used by the engine. | INFO | Other_NonASCII |
| 1359 | core\knowledge\knowledge_metrics.py | other_non_ascii | 2 | KnowledgeMetrics — coverage and quality metrics for a dataset. | INFO | Other_NonASCII |
| 1360 | core\knowledge\knowledge_query.py | other_non_ascii | 2 | KnowledgeQuery — parses free-text and structured queries. | INFO | Other_NonASCII |
| 1361 | core\knowledge\knowledge_query.py | other_non_ascii | 196 | - text(query)    — free-text, falls back to similarity search. | INFO | Other_NonASCII |
| 1362 | core\knowledge\knowledge_query.py | other_non_ascii | 197 | - structured(**) — explicit entry_type + filters. | INFO | Other_NonASCII |
| 1363 | core\knowledge\knowledge_query.py | other_non_ascii | 198 | - filter(func)   — python callable filter on entries. | INFO | Other_NonASCII |
| 1364 | core\knowledge\knowledge_query.py | comment | 394 | # Allow non-strict — still keep results | WARNING | Other_NonASCII |
| 1365 | core\knowledge\knowledge_ranker.py | other_non_ascii | 2 | KnowledgeRanker — combines multiple quality signals into a single rank. | INFO | Other_NonASCII |
| 1366 | core\knowledge\knowledge_ranker.py | other_non_ascii | 10 | - level_fit       (0..1) — how well the entry matches a target level | INFO | Other_NonASCII |
| 1367 | core\knowledge\knowledge_recommender.py | other_non_ascii | 2 | KnowledgeRecommender — produces recommendations based on ranker scores. | INFO | Other_NonASCII |
| 1368 | core\knowledge\knowledge_report.py | other_non_ascii | 2 | KnowledgeReport — human-readable markdown report of the dataset. | INFO | Other_NonASCII |
| 1369 | core\knowledge\knowledge_report.py | other_non_ascii | 117 | f"- **{e['name']}** (`{e['id']}`) — " | INFO | Other_NonASCII |
| 1370 | core\knowledge\knowledge_search.py | other_non_ascii | 2 | KnowledgeSearch — high-level search that combines query + recommender. | INFO | Other_NonASCII |
| 1371 | core\knowledge\knowledge_search.py | other_non_ascii | 28 | - `search(query, k, entry_type=...)` — text or structured. | INFO | Other_NonASCII |
| 1372 | core\knowledge\knowledge_search.py | other_non_ascii | 29 | - `find_similar(entry, k)`           — entry-to-entry similarity. | INFO | Other_NonASCII |
| 1373 | core\knowledge\knowledge_search.py | other_non_ascii | 30 | - `find_by_text(text, k)`           — text-only similarity. | INFO | Other_NonASCII |
| 1374 | core\knowledge\knowledge_search.py | other_non_ascii | 31 | - `find_by_attrs(...)`              — filter by attributes. | INFO | Other_NonASCII |
| 1375 | core\knowledge\__init__.py | other_non_ascii | 2 | HITO 28 — OpenTibia Knowledge Dataset Builder. | INFO | Other_NonASCII |
| 1376 | core\knowledge\__init__.py | other_non_ascii | 10 | - `DatasetBuilder`     — process sources into a `KnowledgeDataset`. | INFO | Other_NonASCII |
| 1377 | core\knowledge\__init__.py | other_non_ascii | 11 | - `KnowledgeEngine`    — high-level public API (find_similar_*, search, query). | INFO | Other_NonASCII |
| 1378 | core\knowledge\__init__.py | other_non_ascii | 12 | - `KnowledgeIndex`     — per-type in-memory indexers. | INFO | Other_NonASCII |
| 1379 | core\knowledge\__init__.py | other_non_ascii | 13 | - `KnowledgeQuery`     — text / structured / filter queries. | INFO | Other_NonASCII |
| 1380 | core\knowledge\__init__.py | other_non_ascii | 14 | - `KnowledgeRanker`    — combines quality, critic, playtest, reuse, similarity. | INFO | Other_NonASCII |
| 1381 | core\knowledge\__init__.py | other_non_ascii | 15 | - `KnowledgeRecommender` — reuse recommendations. | INFO | Other_NonASCII |
| 1382 | core\knowledge\__init__.py | other_non_ascii | 16 | - `KnowledgeSearch`    — search facade. | INFO | Other_NonASCII |
| 1383 | core\knowledge\__init__.py | other_non_ascii | 17 | - `KnowledgeCatalog`   — high-level catalog description. | INFO | Other_NonASCII |
| 1384 | core\knowledge\__init__.py | other_non_ascii | 18 | - `KnowledgeMetrics`   — coverage / quality metrics (knowledge_metrics.json). | INFO | Other_NonASCII |
| 1385 | core\knowledge\__init__.py | other_non_ascii | 19 | - `KnowledgeReport`    — human-readable report (knowledge_report.md). | INFO | Other_NonASCII |
| 1386 | core\knowledge\extractors\base_extractor.py | other_non_ascii | 2 | BaseExtractor — shared helpers for all knowledge extractors. | INFO | Other_NonASCII |
| 1387 | core\knowledge\extractors\base_extractor.py | comment | 101 | # Anything else — wrap it | WARNING | Other_NonASCII |
| 1388 | core\knowledge\extractors\base_extractor.py | comment | 190 | # Default extract() — must be overridden | WARNING | Other_NonASCII |
| 1389 | core\knowledge\extractors\biome_extractor.py | other_non_ascii | 2 | BiomeExtractor — extract biome entries from a world. | INFO | Other_NonASCII |
| 1390 | core\knowledge\extractors\boss_extractor.py | other_non_ascii | 2 | BossExtractor — extract boss room entries from a world. | INFO | Other_NonASCII |
| 1391 | core\knowledge\extractors\city_extractor.py | other_non_ascii | 2 | CityExtractor — extract city entries from a world. | INFO | Other_NonASCII |
| 1392 | core\knowledge\extractors\hunt_extractor.py | other_non_ascii | 2 | HuntExtractor — extract hunt entries from a world. | INFO | Other_NonASCII |
| 1393 | core\knowledge\extractors\hunt_extractor.py | other_non_ascii | 5 | 'cave', or 'sewers' — and that contains at least one spawn. | INFO | Other_NonASCII |
| 1394 | core\knowledge\extractors\quest_extractor.py | other_non_ascii | 2 | QuestExtractor — extract quest entries from a world / campaign. | INFO | Other_NonASCII |
| 1395 | core\knowledge\extractors\raid_extractor.py | other_non_ascii | 2 | RaidExtractor — extract raid entries from a world. | INFO | Other_NonASCII |
| 1396 | core\knowledge\extractors\spawn_extractor.py | other_non_ascii | 2 | SpawnExtractor — extract monster spawn entries from a world. | INFO | Other_NonASCII |
| 1397 | core\knowledge\extractors\structure_extractor.py | other_non_ascii | 2 | StructureExtractor — extract generic structure / region entries from a world. | INFO | Other_NonASCII |
| 1398 | core\knowledge\extractors\waypoint_extractor.py | other_non_ascii | 2 | WaypointExtractor — extract waypoint entries from a world. | INFO | Other_NonASCII |
| 1399 | core\knowledge\extractors\__init__.py | docstring | 1 | """Knowledge extractors — pull catalogued entries from map sources.""" | WARNING | Other_NonASCII |
| 1400 | core\knowledge\indexers\base_indexer.py | other_non_ascii | 2 | BaseIndexer — in-memory inverted index for a single entity type. | INFO | Other_NonASCII |
| 1401 | core\knowledge\indexers\biome_indexer.py | docstring | 1 | """BiomeIndexer — index biomes for fast theme lookup.""" | WARNING | Other_NonASCII |
| 1402 | core\knowledge\indexers\boss_indexer.py | docstring | 1 | """BossIndexer — index boss rooms by arena_type / shape / level.""" | WARNING | Other_NonASCII |
| 1403 | core\knowledge\indexers\city_indexer.py | docstring | 1 | """CityIndexer — index city entries with biome / service attributes.""" | WARNING | Other_NonASCII |
| 1404 | core\knowledge\indexers\hunt_indexer.py | docstring | 1 | """HuntIndexer — index hunt entries with biome / route / circular hints.""" | WARNING | Other_NonASCII |
| 1405 | core\knowledge\indexers\quest_indexer.py | docstring | 1 | """QuestIndexer — index quest entries by style, theme, difficulty.""" | WARNING | Other_NonASCII |
| 1406 | core\knowledge\indexers\region_indexer.py | docstring | 1 | """RegionIndexer — index generic region / dungeon / structure entries.""" | WARNING | Other_NonASCII |
| 1407 | core\knowledge\indexers\__init__.py | docstring | 1 | """Knowledge indexers — build per-type indexes for fast retrieval.""" | WARNING | Other_NonASCII |
| 1408 | core\knowledge\models\knowledge_dataset.py | other_non_ascii | 2 | KnowledgeDataset — the on-disk / in-memory dataset produced by DatasetBuilder. | INFO | Other_NonASCII |
| 1409 | core\knowledge\models\knowledge_entry.py | other_non_ascii | 2 | KnowledgeEntry — base unit of the knowledge dataset. | INFO | Other_NonASCII |
| 1410 | core\knowledge\models\knowledge_entry.py | comment | 138 | # Unknown type — fall back to hunt. | WARNING | Other_NonASCII |
| 1411 | core\knowledge\models\knowledge_query_result.py | other_non_ascii | 2 | KnowledgeQueryResult — container for the result of a knowledge query. | INFO | Other_NonASCII |
| 1412 | core\knowledge\models\knowledge_similarity.py | other_non_ascii | 6 | - `cosine_similarity` — vector-based, works on dicts of token->weight. | INFO | Other_NonASCII |
| 1413 | core\knowledge\models\knowledge_similarity.py | other_non_ascii | 7 | - `jaccard_similarity` — set-based on tokens. | INFO | Other_NonASCII |
| 1414 | core\knowledge\models\knowledge_similarity.py | other_non_ascii | 8 | - `pattern_similarity` — heuristic for shared structural patterns. | INFO | Other_NonASCII |
| 1415 | core\knowledge\models\knowledge_similarity.py | other_non_ascii | 9 | - `hybrid_similarity` — weighted blend of the three. | INFO | Other_NonASCII |
| 1416 | core\learning\blueprint_catalog.py | other_non_ascii | 2 | HITO 17 — Blueprint Catalog: Persistent storage and retrieval of learned blueprints. | INFO | Other_NonASCII |
| 1417 | core\learning\blueprint_learner.py | other_non_ascii | 2 | HITO 17 — Blueprint Learner: Automatic blueprint learning from real OTBM maps. | INFO | Other_NonASCII |
| 1418 | core\learning\blueprint_learner.py | other_non_ascii | 5 | OTBM → WorldModel → MapAnalyzer → BlueprintExtractor → PatternMiner → SimilarityEngine → BlueprintCatalog | INFO | Other_NonASCII |
| 1419 | core\learning\blueprint_learner.py | other_non_ascii | 161 | OTBM → WorldModel → MapAnalysis → BlueprintExtractor | INFO | Other_NonASCII |
| 1420 | core\learning\blueprint_learner.py | other_non_ascii | 162 | → PatternMiner → SimilarityEngine → BlueprintRanker → Catalog | INFO | Other_NonASCII |
| 1421 | core\learning\blueprint_ranker.py | other_non_ascii | 2 | HITO 17 — Blueprint Ranker: Ranks blueprints by quality, relevance, and utility. | INFO | Other_NonASCII |
| 1422 | core\learning\pattern_miner.py | other_non_ascii | 2 | HITO 17 — Pattern Miner: Mines recurring architectural patterns from blueprints and analyses. | INFO | Other_NonASCII |
| 1423 | core\lua\lua_generator.py | other_non_ascii | 2 | MVP V0.1 — Lua Generator | INFO | Other_NonASCII |
| 1424 | core\lua\lua_generator.py | comment | 56 | gen.generate()                              # no input → empty script | WARNING | Other_NonASCII |
| 1425 | core\lua\lua_generator.py | comment | 57 | gen.generate(world)                         # WorldModel only — spawn | WARNING | Other_NonASCII |
| 1426 | core\lua\__init__.py | other_non_ascii | 2 | MVP V0.1 — Lua Generator | INFO | Other_NonASCII |
| 1427 | core\observability\health.py | comment | 78 | # ── Individual check functions ────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 1428 | core\observability\health.py | comment | 282 | # ── Aggregator ────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 1429 | core\otbm\binary_writer.py | other_non_ascii | 2 | OTBM binary writer — safe range-validated struct.pack helpers. | INFO | Other_NonASCII |
| 1430 | core\otbm\binary_writer.py | other_non_ascii | 7 | * Pre-validation of every value (0 <= uint8 <= 255, 0 <= uint16 <= 65535, …) | INFO | Other_NonASCII |
| 1431 | core\otbm\binary_writer.py | comment | 76 | except Exception:  # pragma: no cover — defensive | WARNING | Other_NonASCII |
| 1432 | core\otbm\byte_validator.py | other_non_ascii | 2 | byte_validator.py — HITO 26.1A | INFO | Other_NonASCII |
| 1433 | core\otbm\house_encoder.py | other_non_ascii | 2 | House Encoder — prepara datos de houses para houses.xml compatible con OTServBR. | INFO | Other_NonASCII |
| 1434 | core\otbm\house_encoder.py | other_non_ascii | 18 | Prepara datos de houses para exportación OTBM + houses.xml. | INFO | Latin_Extended |
| 1435 | core\otbm\house_encoder.py | comment | 59 | # Detectar por estructuras con categoría house | WARNING | Latin_Extended |
| 1436 | core\otbm\item_decoder.py | other_non_ascii | 2 | Item Decoder — converts decoded OTBM ITEM nodes into structured Item objects. | INFO | Other_NonASCII |
| 1437 | core\otbm\item_encoder.py | other_non_ascii | 2 | Item Encoder — convierte Items de WorldModel a nodos OTBM ITEM. | INFO | Other_NonASCII |
| 1438 | core\otbm\item_encoder.py | other_non_ascii | 8 | ↓ | INFO | Other_NonASCII |
| 1439 | core\otbm\item_encoder.py | other_non_ascii | 66 | ground_id: ID numérico del ground. | INFO | Latin_Extended |
| 1440 | core\otbm\node_decoder.py | other_non_ascii | 2 | Node Decoder — decodes individual OTBM node types into structured Python dicts. | INFO | Other_NonASCII |
| 1441 | core\otbm\node_decoder.py | other_non_ascii | 5 | - ROOT → map header info | INFO | Other_NonASCII |
| 1442 | core\otbm\node_decoder.py | other_non_ascii | 6 | - MAP_DATA → description, spawn file, house file | INFO | Other_NonASCII |
| 1443 | core\otbm\node_decoder.py | other_non_ascii | 7 | - TILE_AREA → base coords + child tiles | INFO | Other_NonASCII |
| 1444 | core\otbm\node_decoder.py | other_non_ascii | 8 | - TILE → tile position, flags, ground + items | INFO | Other_NonASCII |
| 1445 | core\otbm\node_decoder.py | other_non_ascii | 9 | - ITEM → item_id + attributes | INFO | Other_NonASCII |
| 1446 | core\otbm\node_decoder.py | other_non_ascii | 10 | - SPAWNS → container | INFO | Other_NonASCII |
| 1447 | core\otbm\node_decoder.py | other_non_ascii | 11 | - SPAWN_AREA → center, radius + monster children | INFO | Other_NonASCII |
| 1448 | core\otbm\node_decoder.py | other_non_ascii | 12 | - MONSTER → name, direction, spawntime | INFO | Other_NonASCII |
| 1449 | core\otbm\node_decoder.py | other_non_ascii | 13 | - TOWNS → container | INFO | Other_NonASCII |
| 1450 | core\otbm\node_decoder.py | other_non_ascii | 14 | - TOWN → town_id, name, temple pos | INFO | Other_NonASCII |
| 1451 | core\otbm\node_decoder.py | other_non_ascii | 15 | - WAYPOINTS → container | INFO | Other_NonASCII |
| 1452 | core\otbm\node_decoder.py | other_non_ascii | 16 | - WAYPOINT → name, position | INFO | Other_NonASCII |
| 1453 | core\otbm\node_decoder.py | other_non_ascii | 17 | - HOUSETILE → position, house_id + items | INFO | Other_NonASCII |
| 1454 | core\otbm\node_decoder.py | comment | 690 | # Unknown attribute — skip 1 byte value | WARNING | Other_NonASCII |
| 1455 | core\otbm\otbm_exporter.py | other_non_ascii | 2 | OTBMExporter — fachada principal para exportar WorldModel → .otbm. | INFO | Other_NonASCII |
| 1456 | core\otbm\otbm_exporter.py | other_non_ascii | 10 | ↓ | INFO | Other_NonASCII |
| 1457 | core\otbm\otbm_exporter.py | other_non_ascii | 12 | ↓ | INFO | Other_NonASCII |
| 1458 | core\otbm\otbm_exporter.py | other_non_ascii | 14 | ↓ | INFO | Other_NonASCII |
| 1459 | core\otbm\otbm_exporter.py | other_non_ascii | 15 | Serializer → Writer | INFO | Other_NonASCII |
| 1460 | core\otbm\otbm_exporter.py | other_non_ascii | 16 | ↓ | INFO | Other_NonASCII |
| 1461 | core\otbm\otbm_exporter.py | other_non_ascii | 57 | También genera archivos auxiliares (monster.xml, houses.xml, waypoints.xml) | INFO | Latin_Extended |
| 1462 | core\otbm\otbm_exporter.py | other_non_ascii | 58 | y un reporte JSON con estadísticas. | INFO | Latin_Extended |
| 1463 | core\otbm\otbm_exporter.py | other_non_ascii | 86 | Exporta WorldModel → .otbm + XMLs auxiliares. | INFO | Other_NonASCII |
| 1464 | core\otbm\otbm_exporter.py | other_non_ascii | 91 | generate_report: Si True, también genera report.json. | INFO | Latin_Extended |
| 1465 | core\otbm\otbm_exporter.py | other_non_ascii | 94 | Dict con estadísticas de exportación. | INFO | Latin_Extended |
| 1466 | core\otbm\otbm_exporter.py | comment | 128 | # 5. Reporte de exportación | WARNING | Latin_Extended |
| 1467 | core\otbm\otbm_exporter.py | comment | 180 | # Validación | WARNING | Latin_Extended |
| 1468 | core\otbm\otbm_exporter.py | other_non_ascii | 191 | OtbmValidationResult con estado y estadísticas. | INFO | Latin_Extended |
| 1469 | core\otbm\otbm_exporter.py | comment | 196 | # Generación de XMLs auxiliares | WARNING | Latin_Extended |
| 1470 | core\otbm\otbm_importer.py | other_non_ascii | 2 | OTBM Importer — reads .otbm files and converts them to WorldModel. | INFO | Other_NonASCII |
| 1471 | core\otbm\otbm_nodes.py | other_non_ascii | 2 | OTBM Nodes — constantes de tipos de nodo y atributos del formato OTBM. | INFO | Other_NonASCII |
| 1472 | core\otbm\otbm_parser.py | other_non_ascii | 2 | OTBM Parser — Low-level parser for OTBM binary node structures. | INFO | Other_NonASCII |
| 1473 | core\otbm\otbm_parser.py | comment | 231 | # Children are NOT extracted here — NodeDecoder handles payload parsing | WARNING | Other_NonASCII |
| 1474 | core\otbm\otbm_parser.py | comment | 240 | # Children are NOT extracted here — NodeDecoder handles payload parsing | WARNING | Other_NonASCII |
| 1475 | core\otbm\otbm_parser.py | comment | 491 | # Unknown attribute — break | WARNING | Other_NonASCII |
| 1476 | core\otbm\otbm_serializer.py | other_non_ascii | 58 | ├── MAP_DATA (description, spawn_file, house_file) | INFO | Other_NonASCII |
| 1477 | core\otbm\otbm_serializer.py | other_non_ascii | 59 | │     ├── TILE_AREA (base_x, base_y, base_z) | INFO | Other_NonASCII |
| 1478 | core\otbm\otbm_serializer.py | other_non_ascii | 60 | │     │     ├── TILE (offset_x, offset_y [, flags]) | INFO | Other_NonASCII |
| 1479 | core\otbm\otbm_serializer.py | other_non_ascii | 61 | │     │     │     ├── ITEM (ground) | INFO | Other_NonASCII |
| 1480 | core\otbm\otbm_serializer.py | other_non_ascii | 62 | │     │     │     ├── ITEM (items...) | INFO | Other_NonASCII |
| 1481 | core\otbm\otbm_serializer.py | other_non_ascii | 63 | │     │     │     └── ... | INFO | Other_NonASCII |
| 1482 | core\otbm\otbm_serializer.py | other_non_ascii | 64 | │     │     └── ... | INFO | Other_NonASCII |
| 1483 | core\otbm\otbm_serializer.py | other_non_ascii | 65 | │     ├── SPAWNS | INFO | Other_NonASCII |
| 1484 | core\otbm\otbm_serializer.py | other_non_ascii | 66 | │     │     ├── SPAWN_AREA (center_x, center_y, z, radius) | INFO | Other_NonASCII |
| 1485 | core\otbm\otbm_serializer.py | other_non_ascii | 67 | │     │     │     ├── MONSTER (name, direction, spawntime) | INFO | Other_NonASCII |
| 1486 | core\otbm\otbm_serializer.py | other_non_ascii | 68 | │     │     │     └── ... | INFO | Other_NonASCII |
| 1487 | core\otbm\otbm_serializer.py | other_non_ascii | 69 | │     │     └── ... | INFO | Other_NonASCII |
| 1488 | core\otbm\otbm_serializer.py | other_non_ascii | 70 | │     ├── TOWNS | INFO | Other_NonASCII |
| 1489 | core\otbm\otbm_serializer.py | other_non_ascii | 71 | │     │     ├── TOWN (town_id, name, temple_x, temple_y, temple_z) | INFO | Other_NonASCII |
| 1490 | core\otbm\otbm_serializer.py | other_non_ascii | 72 | │     │     └── ... | INFO | Other_NonASCII |
| 1491 | core\otbm\otbm_serializer.py | other_non_ascii | 73 | │     └── WAYPOINTS | INFO | Other_NonASCII |
| 1492 | core\otbm\otbm_serializer.py | other_non_ascii | 74 | │           ├── WAYPOINT (name, x, y, z) | INFO | Other_NonASCII |
| 1493 | core\otbm\otbm_serializer.py | other_non_ascii | 75 | │           └── ... | INFO | Other_NonASCII |
| 1494 | core\otbm\otbm_serializer.py | other_non_ascii | 753 | description="Generated by OpenTibiaBR RME Agent — Hunt Area", | INFO | Other_NonASCII |
| 1495 | core\otbm\otbm_validator.py | comment | 60 | # HITO 26.1A — own a ByteValidator for post-write byte checks | WARNING | Other_NonASCII |
| 1496 | core\otbm\spawn_encoder.py | other_non_ascii | 2 | Spawn Encoder — convierte spawns de WorldModel a nodos OTBM SPAWN_AREA + MONSTER. | INFO | Other_NonASCII |
| 1497 | core\otbm\spawn_encoder.py | other_non_ascii | 4 | Genera nodos OTBM para spawns y también prepara datos para monster.xml. | INFO | Latin_Extended |
| 1498 | core\otbm\spawn_encoder.py | other_non_ascii | 6 | No incrusta lógica Lua — solo produce nodos OTBM binarios. | INFO | Other_NonASCII, Latin_Extended |
| 1499 | core\otbm\spawn_encoder.py | other_non_ascii | 25 | ↓ | INFO | Other_NonASCII |
| 1500 | core\otbm\spawn_encoder.py | other_non_ascii | 27 | └── MONSTER (name, direction, spawntime) | INFO | Other_NonASCII |
| 1501 | core\otbm\spawn_encoder.py | other_non_ascii | 63 | Envuelve múltiples spawns en un nodo SPAWNS contenedor. | INFO | Latin_Extended |
| 1502 | core\otbm\spawn_encoder.py | comment | 94 | # También revisar spawns a nivel de world_model | WARNING | Latin_Extended |
| 1503 | core\otbm\tile_decoder.py | other_non_ascii | 2 | Tile Decoder — converts decoded OTBM TILE/TILE_AREA nodes into WorldModel Tile objects. | INFO | Other_NonASCII |
| 1504 | core\otbm\tile_encoder.py | comment | 318 | # Dict with 'name' key — look up in our tables | WARNING | Other_NonASCII |
| 1505 | core\otbm\waypoint_encoder.py | other_non_ascii | 2 | Waypoint Encoder — exporta waypoints del WorldModel a nodos OTBM. | INFO | Other_NonASCII |
| 1506 | core\otbm\waypoint_encoder.py | other_non_ascii | 6 | También prepara datos para waypoints.xml. | INFO | Latin_Extended |
| 1507 | core\otbm\waypoint_encoder.py | other_non_ascii | 22 | - Waypoints explícitos en world_model.waypoints | INFO | Latin_Extended |
| 1508 | core\otbm\waypoint_encoder.py | comment | 41 | # 1. Waypoints explícitos | WARNING | Latin_Extended |
| 1509 | core\otbm\waypoint_encoder.py | comment | 68 | # Usar centro de tiles de la región o default | WARNING | Latin_Extended |
| 1510 | core\otbm\waypoint_encoder.py | other_non_ascii | 124 | Envuelve múltiples waypoints en nodo WAYPOINTS. | INFO | Latin_Extended |
| 1511 | core\otbm\world_builder.py | other_non_ascii | 2 | World Builder — assembles a WorldModel from decoded OTBM data. | INFO | Other_NonASCII |
| 1512 | core\pipeline\full_pipeline.py | other_non_ascii | 52 | Complete RME pipeline: Prompt → World → Playtest → Balance → Campaign → Export. | INFO | Other_NonASCII |
| 1513 | core\pipeline\full_pipeline.py | other_non_ascii | 55 | 1. Parse prompt → extract theme, level_range, params | INFO | Other_NonASCII |
| 1514 | core\planner\prompt_interpreter.py | other_non_ascii | 21 | if "city" in lower or "ciudad" in lower or "expansión" in lower: | INFO | Latin_Extended |
| 1515 | core\planner\prompt_interpreter.py | other_non_ascii | 36 | if "expansión" in lower or "expansion" in lower: | INFO | Latin_Extended |
| 1516 | core\planner\world_validator.py | other_non_ascii | 25 | errors.append(f"La ciudad {city.get('name')} tiene población demasiado baja.") | INFO | Latin_Extended |
| 1517 | core\planner\world_validator.py | other_non_ascii | 29 | errors.append(f"La dificultad de {dungeon.get('name')} no es válida.") | INFO | Latin_Extended |
| 1518 | core\playtest\combat_simulator.py | other_non_ascii | 2 | Combat Simulator — Models real Tibia-style combat for 5 vocations. | INFO | Other_NonASCII |
| 1519 | core\playtest\difficulty_evaluator.py | other_non_ascii | 2 | Difficulty Evaluator — Rates zone difficulty and balance. | INFO | Other_NonASCII |
| 1520 | core\playtest\difficulty_evaluator.py | comment | 75 | # ── Spawn Density Score ── | WARNING | Other_NonASCII |
| 1521 | core\playtest\difficulty_evaluator.py | comment | 93 | # ── Level Ratio Score ── | WARNING | Other_NonASCII |
| 1522 | core\playtest\difficulty_evaluator.py | comment | 110 | # ── Boss Difficulty ── | WARNING | Other_NonASCII |
| 1523 | core\playtest\difficulty_evaluator.py | comment | 113 | # ── Healing Availability ── | WARNING | Other_NonASCII |
| 1524 | core\playtest\difficulty_evaluator.py | comment | 116 | # ── Composite Score ── | WARNING | Other_NonASCII |
| 1525 | core\playtest\difficulty_evaluator.py | comment | 120 | # ── Difficulty Label ── | WARNING | Other_NonASCII |
| 1526 | core\playtest\loot_simulator.py | other_non_ascii | 2 | Loot Simulator — Calculates loot yield per hour for hunt areas. | INFO | Other_NonASCII |
| 1527 | core\playtest\loot_simulator.py | comment | 56 | # ── Common Loot Tables ── | WARNING | Other_NonASCII |
| 1528 | core\playtest\party_bot.py | other_non_ascii | 2 | Party Bot — Simulates a party of player bots hunting together. | INFO | Other_NonASCII |
| 1529 | core\playtest\player_bot.py | other_non_ascii | 2 | Player Bot — Simulates individual player characters across all vocations. | INFO | Other_NonASCII |
| 1530 | core\playtest\player_bot.py | other_non_ascii | 110 | that processes one combat turn (≈2 seconds in Tibia). | INFO | Other_NonASCII |
| 1531 | core\playtest\playtest_engine.py | other_non_ascii | 2 | Playtest Engine — Main orchestrator for automated world playtesting. | INFO | Other_NonASCII |
| 1532 | core\playtest\playtest_engine.py | comment | 27 | # ── Default Monster Database (real Tibia stats) ── | WARNING | Other_NonASCII |
| 1533 | core\playtest\playtest_engine.py | comment | 191 | # ── Boss Templates ── | WARNING | Other_NonASCII |
| 1534 | core\playtest\playtest_engine.py | comment | 260 | # ── Step 1: Extract world data ── | WARNING | Other_NonASCII |
| 1535 | core\playtest\playtest_engine.py | comment | 266 | # ── Step 2: Build monster pool ── | WARNING | Other_NonASCII |
| 1536 | core\playtest\playtest_engine.py | comment | 273 | # ── Step 3: Run combat simulation ── | WARNING | Other_NonASCII |
| 1537 | core\playtest\playtest_engine.py | comment | 287 | # ── Step 4: Calculate metrics ── | WARNING | Other_NonASCII |
| 1538 | core\playtest\playtest_engine.py | comment | 305 | # ── Step 5: Pathfinding analysis ── | WARNING | Other_NonASCII |
| 1539 | core\playtest\playtest_engine.py | comment | 309 | # ── Step 6: Survival analysis ── | WARNING | Other_NonASCII |
| 1540 | core\playtest\playtest_engine.py | comment | 317 | # ── Step 7: Difficulty analysis ── | WARNING | Other_NonASCII |
| 1541 | core\playtest\playtest_engine.py | comment | 332 | # ── Step 8: Progression analysis ── | WARNING | Other_NonASCII |
| 1542 | core\playtest\playtest_engine.py | comment | 342 | # ── Step 9: Collect issues ── | WARNING | Other_NonASCII |
| 1543 | core\playtest\playtest_engine.py | comment | 350 | # ── Step 10: Generate report ── | WARNING | Other_NonASCII |
| 1544 | core\playtest\progression_analyzer.py | other_non_ascii | 2 | Progression Analyzer — Evaluates XP/hour, level progression, and game pacing. | INFO | Other_NonASCII |
| 1545 | core\playtest\report_generator.py | other_non_ascii | 2 | Report Generator — Produces the final playtest_report.json. | INFO | Other_NonASCII |
| 1546 | core\playtest\report_generator.py | comment | 110 | # ── Playability Checks ── | WARNING | Other_NonASCII |
| 1547 | core\playtest\report_generator.py | comment | 142 | # ── Recommendations ── | WARNING | Other_NonASCII |
| 1548 | core\playtest\report_generator.py | comment | 146 | # ── Build Report ── | WARNING | Other_NonASCII |
| 1549 | core\playtest\route_simulator.py | other_non_ascii | 2 | Route Simulator — Evaluates hunting route efficiency. | INFO | Other_NonASCII |
| 1550 | core\playtest\route_simulator.py | other_non_ascii | 229 | warnings.append(f"Route caused {metrics.deaths} death(s) — too dangerous") | INFO | Other_NonASCII |
| 1551 | core\playtest\survival_analyzer.py | other_non_ascii | 2 | Survival Analyzer — Evaluates player survival across zones. | INFO | Other_NonASCII |
| 1552 | core\playtest\survival_analyzer.py | comment | 113 | escape_time = safe_distance  # 1 step ≈ 1 second | WARNING | Other_NonASCII |
| 1553 | core\playtest\__init__.py | other_non_ascii | 2 | Playtest Engine — Automated playtesting for worlds generated by Agente RME. | INFO | Other_NonASCII |
| 1554 | core\preview\minimap_renderer.py | other_non_ascii | 2 | Minimap Renderer — genera preview_minimap.png con escalado variable. | INFO | Other_NonASCII |
| 1555 | core\preview\minimap_renderer.py | other_non_ascii | 5 | 4x  → tile_size=4  (miniatura) | INFO | Other_NonASCII |
| 1556 | core\preview\minimap_renderer.py | other_non_ascii | 6 | 8x  → tile_size=8  (mediano) | INFO | Other_NonASCII |
| 1557 | core\preview\minimap_renderer.py | other_non_ascii | 7 | 16x → tile_size=16 (detallado) | INFO | Other_NonASCII |
| 1558 | core\preview\minimap_renderer.py | comment | 26 | # Escalas disponibles: nombre → tile_size | WARNING | Other_NonASCII |
| 1559 | core\preview\minimap_renderer.py | other_non_ascii | 36 | Legacy MinimapRenderer (V1) — mantiene compatibilidad con core/__init__.py. | INFO | Other_NonASCII |
| 1560 | core\preview\minimap_renderer.py | other_non_ascii | 154 | Ruta del archivo guardado, o None si falló. | INFO | Latin_Extended |
| 1561 | core\preview\palette.py | other_non_ascii | 5 | Usado por preview_renderer.py para pintar cada píxel. | INFO | Latin_Extended |
| 1562 | core\preview\palette.py | comment | 9 | GROUND = (180, 180, 180)  # Terreno normal — gris claro | WARNING | Other_NonASCII |
| 1563 | core\preview\palette.py | comment | 10 | WALL = (80, 80, 80)  # Pared/muro — gris oscuro | WARNING | Other_NonASCII |
| 1564 | core\preview\palette.py | comment | 11 | WATER = (0, 100, 255)  # Agua — azul | WARNING | Other_NonASCII |
| 1565 | core\preview\palette.py | comment | 12 | SPAWN = (255, 0, 0)  # Spawn de monstruo — rojo | WARNING | Other_NonASCII |
| 1566 | core\preview\palette.py | comment | 13 | DECORATION = (0, 255, 0)  # Decoración — verde | WARNING | Other_NonASCII, Latin_Extended |
| 1567 | core\preview\palette.py | comment | 14 | BOSS = (255, 128, 0)  # Boss — naranja | WARNING | Other_NonASCII |
| 1568 | core\preview\palette.py | comment | 15 | TEMPLE = (255, 255, 0)  # Estructura tipo templo — amarillo | WARNING | Other_NonASCII |
| 1569 | core\preview\palette.py | comment | 16 | EMPTY = (20, 20, 20)  # Vacío — casi negro | WARNING | Other_NonASCII, Latin_Extended |
| 1570 | core\preview\palette.py | comment | 17 | STRUCTURE = (200, 150, 50)  # Otra estructura — marrón | WARNING | Other_NonASCII, Latin_Extended |
| 1571 | core\preview\palette.py | comment | 19 | # Mapa de IDs de item conocidos para clasificación | WARNING | Latin_Extended |
| 1572 | core\preview\palette.py | comment | 20 | # ID → nombre descriptivo (usado para determinar color) | WARNING | Other_NonASCII |
| 1573 | core\preview\palette.py | other_non_ascii | 81 | Determina el color de un tile según su ground ID. | INFO | Latin_Extended |
| 1574 | core\preview\palette.py | comment | 101 | # IDs desconocidos → terreno por defecto | WARNING | Other_NonASCII |
| 1575 | core\preview\palette.py | comment | 117 | return DECORATION  # Por defecto, cualquier item es decoración | WARNING | Latin_Extended |
| 1576 | core\preview\preview_generator.py | other_non_ascii | 2 | HITO 9 REAL — Preview Generator V1 | INFO | Other_NonASCII |
| 1577 | core\preview\preview_generator.py | other_non_ascii | 7 | WorldModel → PNG (preview.png, preview_minimap.png) | INFO | Other_NonASCII |
| 1578 | core\preview\preview_generator.py | other_non_ascii | 8 | WorldModel → JSON (preview.json) | INFO | Other_NonASCII |
| 1579 | core\preview\preview_generator.py | other_non_ascii | 16 | ↓ | INFO | Other_NonASCII |
| 1580 | core\preview\preview_generator.py | other_non_ascii | 18 | ↓ | INFO | Other_NonASCII |
| 1581 | core\preview\preview_generator.py | other_non_ascii | 20 | ↓ | INFO | Other_NonASCII |
| 1582 | core\preview\preview_generator.py | other_non_ascii | 72 | También se puede usar paso a paso: | INFO | Latin_Extended |
| 1583 | core\preview\preview_generator.py | other_non_ascii | 83 | tile_size: Tamaño de cada tile en píxeles para preview.png. | INFO | Latin_Extended |
| 1584 | core\preview\preview_generator.py | other_non_ascii | 109 | z: Capa Z a renderizar. None = automático. | INFO | Latin_Extended |
| 1585 | core\preview\preview_generator.py | other_non_ascii | 159 | z: Capa Z. None = automático. | INFO | Latin_Extended |
| 1586 | core\preview\preview_generator.py | other_non_ascii | 162 | Ruta del archivo, o None si falló. | INFO | Latin_Extended |
| 1587 | core\preview\preview_generator.py | other_non_ascii | 218 | Ruta del archivo, o None si falló. | INFO | Latin_Extended |
| 1588 | core\preview\preview_generator.py | other_non_ascii | 244 | Genera el reporte de estadísticas del mapa. | INFO | Latin_Extended |
| 1589 | core\preview\preview_generator.py | other_non_ascii | 250 | Dict con estadísticas. | INFO | Latin_Extended |
| 1590 | core\preview\preview_generator.py | other_non_ascii | 260 | Genera preview.json con estadísticas. | INFO | Latin_Extended |
| 1591 | core\preview\preview_generator.py | other_non_ascii | 267 | Ruta del archivo, o None si falló. | INFO | Latin_Extended |
| 1592 | core\preview\preview_generator.py | docstring | 287 | """Añade una leyenda de colores en la parte inferior de la imagen.""" | WARNING | Latin_Extended |
| 1593 | core\preview\preview_generator.py | comment | 290 | # Región para leyenda | WARNING | Latin_Extended |
| 1594 | core\preview\preview_generator.py | comment | 306 | # Título | WARNING | Latin_Extended |
| 1595 | core\preview\preview_generator.py | other_non_ascii | 329 | """Fallo a ASCII si PIL no está disponible. | INFO | Latin_Extended |
| 1596 | core\preview\preview_generator.py | other_non_ascii | 344 | lines.append(f"Z: {bounds['min_z']}–{bounds['max_z']}") | INFO | Other_NonASCII |
| 1597 | core\preview\preview_renderer.py | other_non_ascii | 2 | Preview Renderer — núcleo de renderizado de tiles a píxeles. | INFO | Other_NonASCII, Latin_Extended |
| 1598 | core\preview\preview_renderer.py | other_non_ascii | 8 | WorldModel → renderizar tiles → imagen PIL → PNG | INFO | Other_NonASCII |
| 1599 | core\preview\preview_renderer.py | other_non_ascii | 65 | 3. Ground (gris) / Wall (gris oscuro) según ground ID | INFO | Latin_Extended |
| 1600 | core\preview\preview_renderer.py | other_non_ascii | 66 | 4. Vacío (casi negro) si no hay nada | INFO | Latin_Extended |
| 1601 | core\preview\preview_renderer.py | other_non_ascii | 118 | tile_size: Tamaño de cada tile en píxeles. | INFO | Latin_Extended |
| 1602 | core\preview\preview_renderer.py | other_non_ascii | 122 | Imagen PIL, o None si PIL no está disponible. | INFO | Latin_Extended |
| 1603 | core\preview\preview_renderer.py | other_non_ascii | 171 | Renderiza todas las capas Z como imágenes separadas. | INFO | Latin_Extended |
| 1604 | core\preview\preview_renderer.py | other_non_ascii | 175 | tile_size: Tamaño de cada tile en píxeles. | INFO | Latin_Extended |
| 1605 | core\preview\preview_renderer.py | other_non_ascii | 206 | Dibuja rectángulos de estructura sobre la imagen. | INFO | Latin_Extended |
| 1606 | core\preview\preview_renderer.py | other_non_ascii | 213 | tile_size: Tamaño del tile en píxeles. | INFO | Latin_Extended |
| 1607 | core\preview\preview_report.py | other_non_ascii | 2 | Preview Report — genera preview.json con estadísticas del mapa. | INFO | Other_NonASCII, Latin_Extended |
| 1608 | core\preview\preview_report.py | other_non_ascii | 25 | Genera un reporte JSON-serializable con estadísticas del WorldModel. | INFO | Latin_Extended |
| 1609 | core\preview\__init__.py | other_non_ascii | 2 | core.preview — sistema de preview de mapas. | INFO | Other_NonASCII |
| 1610 | core\preview\__init__.py | other_non_ascii | 5 | palette.py            → colores y clasificación de IDs | INFO | Other_NonASCII, Latin_Extended |
| 1611 | core\preview\__init__.py | other_non_ascii | 6 | preview_renderer.py   → renderizado de tiles a píxeles | INFO | Other_NonASCII, Latin_Extended |
| 1612 | core\preview\__init__.py | other_non_ascii | 7 | minimap_renderer.py   → minimapa escalado | INFO | Other_NonASCII |
| 1613 | core\preview\__init__.py | other_non_ascii | 8 | preview_report.py     → reporte JSON de estadísticas | INFO | Other_NonASCII, Latin_Extended |
| 1614 | core\preview\__init__.py | other_non_ascii | 9 | preview_generator.py  → orquestador principal | INFO | Other_NonASCII |
| 1615 | core\preview\__init__.py | comment | 16 | # → output/preview.png | WARNING | Other_NonASCII |
| 1616 | core\preview\__init__.py | comment | 17 | # → output/preview_minimap.png | WARNING | Other_NonASCII |
| 1617 | core\preview\__init__.py | comment | 18 | # → output/preview.json | WARNING | Other_NonASCII |
| 1618 | core\procedural\continent_generator.py | comment | 63 | # ContinentResult — what the generator produced | WARNING | Other_NonASCII |
| 1619 | core\procedural\terrain_generator.py | other_non_ascii | 10 | The terrain generator is a "decorator" — it never removes a tile that | INFO | Other_NonASCII |
| 1620 | core\procedural\terrain_generator.py | other_non_ascii | 553 | The generator does NOT change the ground — it only adds items to | INFO | Other_NonASCII |
| 1621 | core\procedural\__init__.py | other_non_ascii | 9 | biome_generator    — biome surface (grass, sand, snow, ...) | INFO | Other_NonASCII |
| 1622 | core\procedural\__init__.py | other_non_ascii | 10 | terrain_generator  — mountains, hills, water bodies, lava, forest | INFO | Other_NonASCII |
| 1623 | core\procedural\__init__.py | other_non_ascii | 11 | road_generator     — road network + city street grid + bridges | INFO | Other_NonASCII |
| 1624 | core\procedural\__init__.py | other_non_ascii | 12 | river_generator    — flowing rivers with banks | INFO | Other_NonASCII |
| 1625 | core\procedural\__init__.py | other_non_ascii | 13 | continent_generator — top-level orchestrator (plan -> world) | INFO | Other_NonASCII |
| 1626 | core\procedural\__init__.py | other_non_ascii | 14 | world_synthesizer  — final assembly + validation + merging | INFO | Other_NonASCII |
| 1627 | core\release\documentation_builder.py | other_non_ascii | 27 | - README.md        — Overview, install, usage | INFO | Other_NonASCII |
| 1628 | core\release\documentation_builder.py | other_non_ascii | 28 | - CHANGELOG.md     — Version history, changes added | INFO | Other_NonASCII |
| 1629 | core\release\documentation_builder.py | other_non_ascii | 29 | - MAP_GUIDE.md     — Zone guide, spawns, maps, difficulty | INFO | Other_NonASCII |
| 1630 | core\release\documentation_builder.py | other_non_ascii | 30 | - NPC_LIST.md      — All NPCs with positions | INFO | Other_NonASCII |
| 1631 | core\release\documentation_builder.py | other_non_ascii | 31 | - MONSTER_LIST.md  — All monsters with XP, loot, levels | INFO | Other_NonASCII |
| 1632 | core\release\documentation_builder.py | other_non_ascii | 32 | - SPAWN_TABLE.md   — Detailed spawn distribution | INFO | Other_NonASCII |
| 1633 | core\release\documentation_builder.py | comment | 111 | return f"""# {name.title()} — RME Expansion | WARNING | Other_NonASCII |
| 1634 | core\release\documentation_builder.py | other_non_ascii | 125 | - `{name}.otbm` — Main map file | INFO | Other_NonASCII |
| 1635 | core\release\documentation_builder.py | other_non_ascii | 126 | - `{name}.lua` — Lua scripts (if applicable) | INFO | Other_NonASCII |
| 1636 | core\release\documentation_builder.py | other_non_ascii | 127 | - `monster.xml` — Monster spawn configuration | INFO | Other_NonASCII |
| 1637 | core\release\documentation_builder.py | other_non_ascii | 128 | - `npc.xml` — NPC definitions | INFO | Other_NonASCII |
| 1638 | core\release\documentation_builder.py | other_non_ascii | 129 | - `zones.xml` — Zone metadata | INFO | Other_NonASCII |
| 1639 | core\release\documentation_builder.py | other_non_ascii | 130 | - `MAP_GUIDE.md` — Complete zone guide | INFO | Other_NonASCII |
| 1640 | core\release\documentation_builder.py | other_non_ascii | 131 | - `SPAWN_TABLE.md` — Detailed spawn distribution | INFO | Other_NonASCII |
| 1641 | core\release\documentation_builder.py | other_non_ascii | 132 | - `MONSTER_LIST.md` — Monster stats and loot | INFO | Other_NonASCII |
| 1642 | core\release\documentation_builder.py | other_non_ascii | 133 | - `NPC_LIST.md` — NPC locations | INFO | Other_NonASCII |
| 1643 | core\release\documentation_builder.py | other_non_ascii | 134 | - `CHANGELOG.md` — Version history | INFO | Other_NonASCII |
| 1644 | core\release\documentation_builder.py | comment | 183 | lines = [f"# {name.title()} — Map Guide", ""] | WARNING | Other_NonASCII |
| 1645 | core\release\documentation_builder.py | other_non_ascii | 251 | lines.append("\| _No towns defined_ \| — \| — \| — \|") | INFO | Other_NonASCII |
| 1646 | core\spawn\spawn_generator.py | other_non_ascii | 2 | MVP V0.1 — Spawn Generator | INFO | Other_NonASCII |
| 1647 | core\spawn\spawn_generator.py | other_non_ascii | 10 | 1. ``generate(rooms, theme_monsters, level_range, base_z)`` — original | INFO | Other_NonASCII |
| 1648 | core\spawn\spawn_generator.py | other_non_ascii | 14 | 2. ``generate_for_world(world)`` — convenience wrapper that derives a | INFO | Other_NonASCII |
| 1649 | core\spawn\spawn_generator.py | other_non_ascii | 165 | * ``None`` → returns an empty plan. | INFO | Other_NonASCII |
| 1650 | core\spawn\spawn_generator.py | other_non_ascii | 166 | * A bare dict with a ``"spawns"`` key → coerced into a plan. | INFO | Other_NonASCII |
| 1651 | core\spawn\spawn_generator.py | other_non_ascii | 167 | * A :class:`WorldModel` (with ``.tiles``) → walked normally. | INFO | Other_NonASCII |
| 1652 | core\spawn\spawn_generator.py | other_non_ascii | 169 | carry hunts / bosses / spawns) → walked via the designer | INFO | Other_NonASCII |
| 1653 | core\spawn\__init__.py | other_non_ascii | 2 | MVP V0.1 — Spawn Generator | INFO | Other_NonASCII |
| 1654 | core\themes\theme_resolver.py | other_non_ascii | 2 | MVP V0.1 — Theme Resolver | INFO | Other_NonASCII |
| 1655 | core\themes\__init__.py | other_non_ascii | 2 | MVP V0.1 — Theme Resolver | INFO | Other_NonASCII |
| 1656 | core\world\world_model.py | other_non_ascii | 17 | Unified World Model — the single source of truth for the entire map. | INFO | Other_NonASCII |
| 1657 | core\world\world_model.py | other_non_ascii | 23 | - tiles: Dict[str, Tile] — all tiles keyed by "x:y:z". | INFO | Other_NonASCII |
| 1658 | core\world\world_model.py | other_non_ascii | 24 | - structures: List[Structure] — all placed blueprints. | INFO | Other_NonASCII |
| 1659 | core\world\world_model.py | other_non_ascii | 25 | - regions: List[Region] — named zones. | INFO | Other_NonASCII |
| 1660 | core\world\world_model.py | other_non_ascii | 26 | - chunks: Dict[str, Chunk] — spatial partitioning for large maps. | INFO | Other_NonASCII |
| 1661 | core\world\__init__.py | other_non_ascii | 2 | Unified World Model — the single source of truth for the entire map. | INFO | Other_NonASCII |
| 1662 | core\world_brain\decision_engine.py | comment | 12 | WHAT = "what"  # qué construir | WARNING | Latin_Extended |
| 1663 | core\world_brain\decision_engine.py | comment | 13 | WHERE = "where"  # dónde construir | WARNING | Latin_Extended |
| 1664 | core\world_brain\decision_engine.py | comment | 14 | WHEN = "when"  # cuándo construir | WARNING | Latin_Extended |
| 1665 | core\world_brain\decision_engine.py | comment | 270 | # Goal → Decision conversion | WARNING | Other_NonASCII |
| 1666 | core\world_brain\goal_engine.py | other_non_ascii | 27 | name="Crear expansión endgame", | INFO | Latin_Extended |
| 1667 | core\world_brain\goal_engine.py | other_non_ascii | 61 | A goal translates abstract intent (e.g., "Crear expansión endgame") | INFO | Latin_Extended |
| 1668 | core\world_brain\goal_engine.py | other_non_ascii | 80 | "description": "Añadir contenido nuevo: hunts, bosses, quests", | INFO | Latin_Extended |
| 1669 | core\world_brain\goal_engine.py | other_non_ascii | 90 | "description": "Balancear la dificultad y distribución de contenido", | INFO | Latin_Extended |
| 1670 | core\world_brain\goal_engine.py | other_non_ascii | 100 | "description": "Añadir zonas de quest con recompensas y progresión", | INFO | Latin_Extended |
| 1671 | core\world_brain\goal_engine.py | other_non_ascii | 105 | "description": "Actualizar items, monstruos y formato a versión moderna", | INFO | Latin_Extended |
| 1672 | core\world_brain\goal_engine.py | other_non_ascii | 110 | "description": "Mejorar la estética natural del mapa", | INFO | Latin_Extended |
| 1673 | core\world_brain\goal_engine.py | other_non_ascii | 167 | "Crear expansión endgame con ciudades y hunts" | INFO | Latin_Extended |
| 1674 | core\world_brain\goal_engine.py | other_non_ascii | 168 | → [EXPAND_WORLD, ADD_ENDGAME, ADD_CONTENT] | INFO | Other_NonASCII |
| 1675 | core\world_brain\goal_engine.py | other_non_ascii | 297 | "Crear expansión endgame" | INFO | Latin_Extended |
| 1676 | core\world_brain\goal_engine.py | other_non_ascii | 298 | → [Create city, Create hunt zone, Create boss room, Create quest zone] | INFO | Other_NonASCII |
| 1677 | core\world_brain\reasoning_engine.py | other_non_ascii | 51 | "¿Por qué se creó esta dungeon?" | INFO | Other_NonASCII, Latin_Extended |
| 1678 | core\world_brain\reasoning_engine.py | other_non_ascii | 52 | "¿Por qué existe este boss?" | INFO | Other_NonASCII, Latin_Extended |
| 1679 | core\world_brain\reasoning_engine.py | other_non_ascii | 53 | "¿Por qué este templo tiene 4 pisos?" | INFO | Other_NonASCII, Latin_Extended |
| 1680 | core\world_brain\reasoning_engine.py | other_non_ascii | 54 | "¿Por qué hay una ciudad aquí?" | INFO | Other_NonASCII, Latin_Extended |
| 1681 | core\world_brain\reasoning_engine.py | other_non_ascii | 55 | "¿Por qué estos monstruos están juntos?" | INFO | Other_NonASCII, Latin_Extended |
| 1682 | core\world_brain\reasoning_engine.py | other_non_ascii | 75 | elif "decoración" in lower or "decoration" in lower: | INFO | Latin_Extended |
| 1683 | core\world_brain\reasoning_engine.py | other_non_ascii | 77 | elif "tamaño" in lower or "size" in lower or "grande" in lower: | INFO | Latin_Extended |
| 1684 | core\world_brain\reasoning_engine.py | other_non_ascii | 81 | elif "zona vacía" in lower: | INFO | Latin_Extended |
| 1685 | core\world_brain\reasoning_engine.py | other_non_ascii | 87 | summary=f"La decisión sobre '{topic}' se basa en objetivos de diseño global, " | INFO | Latin_Extended |
| 1686 | core\world_brain\reasoning_engine.py | other_non_ascii | 90 | "Objetivos de diseño del World Brain", | INFO | Latin_Extended |
| 1687 | core\world_brain\reasoning_engine.py | other_non_ascii | 94 | alternatives=["No crear este elemento", "Crearlo en otra ubicación"], | INFO | Latin_Extended |
| 1688 | core\world_brain\reasoning_engine.py | other_non_ascii | 140 | summary="Esta dungeon fue creada para proporcionar contenido de progresión " | INFO | Latin_Extended |
| 1689 | core\world_brain\reasoning_engine.py | other_non_ascii | 141 | "con una curva de dificultad ascendente. Su diseño prioriza la " | INFO | Latin_Extended |
| 1690 | core\world_brain\reasoning_engine.py | other_non_ascii | 142 | "experiencia de exploración, combate táctico y recompensa al final.", | INFO | Latin_Extended |
| 1691 | core\world_brain\reasoning_engine.py | other_non_ascii | 146 | "Restricciones: tamaño 30x30 a 200x200, dificultad 6-8", | INFO | Latin_Extended |
| 1692 | core\world_brain\reasoning_engine.py | other_non_ascii | 147 | "Patrón aprendido: dungeons con 3 pisos tienen mejor retención", | INFO | Latin_Extended |
| 1693 | core\world_brain\reasoning_engine.py | other_non_ascii | 148 | "Estilo visual determinó usar theme roshamuul/issavi", | INFO | Latin_Extended |
| 1694 | core\world_brain\reasoning_engine.py | other_non_ascii | 152 | "Área abierta tipo hunt (rechazada: no proporciona progresión)", | INFO | Latin_Extended |
| 1695 | core\world_brain\reasoning_engine.py | other_non_ascii | 161 | summary="Este boss fue diseñado como punto culminante de la zona. " | INFO | Latin_Extended |
| 1696 | core\world_brain\reasoning_engine.py | other_non_ascii | 162 | "Su ubicación al final del dungeon, con minions y mecánicas " | INFO | Latin_Extended |
| 1697 | core\world_brain\reasoning_engine.py | other_non_ascii | 163 | "específicas, proporciona un desafío adecuado para grupos " | INFO | Latin_Extended |
| 1698 | core\world_brain\reasoning_engine.py | other_non_ascii | 167 | "Restricción boss_room: dificultad 6-10, tamaño 8-30", | INFO | Latin_Extended |
| 1699 | core\world_brain\reasoning_engine.py | other_non_ascii | 168 | "Boss colocado en el punto más alejado de la entrada", | INFO | Latin_Extended |
| 1700 | core\world_brain\reasoning_engine.py | other_non_ascii | 173 | "Boss al inicio del dungeon (rechazado: muy fácil)", | INFO | Latin_Extended |
| 1701 | core\world_brain\reasoning_engine.py | other_non_ascii | 174 | "Múltiples bosses pequeños (rechazado: diluye el foco)", | INFO | Latin_Extended |
| 1702 | core\world_brain\reasoning_engine.py | other_non_ascii | 183 | summary="El templo se colocó en el centro de la ciudad porque es el " | INFO | Latin_Extended |
| 1703 | core\world_brain\reasoning_engine.py | other_non_ascii | 184 | "punto de reaparición principal. Su tamaño y decoración " | INFO | Latin_Extended |
| 1704 | core\world_brain\reasoning_engine.py | other_non_ascii | 190 | "Estilo issavi determinó usar columnas, alfombras y fuego sagrado", | INFO | Latin_Extended |
| 1705 | core\world_brain\reasoning_engine.py | other_non_ascii | 194 | "Templo pequeño (rechazado: no cumple función ceremonial)", | INFO | Latin_Extended |
| 1706 | core\world_brain\reasoning_engine.py | other_non_ascii | 202 | summary="La ciudad fue diseñada como centro neurálgico del mundo. " | INFO | Latin_Extended |
| 1707 | core\world_brain\reasoning_engine.py | other_non_ascii | 203 | "Sus distritos (templo, depot, market, residencial) están " | INFO | Latin_Extended |
| 1708 | core\world_brain\reasoning_engine.py | other_non_ascii | 204 | "conectados por calles principales que facilitan la navegación.", | INFO | Latin_Extended |
| 1709 | core\world_brain\reasoning_engine.py | other_non_ascii | 207 | "Restricción city: PZ zone, tamaño mínimo 20x20", | INFO | Latin_Extended |
| 1710 | core\world_brain\reasoning_engine.py | other_non_ascii | 208 | "Calles principales de 4 tiles de ancho para tráfico fluido", | INFO | Latin_Extended |
| 1711 | core\world_brain\reasoning_engine.py | other_non_ascii | 210 | "Muralla con torres para dar sensación de seguridad", | INFO | Latin_Extended |
| 1712 | core\world_brain\reasoning_engine.py | other_non_ascii | 215 | "Ciudad subterránea (rechazada: difícil de navegar)", | INFO | Latin_Extended |
| 1713 | core\world_brain\reasoning_engine.py | other_non_ascii | 223 | summary="Estos monstruos fueron seleccionados para la zona basándose " | INFO | Latin_Extended |
| 1714 | core\world_brain\reasoning_engine.py | other_non_ascii | 224 | "en compatibilidad temática, nivel de dificultad y sinergia " | INFO | Latin_Extended |
| 1715 | core\world_brain\reasoning_engine.py | other_non_ascii | 225 | "de gameplay. La combinación crea encuentros tácticos interesantes.", | INFO | Latin_Extended |
| 1716 | core\world_brain\reasoning_engine.py | other_non_ascii | 227 | "Monstruos del mismo tema visual (issavi ↔ Frazzlemaw/Sphinx)", | INFO | Other_NonASCII |
| 1717 | core\world_brain\reasoning_engine.py | other_non_ascii | 231 | "Densidad de spawn calculada para flujo de caza óptimo", | INFO | Latin_Extended |
| 1718 | core\world_brain\reasoning_engine.py | other_non_ascii | 234 | "Monstruos aleatorios (rechazado: rompe inmersión)", | INFO | Latin_Extended |
| 1719 | core\world_brain\reasoning_engine.py | other_non_ascii | 235 | "Un solo tipo de monstruo (rechazado: monótono)", | INFO | Latin_Extended |
| 1720 | core\world_brain\reasoning_engine.py | other_non_ascii | 236 | "Monstruos de nivel muy bajo (rechazado: sin desafío)", | INFO | Latin_Extended |
| 1721 | core\world_brain\reasoning_engine.py | other_non_ascii | 244 | summary="La decoración fue seleccionada del Asset Recommender para " | INFO | Latin_Extended |
| 1722 | core\world_brain\reasoning_engine.py | other_non_ascii | 246 | "y fountain se colocaron estratégicamente para mejorar la estética.", | INFO | Latin_Extended |
| 1723 | core\world_brain\reasoning_engine.py | other_non_ascii | 248 | "AssetClassifier determinó items compatibles con el tema", | INFO | Latin_Extended |
| 1724 | core\world_brain\reasoning_engine.py | other_non_ascii | 249 | "AssetSimilarity encontró items visualmente coherentes", | INFO | Latin_Extended |
| 1725 | core\world_brain\reasoning_engine.py | other_non_ascii | 250 | "AssetRecommender priorizó items con alta afinidad temática", | INFO | Latin_Extended |
| 1726 | core\world_brain\reasoning_engine.py | other_non_ascii | 251 | "Densidad de decoración mínima: 15 items por cada 100 tiles", | INFO | Latin_Extended |
| 1727 | core\world_brain\reasoning_engine.py | other_non_ascii | 254 | "Sin decoración (rechazado: mapa plano y aburrido)", | INFO | Latin_Extended |
| 1728 | core\world_brain\reasoning_engine.py | other_non_ascii | 255 | "Decoración aleatoria (rechazado: falta coherencia visual)", | INFO | Latin_Extended |
| 1729 | core\world_brain\reasoning_engine.py | other_non_ascii | 263 | summary="El tamaño fue determinado por las restricciones del perfil " | INFO | Latin_Extended |
| 1730 | core\world_brain\reasoning_engine.py | other_non_ascii | 264 | "de diseño y el análisis de calidad. El objetivo es balancear " | INFO | Latin_Extended |
| 1731 | core\world_brain\reasoning_engine.py | other_non_ascii | 265 | "suficiente espacio para gameplay sin crear zonas vacías.", | INFO | Latin_Extended |
| 1732 | core\world_brain\reasoning_engine.py | other_non_ascii | 267 | f"Restricción del perfil activo para dimensiones", | INFO | Latin_Extended |
| 1733 | core\world_brain\reasoning_engine.py | other_non_ascii | 268 | "Quality Detector penaliza zonas muy pequeñas o muy grandes", | INFO | Latin_Extended |
| 1734 | core\world_brain\reasoning_engine.py | other_non_ascii | 272 | "Tamaño más pequeño (rechazado: densidad muy alta)", | INFO | Latin_Extended |
| 1735 | core\world_brain\reasoning_engine.py | other_non_ascii | 273 | "Tamaño más grande (rechazado: zonas vacías)", | INFO | Latin_Extended |
| 1736 | core\world_brain\reasoning_engine.py | other_non_ascii | 281 | summary="La entrada se colocó siguiendo principios de diseño " | INFO | Latin_Extended |
| 1737 | core\world_brain\reasoning_engine.py | other_non_ascii | 282 | "estándar: ciudades entran desde el sur/borde, dungeons " | INFO | Latin_Extended |
| 1738 | core\world_brain\reasoning_engine.py | other_non_ascii | 285 | "Regla de diseño: entrada en borde sur para ciudades", | INFO | Latin_Extended |
| 1739 | core\world_brain\reasoning_engine.py | other_non_ascii | 286 | "Conexión con caminos existentes del mapa global", | INFO | Latin_Extended |
| 1740 | core\world_brain\reasoning_engine.py | other_non_ascii | 291 | "Múltiples entradas (rechazado: difícil de defender)", | INFO | Latin_Extended |
| 1741 | core\world_brain\reasoning_engine.py | other_non_ascii | 299 | summary="Las zonas vacías fueron detectadas por el Quality Detector " | INFO | Latin_Extended |
| 1742 | core\world_brain\reasoning_engine.py | other_non_ascii | 300 | "y priorizadas para mejora. El Improvement Engine las rellenará " | INFO | Latin_Extended |
| 1743 | core\world_brain\reasoning_engine.py | other_non_ascii | 301 | "con contenido procedural en la siguiente iteración.", | INFO | Latin_Extended |
| 1744 | core\world_brain\reasoning_engine.py | other_non_ascii | 303 | "Quality Detector score bajo activó FILL_EMPTY_ZONES", | INFO | Latin_Extended |
| 1745 | core\world_brain\reasoning_engine.py | other_non_ascii | 305 | "Improvement programado para añadir contenido básico", | INFO | Latin_Extended |
| 1746 | core\world_brain\reasoning_engine.py | other_non_ascii | 308 | "Dejar vacío (rechazado: baja calidad del mapa)", | INFO | Latin_Extended |
| 1747 | core\world_brain\reasoning_engine.py | other_non_ascii | 324 | "por qué ", | INFO | Latin_Extended |
| 1748 | core\world_brain\reasoning_engine.py | other_non_ascii | 340 | .replace("¿", "") | INFO | Other_NonASCII |
| 1749 | core\world_brain\world_brain.py | other_non_ascii | 78 | Prompt → GoalEngine → ConstraintEngine → DecisionEngine | INFO | Other_NonASCII |
| 1750 | core\world_brain\world_brain.py | other_non_ascii | 79 | → ReasoningEngine → Execution | INFO | Other_NonASCII |
| 1751 | core\world_brain\world_brain.py | other_non_ascii | 100 | Given a design goal (e.g., "Crear expansión endgame"), | INFO | Latin_Extended |
| 1752 | data\blueprints\cities\issavi_city.json | export_value | 7 | "description": "Ciudad amurallada estilo oriental con templo central, mercado y depósito", | WARNING | Latin_Extended |
| 1753 | data\blueprints\depots\issavi_depot.json | export_value | 7 | "description": "Depósito estilo Issavi con lockers, balcón superior y acceso central", | WARNING | Latin_Extended |
| 1754 | data\blueprints\hunts\issavi_hunting_grounds.json | export_value | 7 | "description": "Zona de caza Issavi con terreno mixto, múltiples spawns y distribución balanceada", | WARNING | Latin_Extended |
| 1755 | data\blueprints\temples\issavi_temple_large.json | export_value | 7 | "description": "Templo Issavi grande con altar central, columnas y decoración sagrada", | WARNING | Latin_Extended |
| 1756 | docs\INSTALL.md | documentation_text | 1 | # Installation Guide — RME Map AI Agent v2.0 | INFO | Other_NonASCII |
| 1757 | docs\INSTALL.md | documentation_text | 127 | ├── output/          # Generated maps, scripts, previews | INFO | Other_NonASCII |
| 1758 | docs\INSTALL.md | documentation_text | 128 | ├── cache/           # Item/monster/NPC caches | INFO | Other_NonASCII |
| 1759 | docs\INSTALL.md | documentation_text | 129 | ├── config/          # Environment configs (dev, prod) | INFO | Other_NonASCII |
| 1760 | docs\INSTALL.md | documentation_text | 130 | ├── data/            # Blueprints, embeddings | INFO | Other_NonASCII |
| 1761 | docs\INSTALL.md | documentation_text | 131 | ├── logs/            # Application logs | INFO | Other_NonASCII |
| 1762 | docs\INSTALL.md | documentation_text | 132 | ├── exports/         # Exported artifacts | INFO | Other_NonASCII |
| 1763 | docs\INSTALL.md | documentation_text | 133 | └── release/         # Release packages | INFO | Other_NonASCII |
| 1764 | docs\README.md | documentation_text | 1 | # Documentación de RME API y Ejemplos | INFO | Latin_Extended |
| 1765 | docs\README.md | documentation_text | 5 | - `rme_api_reference.md` — referencia de las funciones válidas. | INFO | Other_NonASCII, Latin_Extended |
| 1766 | docs\README.md | documentation_text | 6 | - `README.md` — guía mínima de contenido del directorio. | INFO | Other_NonASCII, Latin_Extended |
| 1767 | docs\rme_api_reference.md | documentation_text | 13 | - Cualquier modificación de tiles o entidades debe hacerse dentro de este bloque. | INFO | Latin_Extended |
| 1768 | docs\rme_api_reference.md | documentation_text | 16 | - Cambia la cámara a una posición específica del mapa. | INFO | Latin_Extended |
| 1769 | docs\rme_api_reference.md | documentation_text | 26 | - Establece el terreno del tile a un ID de item válido. | INFO | Latin_Extended |
| 1770 | docs\rme_api_reference.md | documentation_text | 29 | - Añade un objeto encima del tile. | INFO | Latin_Extended |
| 1771 | docs\rme_api_reference.md | documentation_text | 32 | - Crea un borde alrededor del tile para definir áreas o contornos. | INFO | Latin_Extended |
| 1772 | docs\rme_api_reference.md | documentation_text | 38 | - Coloca un spawn de criatura en el tile con dirección y tiempo de reaparición. | INFO | Latin_Extended |
| 1773 | docs\rme_api_reference.md | documentation_text | 43 | - Genera una dispersión aleatoria en coordenadas. | INFO | Latin_Extended |
| 1774 | docs\rme_api_reference.md | documentation_text | 49 | - Genera ruido simplex para crear terreno procedural: cuevas, formas de terreno y variación natural. | INFO | Latin_Extended |
| 1775 | docs\rme_api_reference.md | documentation_text | 54 | - Crea interfaces de interacción en RME. | INFO | Latin_Extended |
| 1776 | docs\rme_api_reference.md | documentation_text | 56 | ### Métodos frecuentes de Dialog | INFO | Latin_Extended |
| 1777 | docs\rme_api_reference.md | documentation_text | 59 | - Añade una etiqueta de texto. | INFO | Latin_Extended |
| 1778 | docs\rme_api_reference.md | documentation_text | 62 | - Añade un campo de texto para entrada de usuario. | INFO | Latin_Extended |
| 1779 | docs\rme_api_reference.md | documentation_text | 65 | - Añade una casilla de verificación. | INFO | Latin_Extended |
| 1780 | docs\rme_api_reference.md | documentation_text | 68 | - Añade un campo numérico. | INFO | Latin_Extended |
| 1781 | docs\rme_api_reference.md | documentation_text | 71 | - Añade un botón con callback. | INFO | Latin_Extended |
| 1782 | docs\rme_api_reference.md | documentation_text | 74 | - Muestra la ventana de diálogo. | INFO | Latin_Extended |
| 1783 | docs\rme_api_reference.md | documentation_text | 91 | ### Añadir un objeto decorativo | INFO | Latin_Extended |
| 1784 | examples\analyze_ciudades.py | print_string | 16 | print("Ciudades.otbm no encontrado. Generando análisis de ejemplo.") | WARNING | Latin_Extended |
| 1785 | examples\enterprise_demo.py | other_non_ascii | 7 | prompt = "Genera una expansión estilo Issavi + Roshamuul nivel 300-800." | INFO | Latin_Extended |
| 1786 | examples\expansion_demo.py | other_non_ascii | 5 | prompt = "Genera una expansión endgame inspirada en Issavi y Roshamuul." | INFO | Latin_Extended |
| 1787 | examples\hito13_blueprint_extractor_demo.py | other_non_ascii | 2 | HITO 13 — Demo funcional del Blueprint Extractor. | INFO | Other_NonASCII |
| 1788 | examples\hito13_blueprint_extractor_demo.py | other_non_ascii | 5 | OTBM → WorldModel → Theme → Patterns → Structures → Blueprint → JSON | INFO | Other_NonASCII |
| 1789 | examples\hito13_blueprint_extractor_demo.py | comment | 29 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1790 | examples\hito13_blueprint_extractor_demo.py | comment | 31 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1791 | examples\hito13_blueprint_extractor_demo.py | comment | 237 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1792 | examples\hito13_blueprint_extractor_demo.py | comment | 239 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1793 | examples\hito13_blueprint_extractor_demo.py | print_string | 253 | print(f"\nIssavi Tiles → {result['primary_theme']} (confidence: {result['confidence']})") | WARNING | Other_NonASCII |
| 1794 | examples\hito13_blueprint_extractor_demo.py | print_string | 260 | print(f"\nDungeon Tiles → {result['primary_theme']} (confidence: {result['confidence']})") | WARNING | Other_NonASCII |
| 1795 | examples\hito13_blueprint_extractor_demo.py | print_string | 272 | print(f"\nHunt Area → {result['primary_theme']} (is_hunt: {result['is_hunt_area']})") | WARNING | Other_NonASCII |
| 1796 | examples\hito13_blueprint_extractor_demo.py | print_string | 278 | print(f"\nCity Tiles → {result['primary_theme']} (is_urban: {result['is_urban']})") | WARNING | Other_NonASCII |
| 1797 | examples\hito13_blueprint_extractor_demo.py | print_string | 281 | print(f"\nQuick classify 'issavi_temple' → {classifier.quick_classify('issavi_temple')}") | WARNING | Other_NonASCII |
| 1798 | examples\hito13_blueprint_extractor_demo.py | print_string | 282 | print(f"Quick classify 'roshamuul_dungeon' → {classifier.quick_classify('roshamuul_dungeon')}") | WARNING | Other_NonASCII |
| 1799 | examples\hito13_blueprint_extractor_demo.py | print_string | 421 | print("DEMO 4: Blueprint Extractor — Issavi Temple") | WARNING | Other_NonASCII |
| 1800 | examples\hito13_blueprint_extractor_demo.py | other_non_ascii | 495 | status = "✓" if result.success else "✗" | INFO | Other_NonASCII |
| 1801 | examples\hito13_blueprint_extractor_demo.py | print_string | 499 | print(f"  {status} {name:25s} → {theme:12s} ({confidence:.2f}) \| {bp_name}") | WARNING | Other_NonASCII |
| 1802 | examples\hito13_blueprint_extractor_demo.py | comment | 576 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1803 | examples\hito13_blueprint_extractor_demo.py | comment | 578 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 1804 | examples\learn_architecture.py | print_string | 42 | print(f"Guardado aprendizaje arquitectónico en {output_file}") | WARNING | Latin_Extended |
| 1805 | examples\plan_expansion.py | other_non_ascii | 6 | prompt = "Genera una expansión nivel 300-500 inspirada en Issavi y Roshamuul." | INFO | Latin_Extended |
| 1806 | examples\plan_expansion.py | print_string | 27 | print("No se puede generar el mundo: plan inválido.") | WARNING | Latin_Extended |
| 1807 | examples\playtest_demo.py | docstring | 1 | """Playtest Engine Demo — generates a real playtest report.""" | WARNING | Other_NonASCII |
| 1808 | examples\README.md | documentation_text | 7 | - `island_generator.lua` — Generador de isla con borde y decoración. | INFO | Other_NonASCII, Latin_Extended |
| 1809 | examples\README.md | documentation_text | 8 | - `cave_generator.lua` — Generador de cueva procedural usando `noise.simplex()`. | INFO | Other_NonASCII |
| 1810 | examples\README.md | documentation_text | 9 | - `temple_generator.lua` — Generador de templo con cámara y sala central. | INFO | Other_NonASCII, Latin_Extended |
| 1811 | examples\README.md | documentation_text | 10 | - `city_generator.lua` — Generador de ciudad con carreteras y muros. | INFO | Other_NonASCII |
| 1812 | examples\README.md | documentation_text | 11 | - `spawn_generator.lua` — Ejemplo de spawns y puntos de aparición. | INFO | Other_NonASCII, Latin_Extended |
| 1813 | examples\README.md | documentation_text | 12 | - `issavi_roshamuul_hybrid.lua` — Generador híbrido de Issavi + Roshamuul. | INFO | Other_NonASCII, Latin_Extended |
| 1814 | examples\README.md | documentation_text | 16 | 1. Abre RME y carga un mapa vacío o existente. | INFO | Latin_Extended |
| 1815 | generators\dungeon_generator.py | other_non_ascii | 14 | "  -- Crear habitaciones subterráneas y corredores\n" | INFO | Latin_Extended |
| 1816 | installer\run_tests.py | other_non_ascii | 2 | RME Map AI Agent v2.0 — Test Runner | INFO | Other_NonASCII |
| 1817 | installer\setup.py | other_non_ascii | 2 | RME Map AI Agent v2.0 — Production Installer | INFO | Other_NonASCII |
| 1818 | installer\setup.py | other_non_ascii | 94 | results.append((True, pkg_name, f"{ver} — {desc}")) | INFO | Other_NonASCII |
| 1819 | installer\setup.py | other_non_ascii | 96 | results.append((False, pkg_name, f"NOT INSTALLED — {desc}")) | INFO | Other_NonASCII |
| 1820 | installer\setup.py | other_non_ascii | 142 | return True, f"Running — {len(models)} models: {', '.join(names)}" | INFO | Other_NonASCII |
| 1821 | installer\setup.py | other_non_ascii | 182 | print_header("RME Map AI Agent v2.0 — Installer") | INFO | Other_NonASCII |
| 1822 | output\knowledge_report.md | documentation_text | 88 | - **Darashia_0** (`60b34a92b3950b1b`) — biome=`orcsoberfest`, levels=100-500 | INFO | Other_NonASCII |
| 1823 | output\knowledge_report.md | documentation_text | 89 | - **Edron_1** (`748e9b6f483d8b28`) — biome=`yalahar`, levels=100-500 | INFO | Other_NonASCII |
| 1824 | output\knowledge_report.md | documentation_text | 90 | - **Vippre_2** (`98cbd2e6613df08f`) — biome=`orcsoberfest`, levels=100-500 | INFO | Other_NonASCII |
| 1825 | output\knowledge_report.md | documentation_text | 91 | - **Feyrist_2** (`d9091a8d54764abf`) — biome=`orcsoberfest`, levels=100-500 | INFO | Other_NonASCII |
| 1826 | output\knowledge_report.md | documentation_text | 92 | - **Vippre_4** (`7d7425f00cef6a6d`) — biome=`venore`, levels=100-500 | INFO | Other_NonASCII |
| 1827 | output\knowledge_report.md | documentation_text | 96 | - **lair_orcsoberfest_hunt_0** (`7f8afed98b2aa9a0`) — biome=`orcsoberfest`, levels=157-320 | INFO | Other_NonASCII |
| 1828 | output\knowledge_report.md | documentation_text | 97 | - **circular_orcsoberfest_hunt_0** (`fda42445f4142c02`) — biome=`orcsoberfest`, levels=174-507 | INFO | Other_NonASCII |
| 1829 | output\knowledge_report.md | documentation_text | 98 | - **lair_yalahar_hunt_1** (`99941ec9000fbc5d`) — biome=`yalahar`, levels=245-332 | INFO | Other_NonASCII |
| 1830 | output\knowledge_report.md | documentation_text | 99 | - **lower_yalahar_hunt_1** (`cc09d463a4242e11`) — biome=`yalahar`, levels=244-530 | INFO | Other_NonASCII |
| 1831 | output\knowledge_report.md | documentation_text | 100 | - **outer_orcsoberfest_hunt_2** (`8d59cd986fc0ffc4`) — biome=`orcsoberfest`, levels=71-484 | INFO | Other_NonASCII |
| 1832 | output\knowledge_report.md | documentation_text | 104 | - **throne_arena_orcsoberfest_0** (`d106afc8b4017d9e`) — biome=`orcsoberfest`, levels=300-600 | INFO | Other_NonASCII |
| 1833 | output\knowledge_report.md | documentation_text | 105 | - **lair_orcsoberfest_hunt_0** (`2d3ff2c043824c29`) — biome=`orcsoberfest`, levels=157-320 | INFO | Other_NonASCII |
| 1834 | output\knowledge_report.md | documentation_text | 106 | - **pit_arena_yalahar_1** (`c7d25fddfec5b716`) — biome=`yalahar`, levels=300-600 | INFO | Other_NonASCII |
| 1835 | output\knowledge_report.md | documentation_text | 107 | - **lair_yalahar_hunt_1** (`2b46b5e67afa4155`) — biome=`yalahar`, levels=245-332 | INFO | Other_NonASCII |
| 1836 | output\knowledge_report.md | documentation_text | 108 | - **throne_arena_orcsoberfest_2** (`897a4f53a2847fc1`) — biome=`orcsoberfest`, levels=300-600 | INFO | Other_NonASCII |
| 1837 | output\knowledge_report.md | documentation_text | 112 | - **quest_orcsoberfest_0** (`97b1cb8b3421f93d`) — biome=`generic`, levels=1-9999 | INFO | Other_NonASCII |
| 1838 | output\knowledge_report.md | documentation_text | 113 | - **quest_yalahar_1** (`9bd1e728159c84a5`) — biome=`generic`, levels=1-9999 | INFO | Other_NonASCII |
| 1839 | output\knowledge_report.md | documentation_text | 114 | - **quest_orcsoberfest_2** (`571451c3acf41408`) — biome=`generic`, levels=1-9999 | INFO | Other_NonASCII |
| 1840 | output\knowledge_report.md | documentation_text | 115 | - **quest_venore_3** (`5d9c1a74d809b64a`) — biome=`generic`, levels=1-9999 | INFO | Other_NonASCII |
| 1841 | output\knowledge_report.md | documentation_text | 116 | - **quest_venore_4** (`8ec510b094056606`) — biome=`generic`, levels=1-9999 | INFO | Other_NonASCII |
| 1842 | output\knowledge_report.md | documentation_text | 120 | - **lair_orcsoberfest_hunt_0** (`15f5582cf3bebf63`) — biome=`orcsoberfest`, levels=157-320 | INFO | Other_NonASCII |
| 1843 | output\knowledge_report.md | documentation_text | 121 | - **lair_yalahar_hunt_1** (`0a9085f08a20cf67`) — biome=`yalahar`, levels=245-332 | INFO | Other_NonASCII |
| 1844 | output\knowledge_report.md | documentation_text | 122 | - **lair_hellgate_hunt_6** (`f8c70bf0c19f3232`) — biome=`hellgate`, levels=70-548 | INFO | Other_NonASCII |
| 1845 | output\knowledge_report.md | documentation_text | 123 | - **lair_darashia_hunt_11** (`d6235520ba0ec626`) — biome=`darashia`, levels=249-538 | INFO | Other_NonASCII |
| 1846 | output\knowledge_report.md | documentation_text | 124 | - **lair_ankrahmun_hunt_17** (`200d909a4d6ea4ac`) — biome=`ankrahmun`, levels=127-487 | INFO | Other_NonASCII |
| 1847 | output\knowledge_report.md | documentation_text | 128 | - **Orcsoberfest** (`8dd3caaf8ba3eddb`) — biome=`Orcsoberfest`, levels=157-320 | INFO | Other_NonASCII |
| 1848 | output\knowledge_report.md | documentation_text | 129 | - **Yalahar** (`988960ea3a48c15f`) — biome=`Yalahar`, levels=245-332 | INFO | Other_NonASCII |
| 1849 | output\knowledge_report.md | documentation_text | 130 | - **Venore** (`9a0fff82e3674bb7`) — biome=`Venore`, levels=83-489 | INFO | Other_NonASCII |
| 1850 | output\knowledge_report.md | documentation_text | 131 | - **Asura** (`140ecdb8a9007100`) — biome=`Asura`, levels=141-571 | INFO | Other_NonASCII |
| 1851 | output\knowledge_report.md | documentation_text | 132 | - **Hellgate** (`10b3ed5d99a060d6`) — biome=`Hellgate`, levels=70-548 | INFO | Other_NonASCII |
| 1852 | output\critic_test\critic_report.json | export_value | 256 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1853 | output\critic_test\critic_report.json | export_value | 265 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1854 | output\critic_test\critic_report.json | export_value | 274 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1855 | output\critic_test\critic_report.md | documentation_text | 1 | # Critic Report — test_issavi | INFO | Other_NonASCII |
| 1856 | output\critic_test\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T14:54:30.014502  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1857 | output\critic_test\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (19,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1858 | output\critic_test\critic_report.md | documentation_text | 37 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1859 | output\critic_test\critic_report.md | documentation_text | 38 | \| warning \| bottleneck \| pathfinding \| (0,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1860 | output\critic_test\critic_report.md | documentation_text | 43 | _Priority: medium  •  Category: spawn_ | INFO | Other_NonASCII |
| 1861 | output\critic_test\critic_report.md | documentation_text | 48 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1862 | output\critic_test\critic_report.md | documentation_text | 53 | _Priority: high  •  Category: boss_ | INFO | Other_NonASCII |
| 1863 | output\critic_test\critic_report.md | documentation_text | 59 | _Priority: high  •  Category: city_ | INFO | Other_NonASCII |
| 1864 | output\critic_test\critic_report.md | documentation_text | 65 | _Priority: high  •  Category: city_ | INFO | Other_NonASCII |
| 1865 | output\critic_test\critic_report.md | documentation_text | 71 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1866 | output\critic_test\critic_report.md | documentation_text | 76 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1867 | output\hito26_1_benchmark\benchmark_report.json | export_value | 3 | "prompt": "Crear expansión Issavi + Roshamuul\npara niveles 300-500\n\n3 hunts\n2 bosses\n1 raid\nquest principal", | WARNING | Latin_Extended |
| 1868 | output_benchmark\ancient_temple_300\critic_report.json | export_value | 189 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1869 | output_benchmark\ancient_temple_300\critic_report.json | export_value | 198 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1870 | output_benchmark\ancient_temple_300\critic_report.json | export_value | 207 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1871 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 1 | # Critic Report — ancient_temple_300 | INFO | Other_NonASCII |
| 1872 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.180597  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1873 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 30 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1874 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 31 | \| warning \| bottleneck \| pathfinding \| (34,34,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1875 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,34,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1876 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 37 | _Priority: medium  •  Category: spawn_ | INFO | Other_NonASCII |
| 1877 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 42 | _Priority: low  •  Category: hunt_ | INFO | Other_NonASCII |
| 1878 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 47 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1879 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 52 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1880 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1881 | output_benchmark\ancient_temple_300\critic_report.md | documentation_text | 62 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1882 | output_benchmark\darashia_150\critic_report.json | export_value | 223 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1883 | output_benchmark\darashia_150\critic_report.json | export_value | 232 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1884 | output_benchmark\darashia_150\critic_report.json | export_value | 241 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1885 | output_benchmark\darashia_150\critic_report.md | documentation_text | 1 | # Critic Report — darashia_150 | INFO | Other_NonASCII |
| 1886 | output_benchmark\darashia_150\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.010625  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1887 | output_benchmark\darashia_150\critic_report.md | documentation_text | 33 | \| warning \| bottleneck \| pathfinding \| (19,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1888 | output_benchmark\darashia_150\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1889 | output_benchmark\darashia_150\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1890 | output_benchmark\darashia_150\critic_report.md | documentation_text | 40 | _Priority: medium  •  Category: spawn_ | INFO | Other_NonASCII |
| 1891 | output_benchmark\darashia_150\critic_report.md | documentation_text | 45 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1892 | output_benchmark\darashia_150\critic_report.md | documentation_text | 50 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1893 | output_benchmark\darashia_150\critic_report.md | documentation_text | 55 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1894 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 1 | # Critic Report — deep_orc_cave_100 | INFO | Other_NonASCII |
| 1895 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.835072  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1896 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 38 | _Priority: medium  •  Category: visual_ | INFO | Other_NonASCII |
| 1897 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 43 | _Priority: medium  •  Category: density_ | INFO | Other_NonASCII |
| 1898 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 48 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1899 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 53 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1900 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 58 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1901 | output_benchmark\deep_orc_cave_100\critic_report.md | documentation_text | 63 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1902 | output_benchmark\djinn_arena_300\critic_report.json | export_value | 199 | "message": "Only 1 unique decoration types — map looks repetitive", | WARNING | Other_NonASCII |
| 1903 | output_benchmark\djinn_arena_300\critic_report.json | export_value | 229 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1904 | output_benchmark\djinn_arena_300\critic_report.json | export_value | 238 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1905 | output_benchmark\djinn_arena_300\critic_report.json | export_value | 247 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1906 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 1 | # Critic Report — djinn_arena_300 | INFO | Other_NonASCII |
| 1907 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.072689  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1908 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 31 | \| warning \| underdecorated_area \| decor \| - \| Only 1 unique decoration types — map looks repetitive \| | INFO | Other_NonASCII |
| 1909 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1910 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,9,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1911 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (9,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1912 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 41 | _Priority: critical  •  Category: spawn_ | INFO | Other_NonASCII |
| 1913 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 46 | _Priority: low  •  Category: hunt_ | INFO | Other_NonASCII |
| 1914 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 51 | _Priority: high  •  Category: boss_ | INFO | Other_NonASCII |
| 1915 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 57 | _Priority: high  •  Category: boss_ | INFO | Other_NonASCII |
| 1916 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 63 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1917 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 68 | _Priority: medium  •  Category: decor_ | INFO | Other_NonASCII |
| 1918 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 73 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1919 | output_benchmark\djinn_arena_300\critic_report.md | documentation_text | 78 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1920 | output_benchmark\falcon_150\critic_report.json | export_value | 244 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1921 | output_benchmark\falcon_150\critic_report.json | export_value | 253 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1922 | output_benchmark\falcon_150\critic_report.json | export_value | 262 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1923 | output_benchmark\falcon_150\critic_report.md | documentation_text | 1 | # Critic Report — falcon_150 | INFO | Other_NonASCII |
| 1924 | output_benchmark\falcon_150\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.923061  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1925 | output_benchmark\falcon_150\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1926 | output_benchmark\falcon_150\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (24,24,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1927 | output_benchmark\falcon_150\critic_report.md | documentation_text | 37 | \| warning \| bottleneck \| pathfinding \| (24,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1928 | output_benchmark\falcon_150\critic_report.md | documentation_text | 42 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1929 | output_benchmark\falcon_150\critic_report.md | documentation_text | 47 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1930 | output_benchmark\falcon_150\critic_report.md | documentation_text | 52 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1931 | output_benchmark\falcon_150\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1932 | output_benchmark\issavi_300_500\critic_report.json | export_value | 223 | "message": "Hunts 0 and 2 are 120 tiles apart — consider adding a closer hunt", | WARNING | Other_NonASCII |
| 1933 | output_benchmark\issavi_300_500\critic_report.json | export_value | 234 | "message": "Only 3 unique decoration types — map looks repetitive", | WARNING | Other_NonASCII |
| 1934 | output_benchmark\issavi_300_500\critic_report.json | export_value | 303 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1935 | output_benchmark\issavi_300_500\critic_report.json | export_value | 312 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1936 | output_benchmark\issavi_300_500\critic_report.json | export_value | 321 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1937 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 1 | # Critic Report — issavi_300_500 | INFO | Other_NonASCII |
| 1938 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:20.909206  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1939 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 32 | \| warning \| hunt_gap \| hunt \| - \| Hunts 0 and 2 are 120 tiles apart — consider adding a closer hunt \| | INFO | Other_NonASCII |
| 1940 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 33 | \| warning \| underdecorated_area \| decor \| - \| Only 3 unique decoration types — map looks repetitive \| | INFO | Other_NonASCII |
| 1941 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 40 | \| warning \| bottleneck \| pathfinding \| (180,180,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1942 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 41 | \| warning \| bottleneck \| pathfinding \| (219,180,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1943 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 42 | \| warning \| bottleneck \| pathfinding \| (180,219,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1944 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 47 | _Priority: high  •  Category: navigation_ | INFO | Other_NonASCII |
| 1945 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 52 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1946 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 57 | _Priority: medium  •  Category: decor_ | INFO | Other_NonASCII |
| 1947 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 62 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1948 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 67 | _Priority: critical  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1949 | output_benchmark\issavi_300_500\critic_report.md | documentation_text | 72 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1950 | output_benchmark\library_200\critic_report.json | export_value | 199 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1951 | output_benchmark\library_200\critic_report.json | export_value | 208 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1952 | output_benchmark\library_200\critic_report.json | export_value | 217 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1953 | output_benchmark\library_200\critic_report.md | documentation_text | 1 | # Critic Report — library_200 | INFO | Other_NonASCII |
| 1954 | output_benchmark\library_200\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.827241  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1955 | output_benchmark\library_200\critic_report.md | documentation_text | 31 | \| warning \| bottleneck \| pathfinding \| (19,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1956 | output_benchmark\library_200\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1957 | output_benchmark\library_200\critic_report.md | documentation_text | 33 | \| warning \| bottleneck \| pathfinding \| (0,19,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1958 | output_benchmark\library_200\critic_report.md | documentation_text | 38 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1959 | output_benchmark\library_200\critic_report.md | documentation_text | 43 | _Priority: low  •  Category: hunt_ | INFO | Other_NonASCII |
| 1960 | output_benchmark\library_200\critic_report.md | documentation_text | 48 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1961 | output_benchmark\library_200\critic_report.md | documentation_text | 53 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1962 | output_benchmark\library_200\critic_report.md | documentation_text | 58 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1963 | output_benchmark\library_200\critic_report.md | documentation_text | 63 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1964 | output_benchmark\roshamuul_400_600\critic_report.json | export_value | 214 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1965 | output_benchmark\roshamuul_400_600\critic_report.json | export_value | 223 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1966 | output_benchmark\roshamuul_400_600\critic_report.json | export_value | 232 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1967 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 1 | # Critic Report — roshamuul_400_600 | INFO | Other_NonASCII |
| 1968 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.538040  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1969 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 32 | \| warning \| bottleneck \| pathfinding \| (0,39,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1970 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 33 | \| warning \| bottleneck \| pathfinding \| (39,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1971 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1972 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 39 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1973 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 44 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1974 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 49 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1975 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 54 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1976 | output_benchmark\roshamuul_400_600\critic_report.md | documentation_text | 59 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1977 | output_benchmark\soul_war_300\critic_report.json | export_value | 232 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1978 | output_benchmark\soul_war_300\critic_report.json | export_value | 241 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1979 | output_benchmark\soul_war_300\critic_report.json | export_value | 250 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1980 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 1 | # Critic Report — soul_war_300 | INFO | Other_NonASCII |
| 1981 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:21.723507  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1982 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 34 | \| warning \| bottleneck \| pathfinding \| (29,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1983 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1984 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (0,29,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1985 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 41 | _Priority: medium  •  Category: visual_ | INFO | Other_NonASCII |
| 1986 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 46 | _Priority: medium  •  Category: density_ | INFO | Other_NonASCII |
| 1987 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 51 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 1988 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 56 | _Priority: low  •  Category: boss_ | INFO | Other_NonASCII |
| 1989 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 61 | _Priority: low  •  Category: city_ | INFO | Other_NonASCII |
| 1990 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 66 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 1991 | output_benchmark\soul_war_300\critic_report.md | documentation_text | 71 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 1992 | output_benchmark\venore_80\critic_report.json | export_value | 248 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1993 | output_benchmark\venore_80\critic_report.json | export_value | 257 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1994 | output_benchmark\venore_80\critic_report.json | export_value | 266 | "message": "Navigation bottleneck detected — routes funnel through this tile", | WARNING | Other_NonASCII |
| 1995 | output_benchmark\venore_80\critic_report.md | documentation_text | 1 | # Critic Report — venore_80 | INFO | Other_NonASCII |
| 1996 | output_benchmark\venore_80\critic_report.md | documentation_text | 3 | _Generated: 2026-06-08T15:14:22.391718  •  Version: 1.0_ | INFO | Other_NonASCII |
| 1997 | output_benchmark\venore_80\critic_report.md | documentation_text | 35 | \| warning \| bottleneck \| pathfinding \| (29,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1998 | output_benchmark\venore_80\critic_report.md | documentation_text | 36 | \| warning \| bottleneck \| pathfinding \| (0,0,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 1999 | output_benchmark\venore_80\critic_report.md | documentation_text | 37 | \| warning \| bottleneck \| pathfinding \| (0,29,7) \| Navigation bottleneck detected — routes funnel through this tile \| | INFO | Other_NonASCII |
| 2000 | output_benchmark\venore_80\critic_report.md | documentation_text | 42 | _Priority: low  •  Category: spawn_ | INFO | Other_NonASCII |
| 2001 | output_benchmark\venore_80\critic_report.md | documentation_text | 47 | _Priority: medium  •  Category: region_ | INFO | Other_NonASCII |
| 2002 | output_benchmark\venore_80\critic_report.md | documentation_text | 52 | _Priority: medium  •  Category: pathfinding_ | INFO | Other_NonASCII |
| 2003 | rag\retrieval.py | other_non_ascii | 26 | title = doc.get("title", "sin título") | INFO | Latin_Extended |
| 2004 | rag\retrieval.py | other_non_ascii | 32 | lines.append("No se encontró contexto relevante.") | INFO | Latin_Extended |
| 2005 | release\MAP_GUIDE.md | documentation_text | 1 | # Test_Package — Map Guide | INFO | Other_NonASCII |
| 2006 | release\README.md | documentation_text | 1 | # Test_Package — RME Expansion | INFO | Other_NonASCII |
| 2007 | release\README.md | documentation_text | 15 | - `test_package.otbm` — Main map file | INFO | Other_NonASCII |
| 2008 | release\README.md | documentation_text | 16 | - `test_package.lua` — Lua scripts (if applicable) | INFO | Other_NonASCII |
| 2009 | release\README.md | documentation_text | 17 | - `monster.xml` — Monster spawn configuration | INFO | Other_NonASCII |
| 2010 | release\README.md | documentation_text | 18 | - `npc.xml` — NPC definitions | INFO | Other_NonASCII |
| 2011 | release\README.md | documentation_text | 19 | - `zones.xml` — Zone metadata | INFO | Other_NonASCII |
| 2012 | release\README.md | documentation_text | 20 | - `MAP_GUIDE.md` — Complete zone guide | INFO | Other_NonASCII |
| 2013 | release\README.md | documentation_text | 21 | - `SPAWN_TABLE.md` — Detailed spawn distribution | INFO | Other_NonASCII |
| 2014 | release\README.md | documentation_text | 22 | - `MONSTER_LIST.md` — Monster stats and loot | INFO | Other_NonASCII |
| 2015 | release\README.md | documentation_text | 23 | - `NPC_LIST.md` — NPC locations | INFO | Other_NonASCII |
| 2016 | release\README.md | documentation_text | 24 | - `CHANGELOG.md` — Version history | INFO | Other_NonASCII |
| 2017 | release\issavi_roshamuul_v1\docs\MAP_GUIDE.md | documentation_text | 1 | # Issavi_Roshamuul_V1 — Map Guide | INFO | Other_NonASCII |
| 2018 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 1 | # Issavi_Roshamuul_V1 — RME Expansion | INFO | Other_NonASCII |
| 2019 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 15 | - `issavi_roshamuul_v1.otbm` — Main map file | INFO | Other_NonASCII |
| 2020 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 16 | - `issavi_roshamuul_v1.lua` — Lua scripts (if applicable) | INFO | Other_NonASCII |
| 2021 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 17 | - `monster.xml` — Monster spawn configuration | INFO | Other_NonASCII |
| 2022 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 18 | - `npc.xml` — NPC definitions | INFO | Other_NonASCII |
| 2023 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 19 | - `zones.xml` — Zone metadata | INFO | Other_NonASCII |
| 2024 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 20 | - `MAP_GUIDE.md` — Complete zone guide | INFO | Other_NonASCII |
| 2025 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 21 | - `SPAWN_TABLE.md` — Detailed spawn distribution | INFO | Other_NonASCII |
| 2026 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 22 | - `MONSTER_LIST.md` — Monster stats and loot | INFO | Other_NonASCII |
| 2027 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 23 | - `NPC_LIST.md` — NPC locations | INFO | Other_NonASCII |
| 2028 | release\issavi_roshamuul_v1\docs\README.md | documentation_text | 24 | - `CHANGELOG.md` — Version history | INFO | Other_NonASCII |
| 2029 | tests\test_autonomous_designer.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2030 | tests\test_autonomous_designer.py | other_non_ascii | 2 | HITO 18 â€” Tests for :mod:`agente_rme.core.designer.autonomous_designer`. | INFO | Other_NonASCII, Latin_Extended |
| 2031 | tests\test_blueprint_extractor_hito13.py | other_non_ascii | 2 | Tests obligatorios para HITO 13 — Blueprint Extractor. | INFO | Other_NonASCII |
| 2032 | tests\test_blueprint_extractor_hito13.py | other_non_ascii | 5 | OTBM → WorldModel → Blueprint | INFO | Other_NonASCII |
| 2033 | tests\test_blueprint_extractor_hito13.py | comment | 123 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2034 | tests\test_blueprint_extractor_hito13.py | comment | 125 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2035 | tests\test_blueprint_extractor_hito13.py | comment | 238 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2036 | tests\test_blueprint_extractor_hito13.py | comment | 240 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2037 | tests\test_blueprint_extractor_hito13.py | comment | 389 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2038 | tests\test_blueprint_extractor_hito13.py | comment | 391 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2039 | tests\test_blueprint_extractor_hito13.py | comment | 544 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2040 | tests\test_blueprint_extractor_hito13.py | comment | 546 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2041 | tests\test_blueprint_extractor_hito13.py | comment | 820 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2042 | tests\test_blueprint_extractor_hito13.py | comment | 822 | # ────────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2043 | tests\test_blueprint_extractor_hito13.py | docstring | 839 | """Pipeline completo: WorldDict → Theme → Patterns → Structures → Blueprint → JSON.""" | WARNING | Other_NonASCII |
| 2044 | tests\test_blueprint_extractor_hito13.py | comment | 954 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2045 | tests\test_blueprint_extractor_hito13.py | comment | 956 | # ═══════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2046 | tests\test_blueprint_learner.py | other_non_ascii | 2 | Tests for HITO 17 — Blueprint Learner and related modules. | INFO | Other_NonASCII |
| 2047 | tests\test_boss_generator.py | other_non_ascii | 2 | Tests for BossGenerator — validates boss encounter generation. | INFO | Other_NonASCII |
| 2048 | tests\test_city_analyzer.py | comment | 37 | # don't contain a service keyword themselves — they DO contain "city" via | WARNING | Other_NonASCII |
| 2049 | tests\test_content_balancer.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2050 | tests\test_content_balancer.py | other_non_ascii | 2 | HITO 18 â€” Tests for :mod:`agente_rme.core.designer.content_balancer`. | INFO | Other_NonASCII, Latin_Extended |
| 2051 | tests\test_content_balancer.py | comment | 274 | # A very safe zone and a very deadly zone â€” should produce stddev > 0 | WARNING | Other_NonASCII, Latin_Extended |
| 2052 | tests\test_decision_engine.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2053 | tests\test_decision_engine.py | other_non_ascii | 2 | HITO 18 â€” Tests for :mod:`agente_rme.core.designer.decision_engine`. | INFO | Other_NonASCII, Latin_Extended |
| 2054 | tests\test_decision_engine.py | other_non_ascii | 45 | goal = self.engine.parse_goal("levels 50â€“200") | INFO | Other_NonASCII, Latin_Extended |
| 2055 | tests\test_decision_engine.py | other_non_ascii | 54 | goal = self.engine.parse_goal("map 256Ã—256 level 1-50") | INFO | Other_NonASCII, Latin_Extended |
| 2056 | tests\test_hunt_generator.py | other_non_ascii | 2 | Tests for HuntGenerator — the first fully functional generator. | INFO | Other_NonASCII |
| 2057 | tests\test_lua_exporter.py | other_non_ascii | 2 | Tests for Lua Exporter — WorldModel → Lua script pipeline. | INFO | Other_NonASCII |
| 2058 | tests\test_lua_exporter.py | docstring | 159 | """Test the full pipeline: Prompt → WorldModel → Lua → Validation.""" | WARNING | Other_NonASCII |
| 2059 | tests\test_map_analyzer_hito12.py | docstring | 1 | """Tests completos para HITO 12 — Map Analyzer y sub-analizadores.""" | WARNING | Other_NonASCII |
| 2060 | tests\test_map_analyzer_hito12.py | comment | 23 | # Helpers para crear datos sintéticos | WARNING | Latin_Extended |
| 2061 | tests\test_map_analyzer_hito12.py | docstring | 28 | """Crea bytes OTBM mínimos válidos para testing.""" | WARNING | Latin_Extended |
| 2062 | tests\test_map_analyzer_hito12.py | docstring | 80 | """Tests para MapAnalyzer — analizador principal.""" | WARNING | Other_NonASCII |
| 2063 | tests\test_map_analyzer_hito12.py | docstring | 125 | """analyze() procesa OTBM vía análisis directo sin importer.""" | WARNING | Latin_Extended |
| 2064 | tests\test_map_analyzer_hito12.py | docstring | 139 | """analyze() usa importer si está disponible.""" | WARNING | Latin_Extended |
| 2065 | tests\test_map_analyzer_hito12.py | docstring | 173 | """Si el importer falla, hace fallback a análisis directo.""" | WARNING | Latin_Extended |
| 2066 | tests\test_map_analyzer_hito12.py | docstring | 187 | """analyze_to_json() genera JSON válido.""" | WARNING | Latin_Extended |
| 2067 | tests\test_map_analyzer_hito12.py | docstring | 255 | """_normalize_waypoints con lista vacía.""" | WARNING | Latin_Extended |
| 2068 | tests\test_map_analyzer_hito12.py | docstring | 266 | """_read_file_bytes retorna bytes vacíos si no existe.""" | WARNING | Latin_Extended |
| 2069 | tests\test_map_analyzer_hito12.py | docstring | 328 | """_run_derived_analysis puebla los 3 análisis derivados.""" | WARNING | Latin_Extended |
| 2070 | tests\test_map_analyzer_hito12.py | docstring | 353 | """analyze_otbm_spawns con lista vacía.""" | WARNING | Latin_Extended |
| 2071 | tests\test_map_analyzer_hito12.py | docstring | 378 | """analyze_otbm_direct con datos vacíos.""" | WARNING | Latin_Extended |
| 2072 | tests\test_map_analyzer_hito12.py | docstring | 410 | """_classify_zones con contador vacío.""" | WARNING | Latin_Extended |
| 2073 | tests\test_map_analyzer_hito12.py | docstring | 449 | """summarize_spawns con lista vacía.""" | WARNING | Latin_Extended |
| 2074 | tests\test_map_analyzer_hito12.py | docstring | 481 | """analyze con waypoints vacíos.""" | WARNING | Latin_Extended |
| 2075 | tests\test_map_analyzer_hito12.py | docstring | 487 | """analyze con waypoints genera análisis completo.""" | WARNING | Latin_Extended |
| 2076 | tests\test_map_analyzer_hito12.py | docstring | 537 | """_nearest_waypoint_for_spawns encuentra el más cercano.""" | WARNING | Latin_Extended |
| 2077 | tests\test_map_analyzer_hito12.py | docstring | 548 | """_nearest_waypoint_for_spawns con entradas vacías.""" | WARNING | Latin_Extended |
| 2078 | tests\test_map_analyzer_hito12.py | docstring | 560 | """_find_furthest_pair con lista vacía.""" | WARNING | Latin_Extended |
| 2079 | tests\test_map_analyzer_hito12.py | docstring | 564 | """_find_closest_pair con lista vacía.""" | WARNING | Latin_Extended |
| 2080 | tests\test_map_analyzer_hito12.py | docstring | 568 | """_cluster_waypoints con lista vacía.""" | WARNING | Latin_Extended |
| 2081 | tests\test_map_analyzer_hito12.py | comment | 579 | # A y B deberían estar en el mismo cluster, C en otro | WARNING | Latin_Extended |
| 2082 | tests\test_map_analyzer_hito12.py | docstring | 596 | """analyze con datos vacíos.""" | WARNING | Latin_Extended |
| 2083 | tests\test_map_analyzer_hito12.py | docstring | 628 | """_compute_tile_density vacío.""" | WARNING | Latin_Extended |
| 2084 | tests\test_map_analyzer_hito12.py | docstring | 640 | """_compute_item_density vacío.""" | WARNING | Latin_Extended |
| 2085 | tests\test_map_analyzer_hito12.py | docstring | 645 | """_compute_spawn_density calcula métricas.""" | WARNING | Latin_Extended |
| 2086 | tests\test_map_analyzer_hito12.py | docstring | 652 | """_compute_spawn_density vacío.""" | WARNING | Latin_Extended |
| 2087 | tests\test_map_analyzer_hito12.py | docstring | 668 | """_compute_spawn_heatmap vacío.""" | WARNING | Latin_Extended |
| 2088 | tests\test_map_analyzer_hito12.py | docstring | 680 | """_compute_floor_distribution vacío.""" | WARNING | Latin_Extended |
| 2089 | tests\test_map_analyzer_hito12.py | docstring | 690 | """_categorize_density asigna categoría.""" | WARNING | Latin_Extended |
| 2090 | tests\test_map_analyzer_hito12.py | docstring | 710 | """analyze con datos vacíos.""" | WARNING | Latin_Extended |
| 2091 | tests\test_map_analyzer_hito12.py | docstring | 742 | """_analyze_structural_composition vacío.""" | WARNING | Latin_Extended |
| 2092 | tests\test_map_analyzer_hito12.py | docstring | 780 | """_classify_building clasifica tipo de construcción.""" | WARNING | Latin_Extended |
| 2093 | tests\test_map_analyzer_hito12.py | docstring | 816 | """_compute_complexity calcula métricas.""" | WARNING | Latin_Extended |
| 2094 | tests\test_map_analyzer_hito12.py | docstring | 882 | """detect_style con tiles vacíos.""" | WARNING | Latin_Extended |
| 2095 | tests\test_map_analyzer_hito12.py | docstring | 921 | """extract_pattern genera patrón.""" | WARNING | Latin_Extended |
| 2096 | tests\test_mvp_integration.py | other_non_ascii | 2 | MVP V0.1 Integration Tests — Verifica todos los sprints de extremo a extremo. | INFO | Other_NonASCII |
| 2097 | tests\test_navigation_analyzer.py | comment | 67 | # (6,2) has only 1 neighbor — a dead end | WARNING | Other_NonASCII |
| 2098 | tests\test_otbm_exporter.py | other_non_ascii | 2 | Tests para OTBMExporter — WorldModel → .otbm + XMLs. | INFO | Other_NonASCII |
| 2099 | tests\test_otbm_exporter.py | other_non_ascii | 4 | Test mínimo obligatorio: | INFO | Latin_Extended |
| 2100 | tests\test_otbm_exporter.py | other_non_ascii | 12 | Test de integración: | INFO | Latin_Extended |
| 2101 | tests\test_otbm_exporter.py | other_non_ascii | 52 | assert Path("output/test_mandatory.otbm").exists(), "test.otbm no se generó" | INFO | Latin_Extended |
| 2102 | tests\test_otbm_exporter.py | other_non_ascii | 53 | assert os.path.getsize("output/test_mandatory.otbm") > 0, "test.otbm está vacío" | INFO | Latin_Extended |
| 2103 | tests\test_otbm_exporter.py | other_non_ascii | 61 | assert validation.is_valid, f"OTBM inválido: {validation.errors}" | INFO | Latin_Extended |
| 2104 | tests\test_otbm_exporter.py | comment | 71 | # Tests de integración | WARNING | Latin_Extended |
| 2105 | tests\test_otbm_exporter.py | comment | 127 | # Estructura y región | WARNING | Latin_Extended |
| 2106 | tests\test_otbm_exporter.py | docstring | 177 | """Exportar mundo vacío.""" | WARNING | Latin_Extended |
| 2107 | tests\test_otbm_exporter.py | comment | 198 | # Validar datos inválidos | WARNING | Latin_Extended |
| 2108 | tests\test_otbm_exporter.py | docstring | 244 | """Verificar estructura del reporte de exportación.""" | WARNING | Latin_Extended |
| 2109 | tests\test_pattern_miner.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2110 | tests\test_pattern_miner.py | other_non_ascii | 2 | Tests for HITO 17 â€” Pattern Miner. | INFO | Other_NonASCII, Latin_Extended |
| 2111 | tests\test_preview_generator.py | other_non_ascii | 2 | Tests para HITO 9 REAL — Preview Generator V1. | INFO | Other_NonASCII |
| 2112 | tests\test_preview_generator.py | other_non_ascii | 5 | 1. Test obligatorio: WorldModel → Tile → PreviewGenerator → preview.png | INFO | Other_NonASCII |
| 2113 | tests\test_preview_generator.py | other_non_ascii | 6 | 2. Generación de preview.png con colores | INFO | Latin_Extended |
| 2114 | tests\test_preview_generator.py | other_non_ascii | 7 | 3. Generación de preview_minimap.png con escalado | INFO | Latin_Extended |
| 2115 | tests\test_preview_generator.py | other_non_ascii | 8 | 4. Generación de preview.json con estadísticas | INFO | Latin_Extended |
| 2116 | tests\test_preview_generator.py | other_non_ascii | 9 | 5. Pipeline completo: WorldModel → PreviewGenerator → 3 outputs | INFO | Other_NonASCII |
| 2117 | tests\test_preview_generator.py | other_non_ascii | 10 | 6. Clasificación de tiles: ground, wall, spawn, boss, decoration | INFO | Latin_Extended |
| 2118 | tests\test_preview_generator.py | other_non_ascii | 13 | 9. Distinción visual entre: Terreno, Decoración, Spawns, Bosses, Estructuras | INFO | Latin_Extended |
| 2119 | tests\test_preview_generator.py | other_non_ascii | 70 | assert Path("output/test_mandatory.png").exists(), "preview.png no se generó" | INFO | Latin_Extended |
| 2120 | tests\test_preview_generator.py | other_non_ascii | 71 | assert os.path.getsize("output/test_mandatory.png") > 0, "preview.png está vacío" | INFO | Latin_Extended |
| 2121 | tests\test_preview_generator.py | docstring | 83 | """Verificar que los colores de la paleta son tuplas RGB válidas.""" | WARNING | Latin_Extended |
| 2122 | tests\test_preview_generator.py | other_non_ascii | 86 | assert isinstance(c, tuple) and len(c) == 3, f"Color inválido: {c}" | INFO | Latin_Extended |
| 2123 | tests\test_preview_generator.py | print_string | 88 | print("  [OK] Palette colors válidos") | WARNING | Latin_Extended |
| 2124 | tests\test_preview_generator.py | docstring | 92 | """Verificar clasificación de ground IDs.""" | WARNING | Latin_Extended |
| 2125 | tests\test_preview_generator.py | comment | 97 | assert get_color_for_ground(99999) == GROUND  # Desconocido → ground | WARNING | Other_NonASCII |
| 2126 | tests\test_preview_generator.py | docstring | 102 | """Verificar clasificación de items.""" | WARNING | Latin_Extended |
| 2127 | tests\test_preview_generator.py | comment | 103 | assert get_color_for_item(2153) == DECORATION  # Decoración conocida | WARNING | Latin_Extended |
| 2128 | tests\test_preview_generator.py | comment | 104 | assert get_color_for_item(99999) == DECORATION  # Desconocido → decoración | WARNING | Other_NonASCII, Latin_Extended |
| 2129 | tests\test_preview_generator.py | docstring | 109 | """Verificar detección de bosses.""" | WARNING | Latin_Extended |
| 2130 | tests\test_preview_generator.py | docstring | 152 | """Render de tile con decoración.""" | WARNING | Latin_Extended |
| 2131 | tests\test_preview_generator.py | comment | 154 | tile.items.append(Item(itemid=2153))  # Decoración conocida | WARNING | Latin_Extended |
| 2132 | tests\test_preview_generator.py | docstring | 168 | """Verificar cálculo de bounding box.""" | WARNING | Latin_Extended |
| 2133 | tests\test_preview_generator.py | docstring | 188 | """Bounding box vacío.""" | WARNING | Latin_Extended |
| 2134 | tests\test_preview_generator.py | docstring | 246 | """Generar reporte de estadísticas.""" | WARNING | Latin_Extended |
| 2135 | tests\test_preview_generator.py | docstring | 277 | """Reporte de mundo vacío.""" | WARNING | Latin_Extended |
| 2136 | tests\test_preview_generator.py | comment | 299 | # Tests de integración con WorldGenerator | WARNING | Latin_Extended |
| 2137 | tests\test_preview_generator.py | docstring | 304 | """Pipeline completo: WorldGenerator → PreviewGenerator → preview.png + .json.""" | WARNING | Other_NonASCII |
| 2138 | tests\test_preview_generator.py | other_non_ascii | 316 | assert "png" in result, f"No se generó PNG: {result}" | INFO | Latin_Extended |
| 2139 | tests\test_preview_generator.py | other_non_ascii | 318 | assert os.path.getsize(result["png"]) > 0, f"PNG vacío: {result['png']}" | INFO | Latin_Extended |
| 2140 | tests\test_preview_generator.py | other_non_ascii | 340 | Terreno, Decoración, Spawns, Bosses, Estructuras | INFO | Latin_Extended |
| 2141 | tests\test_preview_generator.py | comment | 347 | # Decoración (item) | WARNING | Latin_Extended |
| 2142 | tests\test_preview_generator.py | print_string | 373 | print("  [OK] Distinción visual: GROUND, DECORATION, SPAWN, BOSS, STRUCTURE confirmados") | WARNING | Latin_Extended |
| 2143 | tests\test_preview_generator.py | docstring | 377 | """Preview de mundo vacío.""" | WARNING | Latin_Extended |
| 2144 | tests\test_preview_generator.py | comment | 381 | # No PNG (no tiles), pero puede generar JSON con reporte vacío | WARNING | Latin_Extended |
| 2145 | tests\test_preview_generator.py | other_non_ascii | 382 | assert "png" not in result, "No debería generar PNG sin tiles" | INFO | Latin_Extended |
| 2146 | tests\test_preview_generator.py | docstring | 395 | """Preview con múltiples capas Z.""" | WARNING | Latin_Extended |
| 2147 | tests\test_preview_generator.py | other_non_ascii | 442 | ("Distinción visual", test_distinguir_visualmente), | INFO | Latin_Extended |
| 2148 | tests\test_production.py | other_non_ascii | 2 | Comprehensive Production Test Suite — RME Map AI Agent v2.0 | INFO | Other_NonASCII |
| 2149 | tests\test_production.py | comment | 40 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2150 | tests\test_production.py | comment | 42 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2151 | tests\test_production.py | comment | 121 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2152 | tests\test_production.py | comment | 123 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2153 | tests\test_production.py | comment | 205 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2154 | tests\test_production.py | comment | 207 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2155 | tests\test_production.py | comment | 272 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2156 | tests\test_production.py | comment | 274 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2157 | tests\test_production.py | comment | 340 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2158 | tests\test_production.py | comment | 342 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2159 | tests\test_production.py | comment | 399 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2160 | tests\test_production.py | comment | 401 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2161 | tests\test_production.py | comment | 439 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2162 | tests\test_production.py | comment | 441 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2163 | tests\test_production.py | comment | 509 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2164 | tests\test_production.py | comment | 511 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2165 | tests\test_production.py | comment | 582 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2166 | tests\test_production.py | comment | 584 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2167 | tests\test_production.py | comment | 613 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2168 | tests\test_production.py | comment | 615 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2169 | tests\test_production.py | comment | 700 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2170 | tests\test_production.py | comment | 702 | # ═══════════════════════════════════════════════════════════════════════════════ | WARNING | Other_NonASCII |
| 2171 | tests\test_quest_generator.py | other_non_ascii | 2 | Tests for QuestGenerator — validates quest content generation. | INFO | Other_NonASCII |
| 2172 | tests\test_quest_generator.py | docstring | 202 | """Package should survive to_dict → from_dict roundtrip.""" | WARNING | Other_NonASCII |
| 2173 | tests\test_raid_generator.py | other_non_ascii | 2 | Tests for RaidGenerator — validates raid content generation. | INFO | Other_NonASCII |
| 2174 | tests\test_rme_validator.py | comment | 5 | # ---- Casos válidos ---- | WARNING | Latin_Extended |
| 2175 | tests\test_rme_validator.py | comment | 72 | # ---- Casos inválidos ---- | WARNING | Latin_Extended |
| 2176 | tests\test_score_calculator.py | comment | 25 | # Only visual and navigation supplied — renormalized to 0.5/0.5 | WARNING | Other_NonASCII |
| 2177 | tests\test_similarity_engine.py | other_non_ascii | 2 | Tests for HITO 17 — Similarity Engine. | INFO | Other_NonASCII |
| 2178 | tests\test_visual_critic.py | other_non_ascii | 2 | Tests for the Visual Map Critic AI — top-level orchestrator. | INFO | Other_NonASCII |
| 2179 | tests\test_world_generator.py | other_non_ascii | 2 | Tests for WorldGenerator — the main orchestrator. | INFO | Other_NonASCII |
| 2180 | tests\agents\test_agent_registry.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2181 | tests\agents\test_architect_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2182 | tests\agents\test_architect_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2183 | tests\agents\test_architect_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2184 | tests\agents\test_balance_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2185 | tests\agents\test_balance_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2186 | tests\agents\test_balance_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2187 | tests\agents\test_expansion_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2188 | tests\agents\test_expansion_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2189 | tests\agents\test_expansion_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2190 | tests\agents\test_export_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2191 | tests\agents\test_mapper_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2192 | tests\agents\test_mapper_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2193 | tests\agents\test_mapper_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2194 | tests\agents\test_orchestrator_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2195 | tests\agents\test_playtest_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2196 | tests\agents\test_qa_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2197 | tests\agents\test_qa_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2198 | tests\agents\test_qa_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2199 | tests\agents\test_quest_agent.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2200 | tests\agents\test_quest_agent_coverage.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2201 | tests\agents\test_quest_agent_coverage.py | other_non_ascii | 4 | Hito 26.1D â€” covers all branches: | INFO | Other_NonASCII, Latin_Extended |
| 2202 | tests\autonomous\test_autonomous_director.py | other_non_ascii | 1 | ﻿"""Tests for the Autonomous Director.""" | INFO | Other_NonASCII |
| 2203 | tests\autonomous\test_world_objectives.py | comment | 27 | # 0.4 / 0.8 = 0.5, weight 1.0 → 0.5 | WARNING | Other_NonASCII |
| 2204 | tests\autonomous\test_world_objectives.py | comment | 47 | score = obj.evaluate(0.4)  # below threshold → 0.5 penalty | WARNING | Other_NonASCII |
| 2205 | tests\campaign\test_campaign_export.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2206 | tests\campaign\test_campaign_export.py | comment | 211 | # Fallback contract â€” campaign is NEVER None | WARNING | Other_NonASCII, Latin_Extended |
| 2207 | tests\campaign\test_campaign_fallback.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2208 | tests\campaign\test_campaign_pipeline.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2209 | tests\campaign\test_campaign_pipeline.py | other_non_ascii | 2 | Tests for the prompt â†’ campaign.json pipeline. | INFO | Other_NonASCII, Latin_Extended |
| 2210 | tests\campaign\test_campaign_pipeline.py | other_non_ascii | 6 | â†“ | INFO | Other_NonASCII, Latin_Extended |
| 2211 | tests\campaign\test_campaign_pipeline.py | other_non_ascii | 8 | â†“ | INFO | Other_NonASCII, Latin_Extended |
| 2212 | tests\campaign\test_campaign_pipeline.py | other_non_ascii | 10 | â†“ | INFO | Other_NonASCII, Latin_Extended |
| 2213 | tests\campaign\test_campaign_pipeline.py | comment | 59 | # Prompt â†’ QuestAgent | WARNING | Other_NonASCII, Latin_Extended |
| 2214 | tests\campaign\test_campaign_pipeline.py | comment | 117 | # QuestAgent â†’ ExportAgent | WARNING | Other_NonASCII, Latin_Extended |
| 2215 | tests\campaign\test_campaign_pipeline.py | docstring | 122 | """The output of QuestAgent feeds into ExportAgent â€” verify the chain.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2216 | tests\campaign\test_campaign_pipeline.py | comment | 162 | # ExportAgent â†’ campaign.json | WARNING | Other_NonASCII, Latin_Extended |
| 2217 | tests\campaign\test_campaign_pipeline.py | comment | 228 | # File â†’ Validator | WARNING | Other_NonASCII, Latin_Extended |
| 2218 | tests\campaign\test_campaign_pipeline.py | docstring | 270 | """Prompt â†’ CampaignPackage â†’ campaign.json â†’ Validator.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2219 | tests\common\test_datetime_timezone.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2220 | tests\common\test_datetime_timezone.py | comment | 112 | # Binary or unreadable â€” skip. | WARNING | Other_NonASCII, Latin_Extended |
| 2221 | tests\common\test_timezone_compliance.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2222 | tests\common\test_timezone_compliance.py | other_non_ascii | 2 | HITO 26.1E â€” Timezone Compliance Tests | INFO | Other_NonASCII, Latin_Extended |
| 2223 | tests\common\test_timezone_compliance.py | docstring | 89 | """MultiAgentResult.completed_at â†’ UTC + ISO8601.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2224 | tests\common\test_timezone_compliance.py | docstring | 96 | """AgentResponse.timestamp â†’ UTC + ISO8601.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2225 | tests\common\test_timezone_compliance.py | docstring | 103 | """AgentTask.{created_at,completed_at} â†’ UTC + ISO8601.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2226 | tests\common\test_timezone_compliance.py | docstring | 115 | """WorkflowState.{started_at,completed_at} â†’ UTC + ISO8601.""" | WARNING | Other_NonASCII, Latin_Extended |
| 2227 | tests\integration\test_agent_error_recovery.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2228 | tests\integration\test_autonomous_50world_benchmark.py | comment | 1 | """E2E test #4 — 50-world benchmark (Hito 30 acceptance criterion). | WARNING | Other_NonASCII |
| 2229 | tests\integration\test_autonomous_50world_benchmark.py | comment | 77 | """E2E #4 — Run the full 50-world benchmark and verify convergence metrics.""" | WARNING | Other_NonASCII |
| 2230 | tests\integration\test_autonomous_critic_loop.py | other_non_ascii | 1 | ﻿"""Integration test: Autonomous Designer + Visual Critic loop.""" | INFO | Other_NonASCII |
| 2231 | tests\integration\test_autonomous_export_pipeline.py | comment | 63 | # Without matplotlib we may get none — that's also acceptable | WARNING | Other_NonASCII |
| 2232 | tests\integration\test_autonomous_pipeline.py | other_non_ascii | 3 | These tests run the full end-to-end pipeline (Director → Planner → | INFO | Other_NonASCII |
| 2233 | tests\integration\test_autonomous_pipeline.py | other_non_ascii | 4 | Decision Engine → Optimizer → Export) with the real critic, | INFO | Other_NonASCII |
| 2234 | tests\integration\test_autonomous_pipeline.py | other_non_ascii | 27 | prompt = "Crear expansión Issavi + Roshamuul nivel 300-500, 3 hunts, 2 bosses, 1 raid" | INFO | Latin_Extended |
| 2235 | tests\integration\test_critic_e2e_pipeline.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2236 | tests\integration\test_critic_e2e_pipeline.py | other_non_ascii | 128 | prompt="Crear expansiÃ³n Issavi + Roshamuul nivel 300-500", | INFO | Other_NonASCII, Latin_Extended |
| 2237 | tests\integration\test_critic_pipeline.py | other_non_ascii | 2 | Integration tests for the critic — end-to-end usage from build world to report. | INFO | Other_NonASCII |
| 2238 | tests\integration\test_multi_agent_export.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2239 | tests\integration\test_multi_agent_pipeline.py | other_non_ascii | 1 | ﻿""" | INFO | Other_NonASCII |
| 2240 | tests\knowledge\test_city_extractor.py | comment | 86 | # only one — first match wins | WARNING | Other_NonASCII |
| 2241 | tests\knowledge\test_other_extractors.py | comment | 269 | # only one — first match wins | WARNING | Other_NonASCII |
| 2242 | tests\knowledge\test_recommender.py | comment | 128 | # quality_score=100 should not affect ranking — only similarity | WARNING | Other_NonASCII |
| 2243 | tests\knowledge\test_similarity_engine.py | comment | 33 | # Slightly different vector — close to 1 but not exactly. | WARNING | Other_NonASCII |
| 2244 | tests\knowledge\__init__.py | docstring | 1 | """HITO 28 — knowledge subsystem tests.""" | WARNING | Other_NonASCII |
| 2245 | tests\lua\test_lua_backward_compatibility.py | other_non_ascii | 4 | HITO 26.1B — verifies that every previously-supported call signature | INFO | Other_NonASCII |
| 2246 | tests\lua\test_lua_backward_compatibility.py | comment | 108 | # Behavioural compatibility — outputs are the same as before | WARNING | Other_NonASCII |
| 2247 | tests\lua\test_lua_generator.py | other_non_ascii | 2 | Tests for LuaGenerator — both call signatures and the generated code. | INFO | Other_NonASCII |
| 2248 | tests\lua\test_lua_generator.py | other_non_ascii | 5 | * generate(world)  — works without a spawn plan | INFO | Other_NonASCII |
| 2249 | tests\lua\test_lua_generator.py | other_non_ascii | 6 | * generate(world, spawn_plan) — works with explicit plan | INFO | Other_NonASCII |
| 2250 | tests\lua\test_lua_generator.py | other_non_ascii | 7 | * generate(world, plan_dict) — works with a dict plan | INFO | Other_NonASCII |
| 2251 | tests\lua\test_lua_pipeline.py | other_non_ascii | 4 | HITO 26.1B — full pipeline: | INFO | Other_NonASCII |
| 2252 | tests\lua\test_lua_pipeline.py | other_non_ascii | 7 | ↓ | INFO | Other_NonASCII |
| 2253 | tests\lua\test_lua_pipeline.py | other_non_ascii | 9 | ↓ | INFO | Other_NonASCII |
| 2254 | tests\lua\test_lua_pipeline.py | other_non_ascii | 11 | ↓ | INFO | Other_NonASCII |
| 2255 | tests\lua\test_lua_pipeline.py | comment | 63 | # Pipeline: Prompt → WorldModel → generated.lua | WARNING | Other_NonASCII |
| 2256 | tests\lua\test_lua_pipeline.py | comment | 93 | # archivo no vacío | WARNING | Latin_Extended |
| 2257 | tests\lua\test_lua_pipeline.py | comment | 95 | # sintaxis válida | WARNING | Latin_Extended |
| 2258 | tests\lua\test_lua_pipeline.py | comment | 164 | # archivo existe y no vacío | WARNING | Latin_Extended |
| 2259 | tests\lua\test_lua_pipeline.py | comment | 167 | # sintaxis válida | WARNING | Latin_Extended |
| 2260 | tests\lua\test_lua_pipeline.py | comment | 301 | # No spawn_plan provided — auto-fallback must build one | WARNING | Other_NonASCII |
| 2261 | tests\lua\test_lua_pipeline.py | docstring | 338 | """Run the full chain: SpawnGenerator → SpawnPlan → LuaGenerator.""" | WARNING | Other_NonASCII |
| 2262 | tests\lua\test_spawn_generation.py | other_non_ascii | 2 | Tests for the world → SpawnPlan auto-generation path. | INFO | Other_NonASCII |
| 2263 | tests\lua\test_spawn_generation.py | other_non_ascii | 4 | HITO 26.1B — when a caller invokes ``LuaGenerator.generate(world)`` | INFO | Other_NonASCII |
| 2264 | tests\lua\test_spawn_plan_generation.py | other_non_ascii | 2 | Tests for SpawnPlan / SpawnGenerator — verify the spawns the Lua generator consumes. | INFO | Other_NonASCII |
| 2265 | tests\otbm\test_otbm_export_validation.py | other_non_ascii | 6 | ↓ | INFO | Other_NonASCII |
| 2266 | tests\otbm\test_otbm_export_validation.py | other_non_ascii | 8 | ↓ | INFO | Other_NonASCII |
| 2267 | tests\otbm\test_otbm_export_validation.py | other_non_ascii | 10 | ↓ | INFO | Other_NonASCII |
| 2268 | tests\otbm\test_otbm_export_validation.py | other_non_ascii | 12 | ↓ | INFO | Other_NonASCII |
| 2269 | tests\otbm\test_otbm_export_validation.py | identifier | 33 | → | CRITICAL | Other_NonASCII |
| 2270 | tests\otbm\test_otbm_importer.py | comment | 143 | # Test 1: OtbmParser — basic parsing | WARNING | Other_NonASCII |
| 2271 | tests\otbm\test_otbm_importer.py | print_string | 181 | print(f"[PASS] test_parser_basic — parsed OTBM with {len(root['children'])} child nodes") | WARNING | Other_NonASCII |
| 2272 | tests\otbm\test_otbm_importer.py | comment | 185 | # Test 2: OtbmParser — invalid magic | WARNING | Other_NonASCII |
| 2273 | tests\otbm\test_otbm_importer.py | print_string | 197 | print(f"[PASS] test_parser_invalid_magic — correctly rejected: {e}") | WARNING | Other_NonASCII |
| 2274 | tests\otbm\test_otbm_importer.py | comment | 201 | # Test 3: OtbmParser — truncated data | WARNING | Other_NonASCII |
| 2275 | tests\otbm\test_otbm_importer.py | print_string | 212 | print(f"[PASS] test_parser_truncated — correctly rejected truncated data") | WARNING | Other_NonASCII |
| 2276 | tests\otbm\test_otbm_importer.py | comment | 216 | # Test 4: NodeDecoder — decode root | WARNING | Other_NonASCII |
| 2277 | tests\otbm\test_otbm_importer.py | other_non_ascii | 240 | f"[PASS] test_node_decoder_root — decoded root: {decoded['version']=}, {len(decoded['tile_areas'])} areas" | INFO | Other_NonASCII |
| 2278 | tests\otbm\test_otbm_importer.py | comment | 245 | # Test 5: NodeDecoder — decode tile area | WARNING | Other_NonASCII |
| 2279 | tests\otbm\test_otbm_importer.py | other_non_ascii | 273 | f"[PASS] test_node_decoder_tile_area — {len(decoded['tiles'])} tiles at z={decoded['base_z']}" | INFO | Other_NonASCII |
| 2280 | tests\otbm\test_otbm_importer.py | comment | 278 | # Test 6: NodeDecoder — decode spawns | WARNING | Other_NonASCII |
| 2281 | tests\otbm\test_otbm_importer.py | other_non_ascii | 304 | f"[PASS] test_node_decoder_spawns — {len(decoded['spawn_areas'])} areas, {len(area['monsters'])} monsters" | INFO | Other_NonASCII |
| 2282 | tests\otbm\test_otbm_importer.py | comment | 309 | # Test 7: NodeDecoder — decode towns | WARNING | Other_NonASCII |
| 2283 | tests\otbm\test_otbm_importer.py | print_string | 332 | print(f"[PASS] test_node_decoder_towns — {len(decoded['towns'])} towns") | WARNING | Other_NonASCII |
| 2284 | tests\otbm\test_otbm_importer.py | comment | 336 | # Test 8: NodeDecoder — decode waypoints | WARNING | Other_NonASCII |
| 2285 | tests\otbm\test_otbm_importer.py | print_string | 358 | print(f"[PASS] test_node_decoder_waypoints — {len(decoded['waypoints'])} waypoints") | WARNING | Other_NonASCII |
| 2286 | tests\otbm\test_otbm_importer.py | comment | 362 | # Test 9: TileDecoder — convert tile | WARNING | Other_NonASCII |
| 2287 | tests\otbm\test_otbm_importer.py | print_string | 389 | print(f"[PASS] test_tile_decoder — {len(tiles)} tiles converted") | WARNING | Other_NonASCII |
| 2288 | tests\otbm\test_otbm_importer.py | comment | 393 | # Test 10: ItemDecoder — decode item | WARNING | Other_NonASCII |
| 2289 | tests\otbm\test_otbm_importer.py | print_string | 423 | print(f"[PASS] test_item_decoder — item_id={decoded['item_id']}") | WARNING | Other_NonASCII |
| 2290 | tests\otbm\test_otbm_importer.py | comment | 427 | # Test 11: WorldBuilder — build full WorldModel dict | WARNING | Other_NonASCII |
| 2291 | tests\otbm\test_otbm_importer.py | other_non_ascii | 469 | f"[PASS] test_world_builder — {result['tile_count']} tiles, {result['spawn_count']} spawns, " | INFO | Other_NonASCII |
| 2292 | tests\otbm\test_otbm_importer.py | comment | 475 | # Test 12: WorldBuilder — to_worldmodel | WARNING | Other_NonASCII |
| 2293 | tests\otbm\test_otbm_importer.py | other_non_ascii | 512 | f"[PASS] test_world_builder_to_worldmodel — WorldModel with {len(wm.tiles)} tiles, " | INFO | Other_NonASCII |
| 2294 | tests\otbm\test_otbm_importer.py | comment | 518 | # Test 13: OTBMImporter — import file | WARNING | Other_NonASCII |
| 2295 | tests\otbm\test_otbm_importer.py | other_non_ascii | 546 | f"[PASS] test_importer_import_file — imported {result['stats']['tiles']} tiles, " | INFO | Other_NonASCII |
| 2296 | tests\otbm\test_otbm_importer.py | comment | 555 | # Test 14: OTBMImporter — import from bytes | WARNING | Other_NonASCII |
| 2297 | tests\otbm\test_otbm_importer.py | print_string | 571 | print(f"[PASS] test_importer_import_bytes — imported from bytes") | WARNING | Other_NonASCII |
| 2298 | tests\otbm\test_otbm_importer.py | comment | 575 | # Test 15: OTBMImporter — file not found | WARNING | Other_NonASCII |
| 2299 | tests\otbm\test_otbm_importer.py | print_string | 587 | print(f"[PASS] test_importer_file_not_found — handled: {result.get('error')}") | WARNING | Other_NonASCII |
| 2300 | tests\otbm\test_otbm_importer.py | comment | 591 | # Test 16: OTBMImporter — to_worldmodel convenience | WARNING | Other_NonASCII |
| 2301 | tests\otbm\test_otbm_importer.py | print_string | 611 | print(f"[PASS] test_importer_to_worldmodel — WorldModel with {len(wm.tiles)} tiles") | WARNING | Other_NonASCII |
| 2302 | tests\otbm\test_otbm_importer.py | comment | 618 | # Test 17: OTBMImporter — get_preview | WARNING | Other_NonASCII |
| 2303 | tests\otbm\test_otbm_importer.py | other_non_ascii | 643 | f"[PASS] test_importer_preview — {preview['tiles']} tiles, {preview['spawns']} spawns, " | INFO | Other_NonASCII |
| 2304 | tests\otbm\test_otbm_importer.py | comment | 652 | # Test 18: WorldBuilder — invalid data | WARNING | Other_NonASCII |
| 2305 | tests\otbm\test_otbm_importer.py | print_string | 665 | print(f"[PASS] test_world_builder_invalid — handled: {e}") | WARNING | Other_NonASCII |
| 2306 | tests\otbm\test_otbm_importer.py | comment | 669 | # Test 19: Round trip — OTBM -> WorldModel -> OTBM | WARNING | Other_NonASCII |
| 2307 | tests\otbm\test_otbm_importer.py | other_non_ascii | 717 | f"[PASS] test_round_trip_basic — {len(wm.tiles)} tiles, {len(wm.spawns)} spawns, " | INFO | Other_NonASCII |
| 2308 | tests\otbm\test_otbm_importer.py | comment | 723 | # Test 20: Round trip — with items and attributes | WARNING | Other_NonASCII |
| 2309 | tests\otbm\test_otbm_importer.py | print_string | 777 | print(f"[PASS] test_round_trip_with_items — {len(tile_wm.items)} items preserved") | WARNING | Other_NonASCII |
| 2310 | tests\otbm\test_otbm_importer.py | comment | 781 | # Test 21: Round trip — large map | WARNING | Other_NonASCII |
| 2311 | tests\otbm\test_otbm_importer.py | print_string | 826 | print(f"[PASS] test_round_trip_large — 100 tiles preserved") | WARNING | Other_NonASCII |
| 2312 | tests\otbm\test_otbm_importer.py | print_string | 835 | print("  HITO 11: OTBM Importer — Functional Tests") | WARNING | Other_NonASCII |
| 2313 | tests\otbm\test_otbm_large_map.py | comment | 227 | # x=1000 is far from base 0 — offset 1000 > 255 must be normalised | WARNING | Other_NonASCII |
| 2314 | tests\otbm\test_otbm_large_map.py | identifier | 294 | → | CRITICAL | Other_NonASCII |
| 2315 | tests\otbm\test_otbm_large_world.py | comment | 112 | # x=1000 is far from base 0 — offset 1000 > 255 must be normalised | WARNING | Other_NonASCII |
| 2316 | tests\otbm\test_otbm_large_world.py | identifier | 162 | → | CRITICAL | Other_NonASCII |
| 2317 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 2 | Tests de ida y vuelta (roundtrip) para el módulo OTBM. | INFO | Latin_Extended |
| 2318 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 6 | - City map: múltiples tiles con items decorativos | INFO | Latin_Extended |
| 2319 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 9 | - Serialización → validación → deserialización | INFO | Other_NonASCII, Latin_Extended |
| 2320 | tests\otbm\test_otbm_roundtrip.py | docstring | 44 | """Genera un mapa pequeño y verifica roundtrip completo.""" | WARNING | Latin_Extended |
| 2321 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 56 | assert data[:4] == b"OTBM", f"Magic inválido: {data[:4]!r}" | INFO | Latin_Extended |
| 2322 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 61 | assert result.status == "success", f"Validación falló: {result.errors}" | INFO | Latin_Extended |
| 2323 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 77 | f"[PASS] test_small_map — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawns, {len(data)} bytes" | INFO | Other_NonASCII |
| 2324 | tests\otbm\test_otbm_roundtrip.py | comment | 82 | # Test 2: City map (múltiples tiles con items decorativos) | WARNING | Latin_Extended |
| 2325 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 112 | assert result.status == "success", f"Validación falló: {result.errors}" | INFO | Latin_Extended |
| 2326 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 122 | f"[PASS] test_city_map — {len(decoded['tiles'])} tiles, {len(decoded['towns'])} towns, {len(data)} bytes" | INFO | Other_NonASCII |
| 2327 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 157 | assert result.status == "success", f"Validación falló: {result.errors}" | INFO | Latin_Extended |
| 2328 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 168 | f"[PASS] test_hunt_map — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawn areas" | INFO | Other_NonASCII |
| 2329 | tests\otbm\test_otbm_roundtrip.py | other_non_ascii | 207 | assert result.status == "success", f"Validación falló: {result.errors}" | INFO | Latin_Extended |
| 2330 | tests\otbm\test_otbm_roundtrip.py | print_string | 213 | print(f"[PASS] test_boss_room — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawns") | WARNING | Other_NonASCII |
| 2331 | tests\otbm\test_otbm_roundtrip.py | print_string | 242 | print(f"[PASS] test_worldmodel_to_otbm — API alto nivel funciona") | WARNING | Other_NonASCII |
| 2332 | tests\otbm\test_otbm_roundtrip.py | print_string | 282 | print(f"[PASS] test_node_encoder — nodos binarios correctos") | WARNING | Other_NonASCII |
| 2333 | tests\otbm\test_otbm_roundtrip.py | comment | 295 | # Mapa con item ID 0 (inválido) | WARNING | Latin_Extended |
| 2334 | tests\otbm\test_otbm_roundtrip.py | comment | 300 | # ID 0 del ground se resuelve en TileEncoder (no debería ser 0 real) | WARNING | Latin_Extended |
| 2335 | tests\otbm\test_otbm_roundtrip.py | comment | 304 | # Mapa con dimensiones grandes pero válidas | WARNING | Latin_Extended |
| 2336 | tests\otbm\test_otbm_roundtrip.py | print_string | 314 | print(f"[PASS] test_otbr_compatibility — {result2.stats['tiles']} tiles, {len(data2)} bytes") | WARNING | Other_NonASCII |
| 2337 | tests\ui\test_navigation.py | other_non_ascii | 2 | Tests for ui.navigation.NavigationController — targeting ≥ 80% coverage. | INFO | Other_NonASCII |
| 2338 | tests\ui\test_navigation.py | comment | 57 | # ── basic navigation ──────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2339 | tests\ui\test_navigation.py | comment | 79 | # ── lazy loading ──────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2340 | tests\ui\test_navigation.py | comment | 98 | # ── event bus ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2341 | tests\ui\test_navigation.py | comment | 132 | # ── session persistence ───────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2342 | tests\ui\test_navigation.py | comment | 145 | # No saved value — should return default | WARNING | Other_NonASCII |
| 2343 | tests\ui\test_navigation.py | comment | 149 | # ── registry delegation ───────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2344 | tests\ui\test_navigation.py | comment | 161 | # ── edge cases ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2345 | tools\hotfix_audit.py | other_non_ascii | 2 | hotfix_audit.py — v1.0.1 HOTFIX Post-GA Audit. | INFO | Other_NonASCII |
| 2346 | tools\hotfix_audit.py | comment | 40 | # ── Helpers ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2347 | tools\hotfix_audit.py | comment | 207 | # ── Main audit ─────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2348 | tools\hotfix_certify.py | other_non_ascii | 2 | hotfix_certify.py — v1.0.1 HOTFIX Certification. | INFO | Other_NonASCII |
| 2349 | tools\hotfix_cli_stability.py | other_non_ascii | 2 | hotfix_cli_stability.py — v1.0.1 HOTFIX CLI Stability Suite. | INFO | Other_NonASCII |
| 2350 | tools\hotfix_cli_stability.py | comment | 45 | # ── Runner ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2351 | tools\hotfix_cli_stability.py | comment | 105 | # ── Tests ──────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2352 | tools\hotfix_cli_stability.py | comment | 360 | # ── Main ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2353 | tools\hotfix_lua_hardening.py | other_non_ascii | 2 | hotfix_lua_hardening.py — v1.0.1 HOTFIX LUA Export Hardening Suite. | INFO | Other_NonASCII |
| 2354 | tools\hotfix_lua_hardening.py | comment | 38 | # ── Lua syntax helpers ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2355 | tools\hotfix_lua_hardening.py | comment | 150 | # ── Tests ──────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2356 | tools\hotfix_lua_hardening.py | comment | 456 | # ── Main ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2357 | tools\hotfix_otbm_hardening.py | other_non_ascii | 2 | hotfix_otbm_hardening.py — v1.0.1 HOTFIX OTBM Hardening Suite. | INFO | Other_NonASCII |
| 2358 | tools\hotfix_otbm_hardening.py | comment | 40 | # ── Helpers ────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2359 | tools\hotfix_otbm_hardening.py | comment | 67 | # ── Tests ──────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2360 | tools\hotfix_otbm_hardening.py | comment | 330 | # ── Main ───────────────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2361 | tools\hotfix_performance.py | other_non_ascii | 2 | hotfix_performance.py — v1.0.1 HOTFIX Memory & Performance Suite. | INFO | Other_NonASCII |
| 2362 | tools\hotfix_performance.py | comment | 45 | # ── Memory probing helpers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2363 | tools\hotfix_performance.py | comment | 101 | # ── Main suite ───────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2364 | tools\hotfix_regression.py | other_non_ascii | 2 | hotfix_regression.py — v1.0.1 HOTFIX Regression Validation. | INFO | Other_NonASCII |
| 2365 | tools\hotfix_security.py | other_non_ascii | 2 | hotfix_security.py — v1.0.1 HOTFIX Security Review. | INFO | Other_NonASCII |
| 2366 | tools\real_autonomous_certification.py | other_non_ascii | 2 | tools/real_autonomous_certification.py — Phase 6: Real Autonomous Certification. | INFO | Other_NonASCII |
| 2367 | tools\real_blueprint_validation.py | other_non_ascii | 2 | tools/real_blueprint_validation.py — Phase 8: Real Blueprint Validation. | INFO | Other_NonASCII |
| 2368 | tools\real_knowledge_validation.py | other_non_ascii | 2 | tools/real_knowledge_validation.py — Phase 7: Real Knowledge Validation. | INFO | Other_NonASCII |
| 2369 | tools\real_memory_profile.py | other_non_ascii | 2 | tools/real_memory_profile.py — Phase 9: Real Memory Profile. | INFO | Other_NonASCII |
| 2370 | tools\real_otbm_certification.py | other_non_ascii | 2 | tools/real_otbm_certification.py — Phase 5: Real OTBM Certification. | INFO | Other_NonASCII |
| 2371 | tools\real_performance_profile.py | other_non_ascii | 2 | tools/real_performance_profile.py — Phase 10: Real Performance Profile. | INFO | Other_NonASCII |
| 2372 | tools\real_world_stress.py | other_non_ascii | 2 | tools/real_world_stress.py — Phase 4: Real World Stress Test (FAST). | INFO | Other_NonASCII |
| 2373 | tools\run_rc1_1.py | other_non_ascii | 2 | tools/run_rc1_1.py — RC1.1 Master Certification Runner. | INFO | Other_NonASCII |
| 2374 | tools\validate_modules.py | other_non_ascii | 2 | tools/validate_modules.py — RC1.1 Module Discovery Validator (REAL). | INFO | Other_NonASCII |
| 2375 | ui\app.py | comment | 55 | # ── properties ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2376 | ui\app.py | comment | 77 | # ── public API ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2377 | ui\console.py | comment | 43 | # ── styling ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2378 | ui\console.py | comment | 60 | # ── colour helpers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2379 | ui\console.py | comment | 73 | # ── event handler ─────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2380 | ui\console.py | comment | 91 | # ── public helpers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2381 | ui\main_window.py | comment | 70 | # ── layout ────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2382 | ui\main_window.py | comment | 97 | # Workspace area — QStackedWidget managed by NavigationController | WARNING | Other_NonASCII |
| 2383 | ui\main_window.py | comment | 126 | # ── page registration (lazy loaded) ────────────────────────────────── | WARNING | Other_NonASCII |
| 2384 | ui\main_window.py | other_non_ascii | 131 | Pages are **not** instantiated here — they are created on first | INFO | Other_NonASCII |
| 2385 | ui\main_window.py | comment | 155 | # ── signal wiring ─────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2386 | ui\main_window.py | comment | 162 | # Sidebar → NavigationController | WARNING | Other_NonASCII |
| 2387 | ui\main_window.py | comment | 165 | # ── styling ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2388 | ui\main_window.py | comment | 181 | # ── session restore ───────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2389 | ui\main_window.py | comment | 194 | # ── slots ─────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2390 | ui\main_window.py | comment | 220 | # ── public properties ─────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2391 | ui\navigation.py | comment | 44 | # ── properties ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2392 | ui\navigation.py | comment | 59 | # ── page management ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2393 | ui\navigation.py | other_non_ascii | 64 | The factory is **not** called here — lazy creation happens on | INFO | Other_NonASCII |
| 2394 | ui\navigation.py | comment | 77 | return  # not registered — silently ignore | WARNING | Other_NonASCII |
| 2395 | ui\navigation.py | comment | 99 | # ── session persistence ────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2396 | ui\navigation.py | comment | 119 | # ── convenience ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2397 | ui\page_registry.py | comment | 30 | # ── registration ───────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2398 | ui\page_registry.py | comment | 48 | # ── retrieval ──────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2399 | ui\page_registry.py | comment | 63 | # ── inspection ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2400 | ui\page_registry.py | comment | 81 | # ── lifecycle ──────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2401 | ui\sidebar.py | comment | 53 | # ── layout ────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2402 | ui\sidebar.py | comment | 71 | # ── styling ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2403 | ui\statusbar.py | comment | 45 | # ── styling ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2404 | ui\statusbar.py | comment | 68 | # ── event handlers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2405 | ui\statusbar.py | comment | 86 | # ── public helpers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2406 | ui\theme.py | comment | 17 | # ── Base ──────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2407 | ui\theme.py | comment | 23 | # ── Title bar ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2408 | ui\theme.py | comment | 29 | # ── Sidebar ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2409 | ui\theme.py | comment | 35 | # ── Workspace ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2410 | ui\theme.py | comment | 40 | # ── Console ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2411 | ui\theme.py | comment | 48 | # ── Status bar ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2412 | ui\theme.py | comment | 52 | # ── Buttons ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2413 | ui\theme.py | comment | 57 | # ── Scrollbar ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2414 | ui\theme.py | comment | 61 | # ── Input ─────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2415 | ui\theme.py | comment | 78 | # ── properties ────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2416 | ui\theme.py | comment | 85 | # ── stylesheet generators ─────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2417 | ui\titlebar.py | comment | 57 | # ── layout ────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2418 | ui\titlebar.py | comment | 90 | # ── styling ───────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2419 | ui\titlebar.py | comment | 115 | # ── window dragging ───────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2420 | ui\titlebar.py | comment | 143 | # ── public helpers ────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2421 | ui\__init__.py | other_non_ascii | 2 | Agente RME Studio — New-Generation UI Foundation. | INFO | Other_NonASCII |
| 2422 | ui\__init__.py | other_non_ascii | 5 | Architecture follows: UI → Services → Adapters → Core. | INFO | Other_NonASCII |
| 2423 | ui\adapters\__init__.py | other_non_ascii | 7 | No core module is imported — implementations will be provided later. | INFO | Other_NonASCII |
| 2424 | ui\adapters\__init__.py | docstring | 29 | """Transforms WorldDTO ↔ core world representation.""" | WARNING | Other_NonASCII |
| 2425 | ui\adapters\__init__.py | docstring | 41 | """Transforms CriticDTO ↔ core critic results.""" | WARNING | Other_NonASCII |
| 2426 | ui\adapters\__init__.py | docstring | 53 | """Transforms KnowledgeDTO ↔ core knowledge records.""" | WARNING | Other_NonASCII |
| 2427 | ui\adapters\__init__.py | docstring | 65 | """Transforms CampaignDTO ↔ core campaign data.""" | WARNING | Other_NonASCII |
| 2428 | ui\plugins\__init__.py | other_non_ascii | 5 | No real plugins are registered yet — this is the infrastructure skeleton. | INFO | Other_NonASCII |
| 2429 | ui\plugins\__init__.py | comment | 44 | # ── discovery ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2430 | ui\plugins\__init__.py | comment | 83 | # ── lifecycle ─────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2431 | ui\plugins\__init__.py | comment | 115 | # ── query ─────────────────────────────────────────────────────────── | WARNING | Other_NonASCII |
| 2432 | ui\services\__init__.py | other_non_ascii | 4 | Architecture:  UI → Services → Adapters → Core | INFO | Other_NonASCII |
| 2433 | ui\services\__init__.py | docstring | 55 | """Query the knowledge store and return top‐k results.""" | WARNING | Other_NonASCII |
| 2434 | ui\services\__init__.py | docstring | 74 | """Return a numerical quality score (0.0 – 1.0).""" | WARNING | Other_NonASCII |
| 2435 | ui\widgets\recent_activity_widget.py | other_non_ascii | 2 | Recent activity widget – shows timestamps for the last export, critic run, knowledge build, and campaign. | INFO | Other_NonASCII |
| 2436 | ui\widgets\recent_activity_widget.py | other_non_ascii | 37 | and values are human‑readable timestamps (or ``"-"`` when unavailable). | INFO | Other_NonASCII |
| 2437 | ui\widgets\release_info_widget.py | other_non_ascii | 2 | Release info widget – shows the release name and version. | INFO | Other_NonASCII |
| 2438 | ui\widgets\system_status_widget.py | other_non_ascii | 2 | System status widget – displays static online status for UI components. | INFO | Other_NonASCII |
| 2439 | ui\widgets\system_status_widget.py | docstring | 35 | """Placeholder – kept for API symmetry; status is static.""" | WARNING | Other_NonASCII |
| 2440 | validators\asset_validator.py | other_non_ascii | 2 | Asset Validator — Verifica IDs de items contra el AssetRegistry. | INFO | Other_NonASCII |
| 2441 | validators\asset_validator.py | other_non_ascii | 4 | Usa AssetRegistry como fuente de verdad única. | INFO | Latin_Extended |
| 2442 | validators\monster_validator.py | other_non_ascii | 2 | Monster Validator — Verifica nombres de monstruos contra el AssetRegistry. | INFO | Other_NonASCII |
| 2443 | validators\monster_validator.py | other_non_ascii | 4 | Usa AssetRegistry como fuente de verdad única. | INFO | Latin_Extended |
| 2444 | validators\qa_pipeline.py | other_non_ascii | 14 | ↓ | INFO | Other_NonASCII |
| 2445 | validators\qa_pipeline.py | other_non_ascii | 16 | ↓ | INFO | Other_NonASCII |
| 2446 | validators\qa_pipeline.py | other_non_ascii | 18 | ↓ | INFO | Other_NonASCII |
| 2447 | validators\qa_pipeline.py | other_non_ascii | 20 | ↓ | INFO | Other_NonASCII |
| 2448 | validators\qa_pipeline.py | other_non_ascii | 22 | ↓ | INFO | Other_NonASCII |
| 2449 | validators\tile_validator.py | comment | 23 | # Pattern: map:getOrCreateTile(x, y, z) — allow negatives with optional minus | WARNING | Other_NonASCII |

## Migration Plan

### Phase 1 - Assessment (Current)
- [x] Full repository scan for non-English content
- [ ] Review all Critical findings
- [ ] Review all Warning findings

### Phase 2 - Critical Issues (API/Export Safety)
- [ ] Rename public identifiers with non-English names to English equivalents
- [ ] Update export schemas (JSON/YAML/TOML keys) that contain non-English text
- [ ] Update serialization keys to English
- [ ] Run full test suite after changes

### Phase 3 - Warning Issues (Internal Hygiene)
- [ ] Translate all non-English comments and docstrings to English
- [ ] Translate log messages and print statements to English
- [ ] Rename private identifiers with non-English names
- [ ] Run full test suite after changes

### Phase 4 - Info Issues (Documentation)
- [ ] Review documentation for non-English sections that should be translated
- [ ] Ensure all user-facing documentation is in English

### Phase 5 - Certification
- [ ] Re-run language audit
- [ ] Confirm zero non-English identifiers remain
- [ ] Certify HITO 26.3 - Safe Language Normalization

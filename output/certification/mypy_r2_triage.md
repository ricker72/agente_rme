# MyPy R2 Triage Report

**Baseline file:** `output\certification\mypy_r2_baseline.txt`
**Total errors:** 809
**Total notes:** 303
**Summary:** Found 809 errors in 221 files (checked 756 source files)

## Category Breakdown

| Category | Count | Description |
|----------|-------|-------------|
| missing_imports | 32 | Library stubs not installed or module not found |
| optional_none | 12 | Accessing attributes on Optional/None types |
| incompatible_assignment | 354 | Type mismatches in assignments, arguments, operators |
| return_type_mismatch | 28 | Incompatible return value types |
| untyped_function | 237 | Missing type annotations |
| any_leakage | 99 | Returning Any from typed functions |
| test_only | 47 | Errors in test files (lower priority) |
| generated_excluded | 0 | Errors in generated/output artifacts |

## Priority for Safe Fixes

1. **UI errors** (ui/ and tests/ui/) — target: 0 errors
2. **Critical core surface** (core/otbm, core/critic, core/knowledge, core/autonomous, core/blueprint_intelligence)
3. **Missing imports** (install stubs where possible)
4. **Untyped functions** (add annotations)
5. **Any leakage** (narrow types)
6. **Test-only errors** (add stubs for missing modules)

## test_only (47 errors)

### tests\agents\test_agent_registry.py

- `tests\agents\test_agent_registry.py:7: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_architect_agent.py

- `tests\agents\test_architect_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_architect_agent_coverage.py

- `tests\agents\test_architect_agent_coverage.py:21: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_balance_agent.py

- `tests\agents\test_balance_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_balance_agent_coverage.py

- `tests\agents\test_balance_agent_coverage.py:21: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_expansion_agent.py

- `tests\agents\test_expansion_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_expansion_agent_coverage.py

- `tests\agents\test_expansion_agent_coverage.py:20: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_export_agent.py

- `tests\agents\test_export_agent.py:8: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_mapper_agent.py

- `tests\agents\test_mapper_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_mapper_agent_coverage.py

- `tests\agents\test_mapper_agent_coverage.py:21: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_orchestrator_agent.py

- `tests\agents\test_orchestrator_agent.py:6: error: Module "core.agents" has no attribute "MultiAgentResult"  [attr-defined]`
- `tests\agents\test_orchestrator_agent.py:7: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_playtest_agent.py

- `tests\agents\test_playtest_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_qa_agent.py

- `tests\agents\test_qa_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_qa_agent_coverage.py

- `tests\agents\test_qa_agent_coverage.py:21: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_quest_agent.py

- `tests\agents\test_quest_agent.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\agents\test_quest_agent_coverage.py

- `tests\agents\test_quest_agent_coverage.py:22: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\campaign\test_campaign_export.py

- `tests\campaign\test_campaign_export.py:29: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\campaign\test_campaign_fallback.py

- `tests\campaign\test_campaign_fallback.py:28: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\campaign\test_campaign_pipeline.py

- `tests\campaign\test_campaign_pipeline.py:34: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\common\test_datetime_timezone.py

- `tests\common\test_datetime_timezone.py:24: error: Cannot find implementation or library stub for module named "core.agents.agent_result"  [import-not-found]`
- `tests\common\test_datetime_timezone.py:36: error: Cannot find implementation or library stub for module named "core.agents.contracts.agent_response"  [import-not-found]`
- `tests\common\test_datetime_timezone.py:43: error: Cannot find implementation or library stub for module named "core.agents.contracts.agent_task"  [import-not-found]`
- `tests\common\test_datetime_timezone.py:61: error: Cannot find implementation or library stub for module named "core.agents.contracts.workflow_state"  [import-not-found]`

### tests\common\test_timezone_compliance.py

- `tests\common\test_timezone_compliance.py:92: error: Cannot find implementation or library stub for module named "core.agents.agent_result"  [import-not-found]`
- `tests\common\test_timezone_compliance.py:99: error: Cannot find implementation or library stub for module named "core.agents.contracts.agent_response"  [import-not-found]`
- `tests\common\test_timezone_compliance.py:106: error: Cannot find implementation or library stub for module named "core.agents.contracts.agent_task"  [import-not-found]`
- `tests\common\test_timezone_compliance.py:118: error: Cannot find implementation or library stub for module named "core.agents.contracts.workflow_state"  [import-not-found]`

### tests\integration\test_agent_error_recovery.py

- `tests\integration\test_agent_error_recovery.py:6: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\integration\test_critic_e2e_pipeline.py

- `tests\integration\test_critic_e2e_pipeline.py:20: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\integration\test_knowledge_pipeline.py

- `tests\integration\test_knowledge_pipeline.py:32: error: "Collection[str]" has no attribute "append"  [attr-defined]`
- `tests\integration\test_knowledge_pipeline.py:41: error: "Collection[str]" has no attribute "append"  [attr-defined]`
- `tests\integration\test_knowledge_pipeline.py:49: error: "Collection[str]" has no attribute "append"  [attr-defined]`

### tests\integration\test_multi_agent_export.py

- `tests\integration\test_multi_agent_export.py:8: error: Cannot find implementation or library stub for module named "core.agents.contracts"  [import-not-found]`

### tests\integration\test_multi_agent_pipeline.py

- `tests\integration\test_multi_agent_pipeline.py:7: error: Module "core.agents" has no attribute "MultiAgentResult"  [attr-defined]`

### tests\lua\test_spawn_generation.py

- `tests\lua\test_spawn_generation.py:32: error: Incompatible default for parameter "monster" (default has type "None", parameter has type "str")  [assignment]`

### tests\test_autonomous_designer.py

- `tests\test_autonomous_designer.py:27: error: Cannot find implementation or library stub for module named "core.designer"  [import-not-found]`

### tests\test_blueprint_learner.py

- `tests\test_blueprint_learner.py:92: error: Need type annotation for "ground_counter" (hint: "ground_counter: dict[<type>, <type>] = ...")  [var-annotated]`

### tests\test_content_balancer.py

- `tests\test_content_balancer.py:13: error: Cannot find implementation or library stub for module named "core.designer"  [import-not-found]`

### tests\test_decision_engine.py

- `tests\test_decision_engine.py:13: error: Cannot find implementation or library stub for module named "core.designer"  [import-not-found]`

### tests\test_lua_exporter.py

- `tests\test_lua_exporter.py:198: error: Missing positional argument "tmp_path" in call to "test_lua_exporter_export_to_file"  [call-arg]`

### tests\test_visual_critic.py

- `tests\test_visual_critic.py:29: error: Incompatible types in assignment (expression has type "Tile | None", variable has type "Tile")  [assignment]`

### tests\ui\test_dashboard_page.py

- `tests\ui\test_dashboard_page.py:8: error: Module "PySide6.QtCore" has no attribute "QSignalSpy"  [attr-defined]`

### tests\ui\test_dashboard_provider.py

- `tests\ui\test_dashboard_provider.py:44: error: Incompatible types in "yield" (actual type "QCoreApplication", expected type "QApplication")  [misc]`

### tests\ui\test_service_container.py

- `tests\ui\test_service_container.py:53: error: Need type annotation for "result"  [var-annotated]`
- `tests\ui\test_service_container.py:64: error: Need type annotation for "r1"  [var-annotated]`
- `tests\ui\test_service_container.py:65: error: Need type annotation for "r2"  [var-annotated]`

## missing_imports (32 errors)

### ai\ollama_client.py

- `ai\ollama_client.py:4: error: Library stubs not installed for "requests"  [import-untyped]`
- `ai\ollama_client.py:7: error: Cannot find implementation or library stub for module named "ollama"  [import-not-found]`

### boss_generator.py

- `boss_generator.py:5: error: Cannot find implementation or library stub for module named "asset_registry"  [import-not-found]`
- `boss_generator.py:6: error: Cannot find implementation or library stub for module named "map_designer"  [import-not-found]`
- `boss_generator.py:7: error: Cannot find implementation or library stub for module named "world_model"  [import-not-found]`

### cli.py

- `cli.py:343: error: Library stubs not installed for "requests"  [import-untyped]`

### config_manager.py

- `config_manager.py:13: error: Library stubs not installed for "lxml"  [import-untyped]`

### core\agents\quest_agent.py

- `core\agents\quest_agent.py:16: error: Cannot find implementation or library stub for module named "core.campaign.quest_generator"  [import-not-found]`

### data_extractor.py

- `data_extractor.py:13: error: Library stubs not installed for "lxml"  [import-untyped]`

### hito26_1_benchmark.py

- `hito26_1_benchmark.py:33: error: Cannot find implementation or library stub for module named "agente_rme.core.agents"  [import-not-found]`

### installer\setup.py

- `installer\setup.py:139: error: Library stubs not installed for "requests"  [import-untyped]`

### main.py

- `main.py:15: error: Cannot find implementation or library stub for module named "customtkinter"  [import-not-found]`

### mission_generator.py

- `mission_generator.py:5: error: Cannot find implementation or library stub for module named "asset_registry"  [import-not-found]`
- `mission_generator.py:6: error: Cannot find implementation or library stub for module named "map_designer"  [import-not-found]`
- `mission_generator.py:7: error: Cannot find implementation or library stub for module named "world_model"  [import-not-found]`

### ollama_client.py

- `ollama_client.py:11: error: Cannot find implementation or library stub for module named "ollama"  [import-not-found]`
- `ollama_client.py:17: error: Library stubs not installed for "requests"  [import-untyped]`

### quest_generator.py

- `quest_generator.py:5: error: Cannot find implementation or library stub for module named "asset_registry"  [import-not-found]`
- `quest_generator.py:6: error: Cannot find implementation or library stub for module named "map_designer"  [import-not-found]`
- `quest_generator.py:7: error: Cannot find implementation or library stub for module named "world_model"  [import-not-found]`

### rag\embeddings.py

- `rag\embeddings.py:10: error: Cannot find implementation or library stub for module named "sentence_transformers"  [import-not-found]`

### raid_generator.py

- `raid_generator.py:5: error: Cannot find implementation or library stub for module named "asset_registry"  [import-not-found]`
- `raid_generator.py:6: error: Cannot find implementation or library stub for module named "map_designer"  [import-not-found]`
- `raid_generator.py:7: error: Cannot find implementation or library stub for module named "world_model"  [import-not-found]`

### reward_generator.py

- `reward_generator.py:5: error: Cannot find implementation or library stub for module named "asset_registry"  [import-not-found]`
- `reward_generator.py:6: error: Cannot find implementation or library stub for module named "map_designer"  [import-not-found]`
- `reward_generator.py:7: error: Cannot find implementation or library stub for module named "world_model"  [import-not-found]`

### test_orch_diag.py

- `test_orch_diag.py:7: error: Cannot find implementation or library stub for module named "agente_rme.core.agents.orchestrator_agent"  [import-not-found]`

### test_utcnow.py

- `test_utcnow.py:7: error: Cannot find implementation or library stub for module named "agente_rme.core.agents.agent_result"  [import-not-found]`
- `test_utcnow.py:13: error: Cannot find implementation or library stub for module named "agente_rme.core.agents.contracts.agent_response"  [import-not-found]`
- `test_utcnow.py:19: error: Cannot find implementation or library stub for module named "agente_rme.core.agents.contracts.agent_task"  [import-not-found]`
- `test_utcnow.py:25: error: Cannot find implementation or library stub for module named "agente_rme.core.agents.contracts.workflow_state"  [import-not-found]`

## optional_none (12 errors)

### core\analyzer\map_analyzer.py

- `core\analyzer\map_analyzer.py:140: error: Item "None" of "Any | None" has no attribute "import_file"  [union-attr]`

### core\assets\asset_classifier.py

- `core\assets\asset_classifier.py:284: error: Item "None" of "IndexedItem | None" has no attribute "category"  [union-attr]`
- `core\assets\asset_classifier.py:299: error: Item "None" of "IndexedItem | None" has no attribute "category"  [union-attr]`
- `core\assets\asset_classifier.py:350: error: Item "None" of "AssetIndexer | None" has no attribute "GROUND_KEYWORDS"  [union-attr]`
- `core\assets\asset_classifier.py:352: error: Item "None" of "AssetIndexer | None" has no attribute "WALL_KEYWORDS"  [union-attr]`
- `core\assets\asset_classifier.py:354: error: Item "None" of "AssetIndexer | None" has no attribute "MAGIC_KEYWORDS"  [union-attr]`
- `core\assets\asset_classifier.py:357: error: Item "None" of "AssetIndexer | None" has no attribute "LIBRARY_KEYWORDS"  [union-attr]`
- `core\assets\asset_classifier.py:360: error: Item "None" of "AssetIndexer | None" has no attribute "NATURE_KEYWORDS"  [union-attr]`

### core\planner\prompt_interpreter.py

- `core\planner\prompt_interpreter.py:48: error: Item "None" of "list[Any] | None" has no attribute "append"  [union-attr]`
- `core\planner\prompt_interpreter.py:50: error: Item "None" of "list[Any] | None" has no attribute "append"  [union-attr]`
- `core\planner\prompt_interpreter.py:52: error: Item "None" of "list[Any] | None" has no attribute "append"  [union-attr]`

### hito26_1_benchmark.py

- `hito26_1_benchmark.py:27: error: Item "TextIO" of "TextIO | Any" has no attribute "reconfigure"  [union-attr]`

## incompatible_assignment (354 errors)

### benchmark_autonomous.py

- `benchmark_autonomous.py:183: error: Generator has incompatible item type "int"; expected "bool"  [misc]`
- `benchmark_autonomous.py:183: error: Unsupported operand types for <= ("int" and "object")  [operator]`
- `benchmark_autonomous.py:201: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`

### core\agents\architect_agent.py

- `core\agents\architect_agent.py:42: error: No overload variant of "dict" matches argument type "WorldPlan"  [call-overload]`

### core\agents\playtest_agent.py

- `core\agents\playtest_agent.py:22: error: Missing positional argument "world" in call to "Pathfinder"  [call-arg]`

### core\agents\quest_agent.py

- `core\agents\quest_agent.py:21: error: Missing positional arguments "asset_registry", "map_designer", "world_model" in call to "QuestGenerator"  [call-arg]`

### core\analyzer\architecture_analyzer.py

- `core\analyzer\architecture_analyzer.py:139: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\analyzer\density_analyzer.py

- `core\analyzer\density_analyzer.py:154: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\density_analyzer.py:155: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\density_analyzer.py:194: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\density_analyzer.py:195: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\density_analyzer.py:232: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\density_analyzer.py:237: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[Any], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\analyzer\path_analyzer.py

- `core\analyzer\path_analyzer.py:68: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\path_analyzer.py:69: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\path_analyzer.py:75: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\path_analyzer.py:76: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\path_analyzer.py:81: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\path_analyzer.py:104: error: Argument "key" to "sort" of "list" has incompatible type "Callable[[dict[str, object]], object]"; expected "Callable[[dict[str, object]], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\analyzer\path_analyzer.py:143: error: Argument "key" to "sort" of "list" has incompatible type "Callable[[dict[str, object]], object]"; expected "Callable[[dict[str, object]], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\analyzer\path_analyzer.py:207: error: Generator has incompatible item type "object"; expected "bool"  [misc]`
- `core\analyzer\path_analyzer.py:217: error: Argument "key" to "max" has incompatible type "Callable[[dict[str, object]], object]"; expected "Callable[[dict[str, object]], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\analyzer\path_analyzer.py:227: error: Argument "key" to "min" has incompatible type "Callable[[dict[str, object]], object]"; expected "Callable[[dict[str, object]], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- ... and 4 more

### core\analyzer\spawn_analyzer.py

- `core\analyzer\spawn_analyzer.py:226: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\analyzer\spawn_analyzer.py:227: error: No overload variant of "int" matches argument type "object"  [call-overload]`

### core\analyzer\style_analyzer.py

- `core\analyzer\style_analyzer.py:22: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\architect\layout_engine.py

- `core\architect\layout_engine.py:90: error: Argument "priority" to "LayoutDecision" has incompatible type "str | int"; expected "int"  [arg-type]`

### core\architect\style_engine.py

- `core\architect\style_engine.py:36: error: Argument 1 to "StyleDNA" has incompatible type "**dict[str, str]"; expected "float"  [arg-type]`

### core\architecture\architecture_analyzer.py

- `core\architecture\architecture_analyzer.py:46: error: Argument 2 to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\architecture_analyzer.py:52: error: Argument 1 to "add_structure" of "ArchitectureGraph" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\architecture_analyzer.py:86: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\architecture_analyzer.py:87: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\architecture_analyzer.py:116: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\architecture_analyzer.py:117: error: No overload variant of "int" matches argument type "object"  [call-overload]`

### core\architecture\blueprint_generator.py

- `core\architecture\blueprint_generator.py:31: error: Argument 2 to "register_pattern" of "PatternLibrary" has incompatible type "dict[str, Collection[Collection[str]]]"; expected "dict[str, object]"  [arg-type]`
- `core\architecture\blueprint_generator.py:109: error: Argument 2 to "_default_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:110: error: Argument 3 to "_default_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:122: error: Argument 2 to "_default_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:123: error: Argument 3 to "_default_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:147: error: Argument 2 to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:148: error: Argument 3 to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:165: error: Argument 2 to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:166: error: Argument 3 to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\blueprint_generator.py:168: error: Argument "metadata" to "create_blueprint" of "BlueprintGenerator" has incompatible type "object"; expected "dict[str, object] | None"  [arg-type]`

### core\architecture\building_classifier.py

- `core\architecture\building_classifier.py:24: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\building_classifier.py:25: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\building_classifier.py:28: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`

### core\architecture\structure_extractor.py

- `core\architecture\structure_extractor.py:13: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\structure_extractor.py:14: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\structure_extractor.py:17: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `core\architecture\structure_extractor.py:21: error: No overload variant of "int" matches argument type "object"  [call-overload]`

### core\architecture\style_mixer.py

- `core\architecture\style_mixer.py:27: error: Argument 1 to "enumerate" has incompatible type "object"; expected "Iterable[Never]"  [arg-type]`
- `core\architecture\style_mixer.py:31: error: Argument 1 to "enumerate" has incompatible type "object"; expected "Iterable[Never]"  [arg-type]`
- `core\architecture\style_mixer.py:43: error: Argument 1 to "mix_styles" of "StyleMixer" has incompatible type "object"; expected "str"  [arg-type]`
- `core\architecture\style_mixer.py:43: error: Argument 2 to "mix_styles" of "StyleMixer" has incompatible type "object"; expected "str"  [arg-type]`

### core\assets\asset_classifier.py

- `core\assets\asset_classifier.py:289: error: Incompatible types in assignment (expression has type "set[Never]", variable has type "list[int]")  [assignment]`
- `core\assets\asset_classifier.py:295: error: Incompatible types in assignment (expression has type "set[int]", variable has type "list[int]")  [assignment]`

### core\assets\asset_recommender.py

- `core\assets\asset_recommender.py:231: error: Argument 1 to "get" of "dict" has incompatible type "str | None"; expected "str"  [arg-type]`

### core\autonomous\autonomous_director.py

- `core\autonomous\autonomous_director.py:295: error: Argument "target_size" to "RegionPlan" has incompatible type "float"; expected "int"  [arg-type]`

### core\balance\difficulty_analyzer.py

- `core\balance\difficulty_analyzer.py:190: error: Argument "damage_dealt_min" to "DifficultyProfile" has incompatible type "float"; expected "int"  [arg-type]`
- `core\balance\difficulty_analyzer.py:193: error: Argument "health_pool" to "DifficultyProfile" has incompatible type "float"; expected "int"  [arg-type]`

### core\balance\loot_balancer.py

- `core\balance\loot_balancer.py:333: error: Incompatible types in assignment (expression has type "Tile | None", variable has type "Tile")  [assignment]`

### core\balance\xp_analyzer.py

- `core\balance\xp_analyzer.py:224: error: Incompatible types in assignment (expression has type "float", variable has type "int")  [assignment]`
- `core\balance\xp_analyzer.py:226: error: Incompatible types in assignment (expression has type "float", variable has type "int")  [assignment]`

### core\balance\xp_balancer.py

- `core\balance\xp_balancer.py:244: error: Incompatible types in assignment (expression has type "Tile | None", variable has type "Tile")  [assignment]`

### core\blueprints\blueprint.py

- `core\blueprints\blueprint.py:157: error: Incompatible types in assignment (expression has type "list[str]", target has type "str")  [assignment]`
- `core\blueprints\blueprint.py:161: error: Incompatible types in assignment (expression has type "bool", target has type "str")  [assignment]`

### core\blueprints\blueprint_mixer.py

- `core\blueprints\blueprint_mixer.py:181: error: Argument 1 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`
- `core\blueprints\blueprint_mixer.py:181: error: Argument 2 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`
- `core\blueprints\blueprint_mixer.py:186: error: Argument 1 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`
- `core\blueprints\blueprint_mixer.py:186: error: Argument 2 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`
- `core\blueprints\blueprint_mixer.py:191: error: Argument 1 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`
- `core\blueprints\blueprint_mixer.py:191: error: Argument 2 to "_blend_list" of "BlueprintMixer" has incompatible type "Sequence[object]"; expected "list[Any]"  [arg-type]`

### core\blueprints\blueprint_registry.py

- `core\blueprints\blueprint_registry.py:167: error: Dict entry 1 has incompatible type "str": "dict[str, int]"; expected "str": "int"  [dict-item]`
- `core\blueprints\blueprint_registry.py:168: error: Dict entry 2 has incompatible type "str": "dict[str, int]"; expected "str": "int"  [dict-item]`

### core\blueprints\pattern_detector.py

- `core\blueprints\pattern_detector.py:588: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\blueprints\theme_classifier.py

- `core\blueprints\theme_classifier.py:212: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\campaign\faction_generator.py

- `core\campaign\faction_generator.py:39: error: Dict entry 0 has incompatible type "str": "list[dict[str, Sequence[str]]]"; expected "str": "dict[str, Any]"  [dict-item]`
- `core\campaign\faction_generator.py:65: error: Dict entry 1 has incompatible type "str": "list[dict[str, Sequence[str]]]"; expected "str": "dict[str, Any]"  [dict-item]`
- `core\campaign\faction_generator.py:83: error: Dict entry 2 has incompatible type "str": "list[dict[str, Sequence[str]]]"; expected "str": "dict[str, Any]"  [dict-item]`
- `core\campaign\faction_generator.py:101: error: Dict entry 3 has incompatible type "str": "list[dict[str, Sequence[str]]]"; expected "str": "dict[str, Any]"  [dict-item]`
- `core\campaign\faction_generator.py:151: error: Invalid index type "int" for "dict[str, Any]"; expected type "str"  [index]`

### core\campaign\lore_generator.py

- `core\campaign\lore_generator.py:38: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:44: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:50: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:59: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:66: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:74: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:81: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:90: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:97: error: Dict entry 3 has incompatible type "str": "int"; expected "str": "str"  [dict-item]`
- `core\campaign\lore_generator.py:103: error: Incompatible types in assignment (expression has type "list[str]", variable has type "dict[str, list[str]]")  [assignment]`
- ... and 2 more

### core\campaign\story_generator.py

- `core\campaign\story_generator.py:219: error: Argument "title" to "StoryArc" has incompatible type "object"; expected "str"  [arg-type]`
- `core\campaign\story_generator.py:221: error: Argument "description" to "StoryArc" has incompatible type "object"; expected "str"  [arg-type]`
- `core\campaign\story_generator.py:222: error: No overload variant of "list" matches argument type "object"  [call-overload]`
- `core\campaign\story_generator.py:223: error: Argument "boss_name" to "StoryArc" has incompatible type "object"; expected "str"  [arg-type]`
- `core\campaign\story_generator.py:224: error: Argument "reward_gold" to "StoryArc" has incompatible type "object"; expected "int"  [arg-type]`

### core\compiler\lua_emitter.py

- `core\compiler\lua_emitter.py:44: error: Argument 2 to "_collect" of "LuaMetrics" has incompatible type "dict[str, int]"; expected "dict[str, object]"  [arg-type]`
- `core\compiler\lua_emitter.py:53: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:54: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:58: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:60: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:61: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:63: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:65: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:66: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\compiler\lua_emitter.py:74: error: Unsupported operand types for + ("object" and "int")  [operator]`
- ... and 3 more

### core\compiler\lua_formatter.py

- `core\compiler\lua_formatter.py:68: error: Argument 1 to "_format_expression" of "LuaFormatter" has incompatible type "LuaStatement"; expected "LuaExpression"  [arg-type]`

### core\content\raid_generator.py

- `core\content\raid_generator.py:79: error: Argument "count" to "select_rewards" of "MapDesigner" has incompatible type "float"; expected "int"  [arg-type]`

### core\critic\analyzers\hunt_analyzer.py

- `core\critic\analyzers\hunt_analyzer.py:93: error: Incompatible types in assignment (expression has type "CriticScore", variable has type "float")  [assignment]`

### core\critic\analyzers\spawn_analyzer.py

- `core\critic\analyzers\spawn_analyzer.py:191: error: Incompatible types in assignment (expression has type "list[tuple[int, int]]", variable has type "list[int]")  [assignment]`
- `core\critic\analyzers\spawn_analyzer.py:197: error: Value of type "int" is not indexable  [index]`

### core\critic\critic_engine.py

- `core\critic\critic_engine.py:206: error: Incompatible types in assignment (expression has type "enumerate[Any]", variable has type "dict_items[Any, Any]")  [assignment]`

### core\critic\heatmap_renderer.py

- `core\critic\heatmap_renderer.py:170: error: Unsupported right operand type for in ("list[tuple[int, int, int]] | None")  [operator]`

### core\enterprise.py

- `core\enterprise.py:205: error: Unsupported left operand type for + ("object")  [operator]`
- `core\enterprise.py:215: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:216: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:219: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:220: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:223: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:224: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:227: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`
- `core\enterprise.py:228: error: Argument 1 to "Path" has incompatible type "object"; expected "str | PathLike[str]"  [arg-type]`

### core\evolution\map_evolver.py

- `core\evolution\map_evolver.py:336: error: Argument 2 to "write" of "OtbmWriter" has incompatible type "dict[str, Any]"; expected "str | Path"  [arg-type]`

### core\expansion\boss_expander.py

- `core\expansion\boss_expander.py:206: error: Argument "monster" to "Spawn" has incompatible type "object"; expected "str"  [arg-type]`

### core\factory\expansion_factory.py

- `core\factory\expansion_factory.py:46: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`
- `core\factory\expansion_factory.py:47: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`
- `core\factory\expansion_factory.py:48: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`
- `core\factory\expansion_factory.py:49: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`
- `core\factory\expansion_factory.py:50: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`
- `core\factory\expansion_factory.py:52: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`

### core\factory\season_generator.py

- `core\factory\season_generator.py:10: error: Argument 1 to "_design_seasonal_quests" of "SeasonGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\factory\season_generator.py:11: error: Argument 1 to "_design_seasonal_events" of "SeasonGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\factory\season_generator.py:12: error: Argument 1 to "_design_seasonal_rewards" of "SeasonGenerator" has incompatible type "object"; expected "str"  [arg-type]`
- `core\factory\season_generator.py:22: error: No overload variant of "list" matches argument type "object"  [call-overload]`
- `core\factory\season_generator.py:26: error: Argument 1 to "_build_seasonal_zones" of "SeasonGenerator" has incompatible type "object"; expected "str"  [arg-type]`

### core\factory\world_builder.py

- `core\factory\world_builder.py:25: error: Argument 1 to "build" of "WorldEngine" has incompatible type "dict[str, object]"; expected "WorldPlan"  [arg-type]`

### core\game_design\content_designer.py

- `core\game_design\content_designer.py:44: error: Argument 1 to "enumerate" has incompatible type "object"; expected "Iterable[Never]"  [arg-type]`
- `core\game_design\content_designer.py:60: error: Argument 1 to "enumerate" has incompatible type "object"; expected "Iterable[Never]"  [arg-type]`

### core\game_design\economy_designer.py

- `core\game_design\economy_designer.py:37: error: Value of type "object" is not indexable  [index]`

### core\game_design\lore_generator.py

- `core\game_design\lore_generator.py:12: error: Value of type "object" is not indexable  [index]`
- `core\game_design\lore_generator.py:15: error: Value of type "object" is not indexable  [index]`

### core\generators\city\city_to_worldmodel.py

- `core\generators\city\city_to_worldmodel.py:193: error: Argument "items" to "_add_tile" of "CityToWorldModel" has incompatible type "list[dict[str, int]]"; expected "list[int] | None"  [arg-type]`
- `core\generators\city\city_to_worldmodel.py:213: error: Argument "items" to "_add_tile" of "CityToWorldModel" has incompatible type "list[dict[str, int]]"; expected "list[int] | None"  [arg-type]`

### core\generators\dungeon\dungeon_generator.py

- `core\generators\dungeon\dungeon_generator.py:107: error: List item 0 has incompatible type "str"; expected "int"  [list-item]`
- `core\generators\dungeon\dungeon_generator.py:107: error: List item 1 has incompatible type "str"; expected "int"  [list-item]`
- `core\generators\dungeon\dungeon_generator.py:108: error: List item 0 has incompatible type "str"; expected "int"  [list-item]`
- `core\generators\dungeon\dungeon_generator.py:108: error: List item 1 has incompatible type "str"; expected "int"  [list-item]`
- `core\generators\dungeon\dungeon_generator.py:135: error: Argument "type" to "Shortcut" has incompatible type "object"; expected "str"  [arg-type]`
- `core\generators\dungeon\dungeon_generator.py:136: error: Argument "from_coord" to "Shortcut" has incompatible type "object"; expected "tuple[int, int]"  [arg-type]`
- `core\generators\dungeon\dungeon_generator.py:137: error: Argument "to_coord" to "Shortcut" has incompatible type "object"; expected "tuple[int, int]"  [arg-type]`
- `core\generators\dungeon\dungeon_generator.py:138: error: Argument "description" to "Shortcut" has incompatible type "object"; expected "str"  [arg-type]`

### core\knowledge\knowledge_index.py

- `core\knowledge\knowledge_index.py:61: error: Incompatible types in assignment (expression has type "BaseIndexer | None", variable has type "BaseIndexer")  [assignment]`

### core\knowledge\knowledge_query.py

- `core\knowledge\knowledge_query.py:144: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]`
- `core\knowledge\knowledge_query.py:183: error: Argument "difficulty" to "ParsedQuery" has incompatible type "int | None"; expected "str | None"  [arg-type]`

### core\learning\blueprint_catalog.py

- `core\learning\blueprint_catalog.py:293: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:303: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:313: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:323: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:334: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:345: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:374: error: List comprehension has incompatible type List[Blueprint | None]; expected List[Blueprint]  [misc]`
- `core\learning\blueprint_catalog.py:441: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\learning\blueprint_catalog.py:442: error: Value of type "object" is not indexable  [index]`
- `core\learning\blueprint_catalog.py:442: error: Unsupported target for indexed assignment ("object")  [index]`
- ... and 6 more

### core\learning\blueprint_learner.py

- `core\learning\blueprint_learner.py:204: error: Argument 1 to "append" of "list" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:214: error: Argument 1 to "_find_similar_blueprints" of "BlueprintLearner" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:230: error: Argument 1 to "add_blueprint" of "BlueprintCatalog" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:281: error: Argument 1 to "append" of "list" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:291: error: Argument 1 to "_find_similar_blueprints" of "BlueprintLearner" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:305: error: Argument 1 to "add_blueprint" of "BlueprintCatalog" has incompatible type "Blueprint | None"; expected "Blueprint"  [arg-type]`
- `core\learning\blueprint_learner.py:545: error: Incompatible default for parameter "pattern_type" (default has type "None", parameter has type "str")  [assignment]`

### core\learning\blueprint_ranker.py

- `core\learning\blueprint_ranker.py:101: error: Incompatible default for parameter "reference_patterns" (default has type "None", parameter has type "list[MinedPattern]")  [assignment]`
- `core\learning\blueprint_ranker.py:102: error: Incompatible default for parameter "similar_matches" (default has type "None", parameter has type "list[SimilarityResult]")  [assignment]`
- `core\learning\blueprint_ranker.py:241: error: Incompatible default for parameter "reference_patterns" (default has type "None", parameter has type "list[MinedPattern]")  [assignment]`
- `core\learning\blueprint_ranker.py:302: error: Unsupported right operand type for in ("object")  [operator]`
- `core\learning\blueprint_ranker.py:305: error: Value of type "object" is not indexable  [index]`
- `core\learning\blueprint_ranker.py:309: error: Unsupported right operand type for in ("object")  [operator]`
- `core\learning\blueprint_ranker.py:312: error: Value of type "object" is not indexable  [index]`
- `core\learning\blueprint_ranker.py:316: error: Unsupported right operand type for in ("object")  [operator]`
- `core\learning\blueprint_ranker.py:318: error: Value of type "object" is not indexable  [index]`
- `core\learning\blueprint_ranker.py:322: error: Unsupported right operand type for in ("object")  [operator]`
- ... and 1 more

### core\learning\dataset_builder.py

- `core\learning\dataset_builder.py:129: error: Incompatible default for parameter "maps_directory" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\dataset_builder.py:142: error: Incompatible default for parameter "directory" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\dataset_builder.py:332: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[Any], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\learning\dataset_builder.py:481: error: Incompatible default for parameter "output_path" (default has type "None", parameter has type "str")  [assignment]`

### core\learning\learning_pipeline.py

- `core\learning\learning_pipeline.py:104: error: Incompatible default for parameter "config" (default has type "None", parameter has type "LearningConfig")  [assignment]`
- `core\learning\learning_pipeline.py:141: error: Incompatible default for parameter "dataset" (default has type "None", parameter has type "dict[str, Any]")  [assignment]`
- `core\learning\learning_pipeline.py:162: error: Incompatible types in assignment (expression has type "dict[str, Any]", variable has type "None")  [assignment]`
- `core\learning\learning_pipeline.py:215: error: Incompatible types in assignment (expression has type "datetime", variable has type "None")  [assignment]`
- `core\learning\learning_pipeline.py:244: error: Generator has incompatible item type "int"; expected "bool"  [misc]`
- `core\learning\learning_pipeline.py:271: error: Incompatible default for parameter "style" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\learning_pipeline.py:271: error: Incompatible default for parameter "region_type" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\learning_pipeline.py:271: error: Incompatible default for parameter "count" (default has type "None", parameter has type "int")  [assignment]`
- `core\learning\learning_pipeline.py:321: error: Incompatible default for parameter "region_type" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\learning_pipeline.py:629: error: Incompatible default for parameter "new_maps_directory" (default has type "None", parameter has type "str")  [assignment]`
- ... and 4 more

### core\learning\map_embedding.py

- `core\learning\map_embedding.py:62: error: Incompatible default for parameter "dimensions" (default has type "None", parameter has type "int")  [assignment]`
- `core\learning\map_embedding.py:62: error: Incompatible default for parameter "model_path" (default has type "None", parameter has type "str")  [assignment]`

### core\learning\pattern_encoder.py

- `core\learning\pattern_encoder.py:77: error: Incompatible default for parameter "pattern_types" (default has type "None", parameter has type "list[str]")  [assignment]`
- `core\learning\pattern_encoder.py:230: error: Argument 1 to "append" of "list" has incompatible type "float"; expected "int"  [arg-type]`
- `core\learning\pattern_encoder.py:240: error: Argument 1 to "_bfs_shortest_path" of "PatternEncoder" has incompatible type "defaultdict[Any | None, set[Any | None]]"; expected "dict[str, set[str]]"  [arg-type]`
- `core\learning\pattern_encoder.py:256: error: Dict entry 0 has incompatible type "str": "floating[Any] | int"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_encoder.py:257: error: Dict entry 1 has incompatible type "str": "floating[Any] | int"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_encoder.py:258: error: Dict entry 2 has incompatible type "str": "floating[Any] | int"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_encoder.py:389: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\learning\pattern_encoder.py:477: error: Incompatible default for parameter "dataset" (default has type "None", parameter has type "dict[str, Any]")  [assignment]`
- `core\learning\pattern_encoder.py:614: error: Incompatible default for parameter "pattern_type" (default has type "None", parameter has type "str")  [assignment]`

### core\learning\pattern_miner.py

- `core\learning\pattern_miner.py:541: error: Dict entry 0 has incompatible type "str": "floating[Any] | float"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_miner.py:542: error: Dict entry 1 has incompatible type "str": "floating[Any] | float"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_miner.py:543: error: Dict entry 2 has incompatible type "str": "floating[Any] | float"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_miner.py:544: error: Dict entry 3 has incompatible type "str": "floating[Any] | float"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_miner.py:545: error: Dict entry 4 has incompatible type "str": "floating[Any] | float"; expected "str": "float"  [dict-item]`
- `core\learning\pattern_miner.py:590: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\learning\pattern_miner.py:648: error: No overload variant of "update" of "MutableMapping" matches argument type "object"  [call-overload]`
- `core\learning\pattern_miner.py:673: error: Incompatible default for parameter "pattern_type" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\pattern_miner.py:699: error: Unsupported target for indexed assignment ("object")  [index]`

### core\learning\similarity_engine.py

- `core\learning\similarity_engine.py:61: error: Incompatible default for parameter "index_path" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\similarity_engine.py:79: error: Incompatible default for parameter "region_data" (default has type "None", parameter has type "dict[str, dict[str, Any]]")  [assignment]`
- `core\learning\similarity_engine.py:502: error: Incompatible default for parameter "output_path" (default has type "None", parameter has type "str")  [assignment]`
- `core\learning\similarity_engine.py:528: error: Incompatible default for parameter "input_path" (default has type "None", parameter has type "str")  [assignment]`

### core\learning\style_encoder.py

- `core\learning\style_encoder.py:156: error: Incompatible default for parameter "styles" (default has type "None", parameter has type "list[str]")  [assignment]`
- `core\learning\style_encoder.py:230: error: Dict entry 1 has incompatible type "str": "dict[Never, Never]"; expected "str": "float"  [dict-item]`
- `core\learning\style_encoder.py:246: error: Dict entry 1 has incompatible type "str": "dict[Any, Any]"; expected "str": "float"  [dict-item]`
- `core\learning\style_encoder.py:321: error: Incompatible default for parameter "dataset" (default has type "None", parameter has type "dict[str, Any]")  [assignment]`
- `core\learning\style_encoder.py:425: error: Argument "avg_room_size" to "StyleProfile" has incompatible type "floating[Any] | int"; expected "float"  [arg-type]`
- `core\learning\style_encoder.py:426: error: Argument "avg_corridor_length" to "StyleProfile" has incompatible type "floating[Any] | int"; expected "float"  [arg-type]`
- `core\learning\style_encoder.py:428: error: Argument "connectivity_ratio" to "StyleProfile" has incompatible type "floating[Any] | int"; expected "float"  [arg-type]`
- `core\learning\style_encoder.py:432: error: Argument "decoration_density" to "StyleProfile" has incompatible type "floating[Any] | int"; expected "float"  [arg-type]`
- `core\learning\style_encoder.py:436: error: Argument "dominant_colors" to "StyleProfile" has incompatible type "Sequence[Sequence[object]]"; expected "list[tuple[int, int, int]]"  [arg-type]`
- `core\learning\style_encoder.py:438: error: Argument "style_variance" to "StyleProfile" has incompatible type "floating[Any] | int"; expected "float"  [arg-type]`
- ... and 3 more

### core\observability\health.py

- `core\observability\health.py:178: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`

### core\otbm\item_encoder.py

- `core\otbm\item_encoder.py:97: error: Argument 1 to "int" has incompatible type "Any | None"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"  [arg-type]`

### core\otbm\otbm_exporter.py

- `core\otbm\otbm_exporter.py:126: error: Incompatible types in assignment (expression has type "dict[str, Path]", variable has type "dict[str, str]")  [assignment]`

### core\otbm\otbm_serializer.py

- `core\otbm\otbm_serializer.py:372: error: Incompatible types in assignment (expression has type "tuple[Any, Any]", target has type "list[Any]")  [assignment]`

### core\otbm\spawn_encoder.py

- `core\otbm\spawn_encoder.py:131: error: Argument 1 to "int" has incompatible type "Any | None"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"  [arg-type]`
- `core\otbm\spawn_encoder.py:138: error: Argument 1 to "int" has incompatible type "Any | None"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"  [arg-type]`

### core\pipeline\full_pipeline.py

- `core\pipeline\full_pipeline.py:186: error: Incompatible types in assignment (expression has type "Tile | None", variable has type "Tile")  [assignment]`

### core\planner\planner.py

- `core\planner\planner.py:47: error: Argument 1 to "plan" of "DifficultyPlanner" has incompatible type "object"; expected "tuple[int, int] | None"  [arg-type]`
- `core\planner\planner.py:48: error: Argument 1 to "place_biome" of "BiomePlanner" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:64: error: Argument "name" to "CityPlan" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:65: error: Argument "theme" to "CityPlan" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:66: error: Argument "population" to "CityPlan" has incompatible type "object"; expected "int"  [arg-type]`
- `core\planner\planner.py:67: error: Argument "districts" to "CityPlan" has incompatible type "object"; expected "list[dict[str, object]]"  [arg-type]`
- `core\planner\planner.py:73: error: Argument "name" to "ZonePlan" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:87: error: Argument "theme" to "DungeonPlan" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:127: error: Argument 2 to "_build_zone" of "AIPlanner" has incompatible type "object"; expected "str"  [arg-type]`
- `core\planner\planner.py:140: error: Argument 2 to "_build_zone" of "AIPlanner" has incompatible type "object"; expected "str"  [arg-type]`
- ... and 1 more

### core\planner\prompt_interpreter.py

- `core\planner\prompt_interpreter.py:30: error: Incompatible types in assignment (expression has type "str", target has type "list[Any] | None")  [assignment]`
- `core\planner\prompt_interpreter.py:32: error: Incompatible types in assignment (expression has type "str", target has type "list[Any] | None")  [assignment]`
- `core\planner\prompt_interpreter.py:37: error: Incompatible types in assignment (expression has type "str", target has type "list[Any] | None")  [assignment]`
- `core\planner\prompt_interpreter.py:42: error: Incompatible types in assignment (expression has type "tuple[int, int]", target has type "list[Any] | None")  [assignment]`
- `core\planner\prompt_interpreter.py:55: error: Incompatible types in assignment (expression has type "str", target has type "list[Any] | None")  [assignment]`
- `core\planner\prompt_interpreter.py:57: error: Incompatible types in assignment (expression has type "str", target has type "list[Any] | None")  [assignment]`

### core\planner\world_validator.py

- `core\planner\world_validator.py:20: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`

### core\planner\zone_plan.py

- `core\planner\zone_plan.py:17: error: Incompatible types in assignment (expression has type "None", variable has type "list[str]")  [assignment]`

### core\playtest\loot_simulator.py

- `core\playtest\loot_simulator.py:67: error: List item 3 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:70: error: List item 0 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:94: error: List item 2 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:95: error: List item 3 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:100: error: List item 1 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:101: error: List item 2 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:183: error: List item 2 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:184: error: List item 3 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:188: error: List item 1 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- `core\playtest\loot_simulator.py:197: error: List item 1 has incompatible type "tuple[str, float, int]"; expected "tuple[str, int, float]"  [list-item]`
- ... and 4 more

### core\playtest\playtest_engine.py

- `core\playtest\playtest_engine.py:445: error: Argument "attack" to "MonsterStats" has incompatible type "float"; expected "int"  [arg-type]`
- `core\playtest\playtest_engine.py:446: error: Argument "defense" to "MonsterStats" has incompatible type "float"; expected "int"  [arg-type]`
- `core\playtest\playtest_engine.py:447: error: Argument "magic_defense" to "MonsterStats" has incompatible type "float"; expected "int"  [arg-type]`

### core\playtest\survival_analyzer.py

- `core\playtest\survival_analyzer.py:185: error: Argument "key" to "min" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\playtest\survival_analyzer.py:186: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`
- `core\playtest\survival_analyzer.py:241: error: Argument "key" to "max" has incompatible type overloaded function; expected "Callable[[str], SupportsDunderLT[Any] | SupportsDunderGT[Any]]"  [arg-type]`

### core\preview\heatmap_renderer.py

- `core\preview\heatmap_renderer.py:69: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\preview\heatmap_renderer.py:69: error: Unsupported operand types for // ("object" and "int")  [operator]`

### core\studio.py

- `core\studio.py:81: error: Argument 1 to "build" of "WorldEngine" has incompatible type "object"; expected "WorldPlan"  [arg-type]`

### core\world\blueprint_placer_adapter.py

- `core\world\blueprint_placer_adapter.py:188: error: Incompatible types in assignment (expression has type "Tile | None", variable has type "Tile")  [assignment]`

### core\world_brain\decision_engine.py

- `core\world_brain\decision_engine.py:189: error: Argument 2 to "_find_optimal_position" of "DecisionEngine" has incompatible type "object"; expected "dict[str, Any]"  [arg-type]`

### core\world_brain\goal_engine.py

- `core\world_brain\goal_engine.py:156: error: Argument "description" to "WorldGoal" has incompatible type "Collection[str]"; expected "str"  [arg-type]`
- `core\world_brain\goal_engine.py:157: error: Argument 1 to "dict" has incompatible type "Collection[str]"; expected "Iterable[tuple[str, int]]"  [arg-type]`
- `core\world_brain\goal_engine.py:158: error: Argument 1 to "dict" has incompatible type "Collection[str]"; expected "Iterable[tuple[str, Any]]"  [arg-type]`

### core\world_engine\boss_builder.py

- `core\world_engine\boss_builder.py:21: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `core\world_engine\boss_builder.py:22: error: Unsupported operand types for + ("object" and "int")  [operator]`

### core\world_engine\spawn_builder.py

- `core\world_engine\spawn_builder.py:20: error: Argument 1 to "place_biome" of "BiomePlanner" has incompatible type "object"; expected "str"  [arg-type]`
- `core\world_engine\spawn_builder.py:22: error: Argument 1 to "_pick_monster" of "SpawnBuilder" has incompatible type "object"; expected "str"  [arg-type]`
- `core\world_engine\spawn_builder.py:22: error: Argument 2 to "_pick_monster" of "SpawnBuilder" has incompatible type "object"; expected "str"  [arg-type]`

### core\world_engine\world_builder.py

- `core\world_engine\world_builder.py:54: error: Value of type "object" is not indexable  [index]`
- `core\world_engine\world_builder.py:99: error: Missing positional argument "height" in call to "validate" of "CollisionEngine"  [call-arg]`
- `core\world_engine\world_builder.py:107: error: Missing positional argument "height" in call to "validate" of "CollisionEngine"  [call-arg]`

### data_extractor.py

- `data_extractor.py:127: error: Unsupported target for indexed assignment ("object")  [index]`
- `data_extractor.py:131: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `data_extractor.py:162: error: Unsupported target for indexed assignment ("object")  [index]`
- `data_extractor.py:166: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `data_extractor.py:290: error: Argument 1 to "_parse_xml_file" has incompatible type "Path"; expected "str"  [arg-type]`
- `data_extractor.py:299: error: Argument 1 to "_parse_xml_file" has incompatible type "Path"; expected "str"  [arg-type]`
- `data_extractor.py:311: error: Argument 1 to "_parse_xml_file" has incompatible type "Path"; expected "str"  [arg-type]`
- `data_extractor.py:320: error: Argument 1 to "_parse_xml_file" has incompatible type "Path"; expected "str"  [arg-type]`

### examples\analyze_ciudades.py

- `examples\analyze_ciudades.py:17: error: Incompatible types in assignment (expression has type "dict[str, object]", variable has type "MapAnalysis")  [assignment]`
- `examples\analyze_ciudades.py:46: error: Argument 1 to "build_from_analysis" of "DatasetBuilder" has incompatible type "MapAnalysis"; expected "dict[str, object]"  [arg-type]`

### examples\enterprise_demo.py

- `examples\enterprise_demo.py:22: error: Argument 1 to "len" has incompatible type "object"; expected "Sized"  [arg-type]`

### examples\otbm_demo.py

- `examples\otbm_demo.py:14: error: Argument 1 to "build" of "WorldEngine" has incompatible type "dict[str, object]"; expected "WorldPlan"  [arg-type]`

### examples\plan_expansion.py

- `examples\plan_expansion.py:22: error: Argument 1 to "build" of "WorldEngine" has incompatible type "object"; expected "WorldPlan"  [arg-type]`

### ga_benchmark.py

- `ga_benchmark.py:63: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`

### hito26_1_benchmark.py

- `hito26_1_benchmark.py:210: error: Incompatible types in assignment (expression has type "TextIOWrapper[_WrappedBuffer]", variable has type "str")  [assignment]`
- `hito26_1_benchmark.py:211: error: Argument 2 to "dump" has incompatible type "str"; expected "SupportsWrite[str]"  [arg-type]`
- `hito26_1_benchmark.py:218: error: Value of type "Collection[Collection[Any]]" is not indexable  [index]`

### tools\hotfix_lua_hardening.py

- `tools\hotfix_lua_hardening.py:196: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`
- `tools\hotfix_lua_hardening.py:241: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`
- `tools\hotfix_lua_hardening.py:291: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`
- `tools\hotfix_lua_hardening.py:340: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`
- `tools\hotfix_lua_hardening.py:383: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`
- `tools\hotfix_lua_hardening.py:429: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`

### tools\hotfix_otbm_hardening.py

- `tools\hotfix_otbm_hardening.py:49: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`

### tools\hotfix_performance.py

- `tools\hotfix_performance.py:153: error: Argument 1 to "generate" of "WorldGenerator" has incompatible type "dict[str, object]"; expected "WorldModel | None"  [arg-type]`

### tools\real_blueprint_validation.py

- `tools\real_blueprint_validation.py:105: error: Argument 1 to "generate" of "BlueprintGenerator" has incompatible type "dict[str, str]"; expected "str"  [arg-type]`

### tools\real_knowledge_validation.py

- `tools\real_knowledge_validation.py:76: error: Argument 1 to "query_structured" of "KnowledgeEngine" has incompatible type "str"; expected "EntryType"  [arg-type]`
- `tools\real_knowledge_validation.py:83: error: "KnowledgeQuery" not callable  [operator]`

### tools\real_memory_profile.py

- `tools\real_memory_profile.py:44: error: No overload variant of "dict" matches argument type "WorldPlan"  [call-overload]`

### tools\real_world_stress.py

- `tools\real_world_stress.py:74: error: No overload variant of "dict" matches argument type "WorldPlan"  [call-overload]`

### tools\validate_modules.py

- `tools\validate_modules.py:165: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `tools\validate_modules.py:168: error: Unsupported operand types for + ("object" and "int")  [operator]`
- `tools\validate_modules.py:179: error: Unsupported operand types for < ("int" and "object")  [operator]`

### ui\console.py

- `ui\console.py:41: error: Argument 2 to "register" of "EventBus" has incompatible type "Callable[[ConsoleMessageEvent], None]"; expected "Callable[[BaseEvent], None]"  [arg-type]`

### ui\statusbar.py

- `ui\statusbar.py:42: error: Argument 2 to "register" of "EventBus" has incompatible type "Callable[[StatusMessageEvent], None]"; expected "Callable[[BaseEvent], None]"  [arg-type]`
- `ui\statusbar.py:43: error: Argument 2 to "register" of "EventBus" has incompatible type "Callable[[ServiceStateChangedEvent], None]"; expected "Callable[[BaseEvent], None]"  [arg-type]`

### ui\titlebar.py

- `ui\titlebar.py:122: error: Incompatible types in assignment (expression has type "QPoint", variable has type "None")  [assignment]`

### validators\asset_validator.py

- `validators\asset_validator.py:12: error: Incompatible types in assignment (expression has type "None", variable has type "AssetRegistry")  [assignment]`

### validators\monster_validator.py

- `validators\monster_validator.py:12: error: Incompatible types in assignment (expression has type "None", variable has type "AssetRegistry")  [assignment]`

## return_type_mismatch (28 errors)

### core\analyzer\path_analyzer.py

- `core\analyzer\path_analyzer.py:104: error: Incompatible return value type (got "object", expected "SupportsDunderLT[Any] | SupportsDunderGT[Any]")  [return-value]`
- `core\analyzer\path_analyzer.py:143: error: Incompatible return value type (got "object", expected "SupportsDunderLT[Any] | SupportsDunderGT[Any]")  [return-value]`
- `core\analyzer\path_analyzer.py:217: error: Incompatible return value type (got "object", expected "SupportsDunderLT[Any] | SupportsDunderGT[Any]")  [return-value]`
- `core\analyzer\path_analyzer.py:227: error: Incompatible return value type (got "object", expected "SupportsDunderLT[Any] | SupportsDunderGT[Any]")  [return-value]`

### core\architecture\architecture_graph.py

- `core\architecture\architecture_graph.py:23: error: Incompatible return value type (got "dict[str, list[str]]", expected "dict[str, object]")  [return-value]`
- `core\architecture\architecture_graph.py:34: error: Incompatible return value type (got "dict[str, dict[str, list[str]]]", expected "dict[str, object]")  [return-value]`

### core\architecture\blueprint_generator.py

- `core\architecture\blueprint_generator.py:36: error: Incompatible return value type (got "dict[str, Collection[Collection[str]]]", expected "dict[str, object]")  [return-value]`

### core\balance\difficulty_analyzer.py

- `core\balance\difficulty_analyzer.py:472: error: Incompatible return value type (got "dict[str, int]", expected "dict[str, float]")  [return-value]`
- `core\balance\difficulty_analyzer.py:473: error: Incompatible return value type (got "dict[str, int]", expected "dict[str, float]")  [return-value]`

### core\compiler\lua_ast.py

- `core\compiler\lua_ast.py:69: error: Incompatible return value type (got "list[LuaExpression]", expected "list[LuaNode]")  [return-value]`

### core\compiler\lua_emitter.py

- `core\compiler\lua_emitter.py:45: error: Incompatible return value type (got "dict[str, int]", expected "dict[str, object]")  [return-value]`

### core\evolution\improvement_engine.py

- `core\evolution\improvement_engine.py:185: error: "add" of "set" does not return a value (it only ever returns None)  [func-returns-value]`

### core\generators\city\city_generator.py

- `core\generators\city\city_generator.py:100: error: Returning Any from function declared to return "dict[str, list[int]]"  [no-any-return]`

### core\generators\city\harbor_generator.py

- `core\generators\city\harbor_generator.py:31: error: Incompatible return value type (got "list[dict[str, int]]", expected "list[dict[str, object]]")  [return-value]`

### core\generators\dungeon\dungeon_generator.py

- `core\generators\dungeon\dungeon_generator.py:100: error: Returning Any from function declared to return "dict[str, list[int]]"  [no-any-return]`

### core\knowledge\knowledge_base.py

- `core\knowledge\knowledge_base.py:156: error: Incompatible return value type (got "dict[str, Collection[str]]", expected "dict[str, object]")  [return-value]`

### core\learning\blueprint_ranker.py

- `core\learning\blueprint_ranker.py:372: error: Incompatible return value type (got "floating[Any] | float", expected "float")  [return-value]`

### core\learning\map_embedding.py

- `core\learning\map_embedding.py:419: error: Incompatible return value type (got "int", expected "str")  [return-value]`

### core\learning\pattern_miner.py

- `core\learning\pattern_miner.py:578: error: Incompatible return value type (got "floating[Any] | float", expected "float")  [return-value]`

### core\learning\similarity_engine.py

- `core\learning\similarity_engine.py:195: error: Incompatible return value type (got "floating[Any] | float", expected "float")  [return-value]`

### core\planner\prompt_interpreter.py

- `core\planner\prompt_interpreter.py:59: error: Incompatible return value type (got "dict[str, list[Any] | None]", expected "dict[str, object]")  [return-value]`

### core\preview\heatmap_renderer.py

- `core\preview\heatmap_renderer.py:68: error: Incompatible return value type (got "None", expected "tuple[int, int]")  [return-value]`

### core\world\blueprint_placer_adapter.py

- `core\world\blueprint_placer_adapter.py:100: error: Return type "int" of "_place_tile_based" incompatible with return type "None" in supertype "core.blueprints.blueprint_placer.BlueprintPlacer"  [override]`
- `core\world\blueprint_placer_adapter.py:148: error: Return type "int" of "_place_descriptive" incompatible with return type "None" in supertype "core.blueprints.blueprint_placer.BlueprintPlacer"  [override]`

### pipeline_runner.py

- `pipeline_runner.py:431: error: Incompatible return value type (got "Path", expected "str | None")  [return-value]`
- `pipeline_runner.py:547: error: Incompatible return value type (got "Path", expected "str | None")  [return-value]`
- `pipeline_runner.py:788: error: Incompatible return value type (got "Path", expected "str | None")  [return-value]`

### ui\navigation.py

- `ui\navigation.py:113: error: Incompatible return value type (got "object", expected "str")  [return-value]`

## untyped_function (237 errors)

### _write_file.py

- `_write_file.py:4: error: Need type annotation for "b64" (hint: "b64: list[<type>] = ...")  [var-annotated]`

### assets\items_loader.py

- `assets\items_loader.py:7: error: Need type annotation for "items_catalog" (hint: "items_catalog: dict[<type>, <type>] = ...")  [var-annotated]`
- `assets\items_loader.py:8: error: Need type annotation for "documents" (hint: "documents: list[<type>] = ...")  [var-annotated]`

### boss_generator.py

- `boss_generator.py:4: error: Module "boss_generator" has no attribute "BossGenerator"; maybe "TestBossGenerator"?  [attr-defined]`

### core\analyzer\architecture_analyzer.py

- `core\analyzer\architecture_analyzer.py:127: error: Need type annotation for "categories"  [var-annotated]`
- `core\analyzer\architecture_analyzer.py:275: error: "object" has no attribute "lower"  [attr-defined]`

### core\analyzer\city_analyzer.py

- `core\analyzer\city_analyzer.py:9: error: Need type annotation for "district_types"  [var-annotated]`

### core\analyzer\density_analyzer.py

- `core\analyzer\density_analyzer.py:191: error: Need type annotation for "grid"  [var-annotated]`
- `core\analyzer\density_analyzer.py:230: error: Need type annotation for "floor_counts"  [var-annotated]`

### core\analyzer\map_analyzer.py

- `core\analyzer\map_analyzer.py:246: error: Need type annotation for "tile_counter"  [var-annotated]`
- `core\analyzer\map_analyzer.py:247: error: Need type annotation for "item_counter"  [var-annotated]`
- `core\analyzer\map_analyzer.py:290: error: Need type annotation for "item_counter"  [var-annotated]`
- `core\analyzer\map_analyzer.py:372: error: Need type annotation for "counts"  [var-annotated]`
- `core\analyzer\map_analyzer.py:396: error: Need type annotation for "counts"  [var-annotated]`

### core\analyzer\spawn_analyzer.py

- `core\analyzer\spawn_analyzer.py:182: error: Need type annotation for "counts"  [var-annotated]`
- `core\analyzer\spawn_analyzer.py:220: error: Need type annotation for "monster_counts"  [var-annotated]`

### core\analyzer\tile_analyzer.py

- `core\analyzer\tile_analyzer.py:16: error: Need type annotation for "counts"  [var-annotated]`
- `core\analyzer\tile_analyzer.py:26: error: Need type annotation for "counts"  [var-annotated]`
- `core\analyzer\tile_analyzer.py:33: error: Need type annotation for "counts"  [var-annotated]`

### core\architecture\architecture_analyzer.py

- `core\architecture\architecture_analyzer.py:45: error: "object" has no attribute "lower"  [attr-defined]`
- `core\architecture\architecture_analyzer.py:95: error: "object" has no attribute "lower"  [attr-defined]`

### core\architecture\blueprint_generator.py

- `core\architecture\blueprint_generator.py:105: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:106: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:118: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:119: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:132: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:133: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:143: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\architecture\blueprint_generator.py:155: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\blueprint_generator.py:161: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`

### core\architecture\building_classifier.py

- `core\architecture\building_classifier.py:30: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\building_classifier.py:31: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\architecture\building_classifier.py:34: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\architecture\building_classifier.py:38: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\architecture\building_classifier.py:42: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`

### core\architecture\style_mixer.py

- `core\architecture\style_mixer.py:27: error: Need type annotation for "tile"  [var-annotated]`
- `core\architecture\style_mixer.py:49: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\style_mixer.py:50: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\style_mixer.py:53: error: "object" has no attribute "get"  [attr-defined]`
- `core\architecture\style_mixer.py:54: error: "object" has no attribute "get"  [attr-defined]`

### core\assets\asset_classifier.py

- `core\assets\asset_classifier.py:292: error: "list[int]" has no attribute "update"  [attr-defined]`

### core\assets\asset_indexer.py

- `core\assets\asset_indexer.py:565: error: Need type annotation for "cats" (hint: "cats: dict[<type>, <type>] = ...")  [var-annotated]`

### core\assets\item_indexer.py

- `core\assets\item_indexer.py:100: error: "object" has no attribute "lower"  [attr-defined]`

### core\autonomous\autonomous_planner.py

- `core\autonomous\autonomous_planner.py:101: error: Need type annotation for "region_counts" (hint: "region_counts: dict[<type>, <type>] = ...")  [var-annotated]`

### core\blueprints\blueprint_extractor.py

- `core\blueprints\blueprint_extractor.py:471: error: Need type annotation for "tile_counter"  [var-annotated]`
- `core\blueprints\blueprint_extractor.py:472: error: Need type annotation for "item_counter"  [var-annotated]`

### core\blueprints\pattern_detector.py

- `core\blueprints\pattern_detector.py:673: error: "dict[str, int]" has no attribute "most_common"  [attr-defined]`

### core\campaign\lore_generator.py

- `core\campaign\lore_generator.py:165: error: Invalid index type "int" for "dict[str, list[str]]"; expected type "str"  [index]`
- `core\campaign\lore_generator.py:169: error: "dict[str, str]" has no attribute "format"  [attr-defined]`

### core\compiler\lua_optimizer.py

- `core\compiler\lua_optimizer.py:27: error: Need type annotation for "last_assignment" (hint: "last_assignment: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\compiler\lua_optimizer.py:28: error: Need type annotation for "seen_calls" (hint: "seen_calls: set[<type>] = ...")  [var-annotated]`

### core\critic\analyzers\visual_analyzer.py

- `core\critic\analyzers\visual_analyzer.py:105: error: Need type annotation for "cnt"  [var-annotated]`

### core\enterprise.py

- `core\enterprise.py:114: error: Item "None" of "Match[str] | None" has no attribute "group"  [union-attr]`
- `core\enterprise.py:195: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:196: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:197: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:198: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:199: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:200: error: "object" has no attribute "get"  [attr-defined]`
- `core\enterprise.py:201: error: "object" has no attribute "get"  [attr-defined]`

### core\factory\expansion_factory.py

- `core\factory\expansion_factory.py:33: error: "object" has no attribute "replace"  [attr-defined]`
- `core\factory\expansion_factory.py:51: error: "object" has no attribute "keys"  [attr-defined]`

### core\factory\season_generator.py

- `core\factory\season_generator.py:27: error: "object" has no attribute "extend"  [attr-defined]`

### core\game_design\content_designer.py

- `core\game_design\content_designer.py:44: error: Need type annotation for "tier"  [var-annotated]`
- `core\game_design\content_designer.py:60: error: Need type annotation for "tier"  [var-annotated]`

### core\knowledge\knowledge_base.py

- `core\knowledge\knowledge_base.py:48: error: Need type annotation for "distribution" (hint: "distribution: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\knowledge\knowledge_base.py:155: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `core\knowledge\knowledge_base.py:155: error: "Collection[str]" has no attribute "get"  [attr-defined]`

### core\learning\blueprint_catalog.py

- `core\learning\blueprint_catalog.py:274: error: "BlueprintRegistry" has no attribute "list_all"  [attr-defined]`
- `core\learning\blueprint_catalog.py:391: error: Need type annotation for "themes"  [var-annotated]`
- `core\learning\blueprint_catalog.py:392: error: Need type annotation for "categories"  [var-annotated]`
- `core\learning\blueprint_catalog.py:393: error: Need type annotation for "difficulties"  [var-annotated]`
- `core\learning\blueprint_catalog.py:394: error: Need type annotation for "versions"  [var-annotated]`
- `core\learning\blueprint_catalog.py:429: error: Need type annotation for "theme_stats"  [var-annotated]`
- `core\learning\blueprint_catalog.py:549: error: "Sequence[str]" has no attribute "append"  [attr-defined]`

### core\learning\blueprint_learner.py

- `core\learning\blueprint_learner.py:205: error: "LearningResult" has no attribute "saved_path"  [attr-defined]`
- `core\learning\blueprint_learner.py:282: error: "LearningResult" has no attribute "saved_path"  [attr-defined]`
- `core\learning\blueprint_learner.py:371: error: Need type annotation for "grounds" (hint: "grounds: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\blueprint_learner.py:372: error: Need type annotation for "items" (hint: "items: dict[<type>, <type>] = ...")  [var-annotated]`

### core\learning\dataset_builder.py

- `core\learning\dataset_builder.py:294: error: Need type annotation for "ground_types" (hint: "ground_types: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\dataset_builder.py:449: error: Need type annotation for "segments" (hint: "segments: list[<type>] = ...")  [var-annotated]`
- `core\learning\dataset_builder.py:474: error: "object" has no attribute "append"  [attr-defined]`
- `core\learning\dataset_builder.py:496: error: Need type annotation for "all_features" (hint: "all_features: list[<type>] = ...")  [var-annotated]`
- `core\learning\dataset_builder.py:542: error: Need type annotation for "style_counts" (hint: "style_counts: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\dataset_builder.py:543: error: Need type annotation for "type_counts" (hint: "type_counts: dict[<type>, <type>] = ...")  [var-annotated]`

### core\learning\learning_pipeline.py

- `core\learning\learning_pipeline.py:122: error: Need type annotation for "embeddings" (hint: "embeddings: list[<type>] = ...")  [var-annotated]`
- `core\learning\learning_pipeline.py:164: error: "None" has no attribute "get"  [attr-defined]`
- `core\learning\learning_pipeline.py:165: error: "None" has no attribute "get"  [attr-defined]`
- `core\learning\learning_pipeline.py:169: error: "None" has no attribute "embed_dataset"  [attr-defined]`
- `core\learning\learning_pipeline.py:170: error: "None" has no attribute "save_embeddings"  [attr-defined]`
- `core\learning\learning_pipeline.py:175: error: "None" has no attribute "train"  [attr-defined]`
- `core\learning\learning_pipeline.py:176: error: "None" has no attribute "save_profiles"  [attr-defined]`
- `core\learning\learning_pipeline.py:177: error: "None" has no attribute "style_profiles"  [attr-defined]`
- `core\learning\learning_pipeline.py:181: error: "None" has no attribute "train"  [attr-defined]`
- `core\learning\learning_pipeline.py:182: error: "None" has no attribute "save_profiles"  [attr-defined]`
- ... and 30 more

### core\learning\map_embedding.py

- `core\learning\map_embedding.py:100: error: Need type annotation for "ground_types" (hint: "ground_types: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\map_embedding.py:253: error: Need type annotation for "item_types" (hint: "item_types: dict[<type>, <type>] = ...")  [var-annotated]`

### core\learning\pattern_encoder.py

- `core\learning\pattern_encoder.py:699: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`

### core\learning\pattern_miner.py

- `core\learning\pattern_miner.py:264: error: Need type annotation for "grounds" (hint: "grounds: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\pattern_miner.py:265: error: Need type annotation for "items" (hint: "items: dict[<type>, <type>] = ...")  [var-annotated]`
- `core\learning\pattern_miner.py:350: error: Need type annotation for "all_grounds"  [var-annotated]`
- `core\learning\pattern_miner.py:351: error: Need type annotation for "all_items"  [var-annotated]`
- `core\learning\pattern_miner.py:352: error: Need type annotation for "all_spawn_monsters"  [var-annotated]`
- `core\learning\pattern_miner.py:510: error: Need type annotation for "symmetry_scores" (hint: "symmetry_scores: list[<type>] = ...")  [var-annotated]`

### core\learning\similarity_engine.py

- `core\learning\similarity_engine.py:445: error: Invalid index type "int" for "defaultdict[signedinteger[_32Bit | _64Bit], list[str]]"; expected type "signedinteger[_32Bit | _64Bit]"  [index]`
- `core\learning\similarity_engine.py:447: error: Invalid index type "int" for "defaultdict[signedinteger[_32Bit | _64Bit], list[str]]"; expected type "signedinteger[_32Bit | _64Bit]"  [index]`
- `core\learning\similarity_engine.py:468: error: Need type annotation for "style_counts"  [var-annotated]`
- `core\learning\similarity_engine.py:469: error: Need type annotation for "style_types"  [var-annotated]`
- `core\learning\similarity_engine.py:488: error: Need type annotation for "type_counts"  [var-annotated]`
- `core\learning\similarity_engine.py:489: error: Need type annotation for "type_styles"  [var-annotated]`

### core\learning\style_encoder.py

- `core\learning\style_encoder.py:185: error: Need type annotation for "ground_counts"  [var-annotated]`
- `core\learning\style_encoder.py:196: error: Need type annotation for "wall_counts"  [var-annotated]`
- `core\learning\style_encoder.py:212: error: Need type annotation for "item_counts"  [var-annotated]`
- `core\learning\style_encoder.py:350: error: Need type annotation for "ground_counter"  [var-annotated]`
- `core\learning\style_encoder.py:351: error: Need type annotation for "wall_counter"  [var-annotated]`
- `core\learning\style_encoder.py:352: error: Need type annotation for "item_counter"  [var-annotated]`
- `core\learning\style_encoder.py:356: error: Need type annotation for "shape_counters"  [var-annotated]`
- `core\learning\style_encoder.py:377: error: "float" has no attribute "items"  [attr-defined]`
- `core\learning\style_encoder.py:541: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`

### core\otbm\otbm_serializer.py

- `core\otbm\otbm_serializer.py:348: error: Need type annotation for "result"  [var-annotated]`
- `core\otbm\otbm_serializer.py:506: error: Need type annotation for "items" (hint: "items: list[<type>] = ...")  [var-annotated]`

### core\planner\planner.py

- `core\planner\planner.py:59: error: "object" has no attribute "capitalize"  [attr-defined]`
- `core\planner\planner.py:64: error: "object" has no attribute "capitalize"  [attr-defined]`
- `core\planner\planner.py:86: error: "object" has no attribute "capitalize"  [attr-defined]`
- `core\planner\planner.py:107: error: "object" has no attribute "capitalize"  [attr-defined]`
- `core\planner\planner.py:119: error: "object" has no attribute "capitalize"  [attr-defined]`
- `core\planner\planner.py:207: error: "object" has no attribute "get"  [attr-defined]`
- `core\planner\planner.py:208: error: "object" has no attribute "get"  [attr-defined]`
- `core\planner\planner.py:209: error: "object" has no attribute "get"  [attr-defined]`
- `core\planner\planner.py:216: error: "object" has no attribute "get"  [attr-defined]`
- `core\planner\planner.py:220: error: "object" has no attribute "get"  [attr-defined]`
- ... and 1 more

### core\planner\prompt_interpreter.py

- `core\planner\prompt_interpreter.py:10: error: Need type annotation for "result"  [var-annotated]`

### core\planner\world_size_estimator.py

- `core\planner\world_size_estimator.py:10: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\planner\world_size_estimator.py:11: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\planner\world_size_estimator.py:12: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`

### core\planner\world_validator.py

- `core\planner\world_validator.py:25: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`
- `core\planner\world_validator.py:31: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`

### core\playtest\progression_analyzer.py

- `core\playtest\progression_analyzer.py:248: error: Need type annotation for "results"  [var-annotated]`

### core\preview\heatmap_renderer.py

- `core\preview\heatmap_renderer.py:19: error: Need type annotation for "intensity"  [var-annotated]`

### core\preview\structure_renderer.py

- `core\preview\structure_renderer.py:45: error: Need type annotation for "biome_counts" (hint: "biome_counts: dict[<type>, <type>] = ...")  [var-annotated]`

### core\preview\tile_renderer.py

- `core\preview\tile_renderer.py:45: error: Need type annotation for "line" (hint: "line: list[<type>] = ...")  [var-annotated]`

### core\world_brain\decision_engine.py

- `core\world_brain\decision_engine.py:457: error: "object" has no attribute "get"  [attr-defined]`

### core\world_engine\boss_builder.py

- `core\world_engine\boss_builder.py:18: error: "object" has no attribute "lower"  [attr-defined]`

### core\world_engine\city_builder.py

- `core\world_engine\city_builder.py:17: error: "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)  [attr-defined]`

### data_extractor.py

- `data_extractor.py:126: error: "object" has no attribute "append"  [attr-defined]`
- `data_extractor.py:128: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:129: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:130: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:161: error: "object" has no attribute "append"  [attr-defined]`
- `data_extractor.py:163: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:164: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:165: error: "object" has no attribute "setdefault"  [attr-defined]`
- `data_extractor.py:286: error: Need type annotation for "names" (hint: "names: list[<type>] = ...")  [var-annotated]`
- `data_extractor.py:307: error: Need type annotation for "names" (hint: "names: list[<type>] = ...")  [var-annotated]`

### examples\enterprise_demo.py

- `examples\enterprise_demo.py:25: error: "object" has no attribute "get"  [attr-defined]`
- `examples\enterprise_demo.py:26: error: "object" has no attribute "get"  [attr-defined]`
- `examples\enterprise_demo.py:27: error: "object" has no attribute "keys"  [attr-defined]`
- `examples\enterprise_demo.py:28: error: "object" has no attribute "get"  [attr-defined]`

### examples\expansion_demo.py

- `examples\expansion_demo.py:11: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:12: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:13: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:14: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:15: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:16: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:17: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:18: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:20: error: "object" has no attribute "get"  [attr-defined]`
- `examples\expansion_demo.py:24: error: "object" has no attribute "get"  [attr-defined]`
- ... and 4 more

### ga_benchmark.py

- `ga_benchmark.py:172: error: Value of type "Collection[str]" is not indexable  [index]`

### mission_generator.py

- `mission_generator.py:4: error: Module "mission_generator" has no attribute "MissionGenerator"; maybe "TestMissionGenerator"?  [attr-defined]`

### pipeline_runner.py

- `pipeline_runner.py:337: error: "PreviewGenerator" has no attribute "generate_ascii"  [attr-defined]`

### quest_generator.py

- `quest_generator.py:4: error: Module "quest_generator" has no attribute "QuestGenerator"; maybe "TestQuestGenerator"?  [attr-defined]`

### raid_generator.py

- `raid_generator.py:4: error: Module "raid_generator" has no attribute "RaidGenerator"; maybe "TestRaidGenerator"?  [attr-defined]`

### reward_generator.py

- `reward_generator.py:4: error: Module "reward_generator" has no attribute "RewardGenerator"; maybe "TestRewardGenerator"?  [attr-defined]`

### tools\hotfix_lua_hardening.py

- `tools\hotfix_lua_hardening.py:351: error: "WorldModel" has no attribute "waypoints"  [attr-defined]`

### tools\hotfix_performance.py

- `tools\hotfix_performance.py:81: error: Module has no attribute "getrusage"  [attr-defined]`
- `tools\hotfix_performance.py:81: error: Module has no attribute "RUSAGE_SELF"  [attr-defined]`
- `tools\hotfix_performance.py:254: error: Module has no attribute "getrusage"  [attr-defined]`
- `tools\hotfix_performance.py:254: error: Module has no attribute "RUSAGE_SELF"  [attr-defined]`

### tools\hotfix_security.py

- `tools\hotfix_security.py:331: error: Value of type "Collection[str]" is not indexable  [index]`
- `tools\hotfix_security.py:333: error: Value of type "Collection[str]" is not indexable  [index]`

### tools\real_otbm_certification.py

- `tools\real_otbm_certification.py:52: error: "WorldModel" has no attribute "name"  [attr-defined]`

### tools\validate_modules.py

- `tools\validate_modules.py:163: error: "object" has no attribute "append"  [attr-defined]`

### ui\console.py

- `ui\console.py:84: error: "ConsolePanel" has no attribute "setTextColor"  [attr-defined]`

### ui\widgets\metric_card.py

- `ui\widgets\metric_card.py:71: error: "type[Qt]" has no attribute "AlignCenter"  [attr-defined]`

### ui\widgets\recent_artifacts_widget.py

- `ui\widgets\recent_artifacts_widget.py:75: error: "type[QHeaderView]" has no attribute "Stretch"  [attr-defined]`
- `ui\widgets\recent_artifacts_widget.py:76: error: "type[QTableWidget]" has no attribute "SelectRows"  [attr-defined]`
- `ui\widgets\recent_artifacts_widget.py:77: error: "type[QTableWidget]" has no attribute "NoEditTriggers"  [attr-defined]`

### ui\widgets\status_card.py

- `ui\widgets\status_card.py:87: error: "type[Qt]" has no attribute "AlignRight"  [attr-defined]`
- `ui\widgets\status_card.py:87: error: "type[Qt]" has no attribute "AlignVCenter"  [attr-defined]`

### validators\qa_pipeline.py

- `validators\qa_pipeline.py:37: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:40: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:41: error: "Collection[str]" has no attribute "append"  [attr-defined]`
- `validators\qa_pipeline.py:48: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:49: error: "Collection[str]" has no attribute "extend"  [attr-defined]`
- `validators\qa_pipeline.py:53: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:58: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:59: error: "Collection[str]" has no attribute "extend"  [attr-defined]`
- `validators\qa_pipeline.py:63: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- `validators\qa_pipeline.py:68: error: Unsupported target for indexed assignment ("Collection[str]")  [index]`
- ... and 2 more

## any_leakage (99 errors)

### config_manager.py

- `config_manager.py:39: error: Returning Any from function declared to return "dict[Any, Any]"  [no-any-return]`
- `config_manager.py:145: error: Returning Any from function declared to return "list[Any]"  [no-any-return]`

### core\analyzer\path_analyzer.py

- `core\analyzer\path_analyzer.py:68: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\analyzer\path_analyzer.py:81: error: Returning Any from function declared to return "bool"  [no-any-return]`

### core\architect\difficulty_planner.py

- `core\architect\difficulty_planner.py:328: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\difficulty_planner.py:330: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\difficulty_planner.py:331: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\difficulty_planner.py:336: error: Returning Any from function declared to return "int"  [no-any-return]`

### core\architect\mapper_ai.py

- `core\architect\mapper_ai.py:161: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\architect\theme_resolver.py

- `core\architect\theme_resolver.py:712: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`
- `core\architect\theme_resolver.py:816: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\architect\zone_planner.py

- `core\architect\zone_planner.py:353: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\zone_planner.py:356: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\zone_planner.py:357: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\architect\zone_planner.py:363: error: Returning Any from function declared to return "int"  [no-any-return]`

### core\balance\difficulty_balancer.py

- `core\balance\difficulty_balancer.py:343: error: Returning Any from function declared to return "DifficultyAnalysis"  [no-any-return]`

### core\balance\loot_balancer.py

- `core\balance\loot_balancer.py:387: error: Returning Any from function declared to return "LootAnalysis"  [no-any-return]`

### core\balance\xp_balancer.py

- `core\balance\xp_balancer.py:313: error: Returning Any from function declared to return "XPAnalysis"  [no-any-return]`

### core\blueprints\blueprint_placer.py

- `core\blueprints\blueprint_placer.py:294: error: Returning Any from function declared to return "int"  [no-any-return]`

### core\compiler\lua_emitter.py

- `core\compiler\lua_emitter.py:99: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\compiler\lua_emitter.py:111: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\config_manager.py

- `core\config_manager.py:203: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`

### core\content\map_designer.py

- `core\content\map_designer.py:361: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\content\map_designer.py:370: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\content\map_designer.py:379: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\content\map_designer.py:398: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\content\map_designer.py:404: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\evolution\expansion_engine.py

- `core\evolution\expansion_engine.py:345: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`
- `core\evolution\expansion_engine.py:994: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`
- `core\evolution\expansion_engine.py:1005: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`

### core\evolution\improvement_engine.py

- `core\evolution\improvement_engine.py:243: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`
- `core\evolution\improvement_engine.py:256: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`

### core\evolution\map_evolver.py

- `core\evolution\map_evolver.py:311: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`
- `core\evolution\map_evolver.py:364: error: Returning Any from function declared to return "MapQualityReport"  [no-any-return]`
- `core\evolution\map_evolver.py:377: error: Returning Any from function declared to return "ImprovementResult"  [no-any-return]`
- `core\evolution\map_evolver.py:397: error: Returning Any from function declared to return "ExpansionResult"  [no-any-return]`

### core\evolution\modernization_engine.py

- `core\evolution\modernization_engine.py:565: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`
- `core\evolution\modernization_engine.py:576: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`

### core\exporters\lua_exporter.py

- `core\exporters\lua_exporter.py:93: error: Returning Any from function declared to return "str"  [no-any-return]`
- `core\exporters\lua_exporter.py:128: error: Returning Any from function declared to return "LuaValidationResult"  [no-any-return]`

### core\generators\world_generator.py

- `core\generators\world_generator.py:240: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\knowledge\dataset_builder.py

- `core\knowledge\dataset_builder.py:220: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### core\knowledge\extractors\boss_extractor.py

- `core\knowledge\extractors\boss_extractor.py:124: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\learning\blueprint_catalog.py

- `core\learning\blueprint_catalog.py:274: error: Returning Any from function declared to return "list[Blueprint]"  [no-any-return]`

### core\learning\dataset_builder.py

- `core\learning\dataset_builder.py:532: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### core\learning\pattern_encoder.py

- `core\learning\pattern_encoder.py:138: error: Returning Any from function declared to return "float"  [no-any-return]`
- `core\learning\pattern_encoder.py:180: error: Returning Any from function declared to return "float"  [no-any-return]`

### core\observability\diagnostics.py

- `core\observability\diagnostics.py:140: error: Returning Any from function declared to return "bool"  [no-any-return]`

### core\otbm\item_decoder.py

- `core\otbm\item_decoder.py:114: error: Returning Any from function declared to return "int"  [no-any-return]`

### core\otbm\item_encoder.py

- `core\otbm\item_encoder.py:57: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\item_encoder.py:79: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\node_decoder.py

- `core\otbm\node_decoder.py:608: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`
- `core\otbm\node_decoder.py:755: error: Returning Any from function declared to return "list[dict[str, Any]]"  [no-any-return]`
- `core\otbm\node_decoder.py:764: error: Returning Any from function declared to return "list[dict[str, Any]]"  [no-any-return]`

### core\otbm\otbm_deserializer.py

- `core\otbm\otbm_deserializer.py:26: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`

### core\otbm\otbm_parser.py

- `core\otbm\otbm_parser.py:374: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### core\otbm\otbm_serializer.py

- `core\otbm\otbm_serializer.py:255: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\otbm_serializer.py:476: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:489: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:519: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:527: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:567: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:572: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:588: error: Returning Any from function declared to return "int"  [no-any-return]`
- `core\otbm\otbm_serializer.py:595: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`
- `core\otbm\otbm_serializer.py:783: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\otbm_writer.py

- `core\otbm\otbm_writer.py:44: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\spawn_encoder.py

- `core\otbm\spawn_encoder.py:53: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\spawn_encoder.py:71: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\tile_decoder.py

- `core\otbm\tile_decoder.py:269: error: Returning Any from function declared to return "bool"  [no-any-return]`

### core\otbm\tile_encoder.py

- `core\otbm\tile_encoder.py:150: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\tile_encoder.py:201: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\tile_encoder.py:237: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\tile_encoder.py:263: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\waypoint_encoder.py

- `core\otbm\waypoint_encoder.py:124: error: Returning Any from function declared to return "bytes"  [no-any-return]`
- `core\otbm\waypoint_encoder.py:136: error: Returning Any from function declared to return "bytes"  [no-any-return]`

### core\otbm\world_builder.py

- `core\otbm\world_builder.py:230: error: Returning Any from function declared to return "list[dict[str, Any]]"  [no-any-return]`

### core\preview\preview_renderer.py

- `core\preview\preview_renderer.py:95: error: Returning Any from function declared to return "tuple[int, int, int]"  [no-any-return]`
- `core\preview\preview_renderer.py:101: error: Returning Any from function declared to return "tuple[int, int, int]"  [no-any-return]`

### core\quality\visual_analyzer.py

- `core\quality\visual_analyzer.py:63: error: Returning Any from function declared to return "float"  [no-any-return]`

### core\recovery.py

- `core\recovery.py:163: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### core\registry\blueprint_registry.py

- `core\registry\blueprint_registry.py:68: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### core\themes\theme_resolver.py

- `core\themes\theme_resolver.py:164: error: Returning Any from function declared to return "dict[Any, Any] | None"  [no-any-return]`

### core\world_brain\decision_engine.py

- `core\world_brain\decision_engine.py:432: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\world_brain\world_brain.py

- `core\world_brain\world_brain.py:191: error: Returning Any from function declared to return "DesignExplanation"  [no-any-return]`
- `core\world_brain\world_brain.py:195: error: Returning Any from function declared to return "WorldBrainState"  [no-any-return]`
- `core\world_brain\world_brain.py:199: error: Returning Any from function declared to return "list[dict[str, Any]]"  [no-any-return]`

### core\world_engine\export_pipeline.py

- `core\world_engine\export_pipeline.py:59: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`
- `core\world_engine\export_pipeline.py:67: error: Returning Any from function declared to return "str"  [no-any-return]`

### core\world_engine\world_engine.py

- `core\world_engine\world_engine.py:167: error: Returning Any from function declared to return "dict[str, object]"  [no-any-return]`

### data_extractor.py

- `data_extractor.py:192: error: Returning Any from function declared to return "dict[Any, Any]"  [no-any-return]`

### ga_certify.py

- `ga_certify.py:20: error: Returning Any from function declared to return "dict[Any, Any]"  [no-any-return]`

### rag\retrieval.py

- `rag\retrieval.py:21: error: Returning Any from function declared to return "list[dict[Any, Any]]"  [no-any-return]`

### tools\hotfix_audit.py

- `tools\hotfix_audit.py:50: error: Returning Any from function declared to return "dict[Any, Any] | None"  [no-any-return]`

### tools\hotfix_certify.py

- `tools\hotfix_certify.py:46: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`

### tools\hotfix_performance.py

- `tools\hotfix_performance.py:73: error: Returning Any from function declared to return "float"  [no-any-return]`
- `tools\hotfix_performance.py:83: error: Returning Any from function declared to return "float"  [no-any-return]`

### tools\run_rc1_1.py

- `tools\run_rc1_1.py:124: error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

### ui\dashboard_data_provider.py

- `ui\dashboard_data_provider.py:100: error: Returning Any from function declared to return "dict[Any, Any]"  [no-any-return]`

## generated_excluded (0 errors)

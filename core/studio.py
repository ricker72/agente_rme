import json
import logging
from pathlib import Path

from ollama_client import OllamaClient
from rag.retrieval import RagRetriever
from core.architecture import ArchitectureGraph, PatternLibrary
from core.generators import CityGenerator, DungeonGenerator
from core.knowledge.knowledge_base import KnowledgeGraph
from core.planner import AIPlanner
from core.world_engine import WorldEngine

logger = logging.getLogger(__name__)

class AIMapStudio:
    """High-level AI map studio controller for OpenTibia RME script generation."""

    def __init__(self, config: dict, item_docs: list[dict], monster_docs: list[dict], npc_docs: list[dict]):
        self.config = config
        self.ollama = OllamaClient()
        self.retriever = RagRetriever()
        self.pattern_library = PatternLibrary()
        self.architecture_graph = ArchitectureGraph()
        self.knowledge_graph = KnowledgeGraph(self.pattern_library, self.architecture_graph)
        self.planner = AIPlanner(self.pattern_library, self.architecture_graph, self.knowledge_graph)
        self.world_engine = WorldEngine(self.knowledge_graph, self.architecture_graph)
        self._build_knowledge_base(item_docs, monster_docs, npc_docs)

    def _build_knowledge_base(self, item_docs: list[dict], monster_docs: list[dict], npc_docs: list[dict]):
        catalog = item_docs + monster_docs + npc_docs
        if catalog:
            self.retriever.build_store(catalog)
        else:
            logger.warning("No documents available to build RAG knowledge base.")

    def ingest_map_analysis(self, source: str, analysis_data: dict) -> None:
        self.knowledge_graph.ingest_analysis(source, analysis_data)

    def create_generation_prompt(self, description: str, monster_names: list[str], npc_names: list[str]) -> str:
        context = self.retriever.retrieve(description, top_k=6)
        rag_text = self.retriever.build_rag_context(context)
        knowledge_context = self.knowledge_graph.build_context(
            description=description,
            monster_names=monster_names,
            npc_names=npc_names,
            level_hint=self.config.get("player_level"),
        )
        return self.ollama.build_user_message(
            description, rag_text, knowledge_context, monster_names, npc_names
        )

    def generate_script(self, description: str, model: str, monster_names: list[str], npc_names: list[str], on_chunk, on_complete, on_error):
        world_plan_result = self.planner.plan(description)
        if not world_plan_result.get("plan_valid", False):
            errors = world_plan_result.get("validation", [])
            on_error(f"Plan inválido: {errors}")
            return

        world_plan = world_plan_result.get("world_plan", {})
        world_model = self.world_engine.build(world_plan)
        try:
            lua_code = self.world_engine.export(world_model)
        except RuntimeError as exc:
            on_error(f"Export blocked: {exc}")
            return
        on_complete(lua_code)
        return

    def available_models(self) -> list[str]:
        alive, _ = self.ollama.check_ollama_alive()
        if not alive:
            return []
        return self.ollama.list_models()

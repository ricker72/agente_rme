from datetime import datetime
from typing import List

class PromptBuilder:
    """Builds structured prompts for Ollama using the OpenTibiaBR RME API."""

    def build_system_message(self) -> str:
        return (
            "Eres un asistente experto en OpenTibia Remere's Map Editor (RME). "
            "Tu salida debe ser un script Lua válido para RME que use la API real de OpenTibiaBR. "
            "No incluyas explicaciones, solo el código Lua necesario en la respuesta final.\n"
            "Usa preferentemente funciones de transacción y validación de mapa como app.transaction() y app.hasMap()."
        )

    def build_user_message(self, description: str, context_documents: List[dict]) -> str:
        context_text = "\n".join(
            f"- {doc['title']}: {doc['text']}" for doc in context_documents[:6]
        )
        if not context_text:
            context_text = "No hay contexto de RAG disponible."

        instruction = (
            "Genera un script Lua para RME basado en la descripción del mapa y los datos del juego. "
            "El script debe completar el entorno del mapa con tiles, items, monstros y NPCs usando la API de RME. "
            "Conserva siempre el estilo y formato adecuado para un archivo .lua."
        )

        rules = (
            "Reglas de generación:\n"
            "1) Usa solo el API de RME real: app.transaction(), app.hasMap(), map:getOrCreateTile(x,y,z), tile:setGround(itemId), creature:createMonster(name, tile), npc:create(name, tile).\n"
            "2) No generes funciones inventadas de la API.\n"
            "3) El resultado final debe ser un script Lua completo que pueda cargarse en RME.\n"
            "4) Evita comentarios explicativos largos en el código. Usa comentarios mínimos si es necesario.\n"
        )

        prompt_lines = [
            f"Descripción del mapa: {description}",
            "",
            "Contexto de juego relevante:",
            context_text,
            "",
            instruction,
            rules,
            "",
            "Plantilla DSL disponible:\n",
            "local RME = require(\"lua/rme_dsl\")\n",
            "RME.transaction(function(map)\n  -- usa la API de RME para crear o actualizar tiles\nend)\n",
        ]

        return "\n".join(prompt_lines)

from typing import List


class PromptBuilder:
    """Builds structured prompts for Ollama using the OpenTibiaBR RME API."""

    def build_system_message(self) -> str:
        return (
            "You are an expert assistant in OpenTibia Remere's Map Editor (RME). "
            "Your output must be a valid Lua script for RME that uses the real OpenTibiaBR API. "
            "Do not include explanations, only the necessary Lua code in the final response.\n"
            "Prefer using transaction and map validation functions like app.transaction() and app.hasMap()."
        )

    def build_user_message(
        self, description: str, context_documents: List[dict]
    ) -> str:
        context_text = "\n".join(
            f"- {doc['title']}: {doc['text']}" for doc in context_documents[:6]
        )
        if not context_text:
            context_text = "No RAG context available."

        instruction = (
            "Generate a Lua script for RME based on the map description and game data. "
            "The script should complete the map environment with tiles, items, monsters and NPCs using the RME API. "
            "Always preserve the proper style and format for a .lua file."
        )

        rules = (
            "Generation rules:\n"
            "1) Use only the real RME API: app.transaction(), app.hasMap(), "
            "map:getOrCreateTile(x,y,z), tile:setGround(itemId), "
            "creature:createMonster(name, tile), npc:create(name, tile).\n"
            "2) Do not generate invented API functions.\n"
            "3) The final result must be a complete Lua script that can be loaded in RME.\n"
            "4) Avoid long explanatory comments in the code. Use minimal comments if necessary.\n"
        )

        prompt_lines = [
            f"Map description: {description}",
            "",
            "Relevant game context:",
            context_text,
            "",
            instruction,
            rules,
            "",
            "Available DSL template:\n",
            'local RME = require("lua/rme_dsl")\n',
            "RME.transaction(function(map)\n  -- use the RME API to create or update tiles\nend)\n",
        ]

        return "\n".join(prompt_lines)

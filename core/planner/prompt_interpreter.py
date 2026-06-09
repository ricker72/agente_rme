from __future__ import annotations

import re
from typing import Dict


class PromptInterpreter:
    def interpret(self, prompt: str) -> Dict[str, object]:
        lower = prompt.lower()
        result = {
            "city": None,
            "dungeon": None,
            "north_zone": None,
            "difficulty_range": None,
            "story_tags": [],
        }

        styles = ["issavi", "roshamuul", "yalahar", "library", "ankrahmun", "soul war", "soulwar"]
        for style in styles:
            if style in lower:
                if "city" in lower or "ciudad" in lower or "expansión" in lower:
                    result["city"] = style.replace(" ", "")
                elif "dungeon" in lower or style in ["roshamuul", "soulwar"]:
                    result["dungeon"] = style.replace(" ", "")

        if "norte" in lower or "north" in lower:
            for style in styles:
                if style in lower:
                    result["north_zone"] = style.replace(" ", "")
                    break

        range_match = re.search(r"(\d+)[^\d]+(\d+)", prompt)
        if range_match:
            result["difficulty_range"] = (int(range_match.group(1)), int(range_match.group(2)))

        if "expansión" in lower or "expansion" in lower:
            result["story_tags"].append("expansion")
        if "boss" in lower or "jefe" in lower:
            result["story_tags"].append("boss")
        if "quest" in lower or "mision" in lower:
            result["story_tags"].append("quest")

        if result["city"] is None and "issavi" in lower:
            result["city"] = "issavi"
        if result["dungeon"] is None and "roshamuul" in lower:
            result["dungeon"] = "roshamuul"

        return result

"""
MVP V0.1 — Prompt Interpreter
Parses natural language prompts into structured JSON for map generation.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PromptIntent:
    theme: List[str] = field(default_factory=list)
    level_range: List[int] = field(default_factory=lambda: [300, 500])
    type: str = "hunt"
    raw_prompt: str = ""


class PromptInterpreter:
    """
    Interprets Spanish/English natural language prompts about Tibia hunt zones.

    Example:
        >>> pi = PromptInterpreter()
        >>> intent = pi.interpret("Genera una zona Issavi + Roshamuul nivel 300-500")
        >>> intent.theme => ["issavi", "roshamuul"]
        >>> intent.level_range => [300, 500]
    """

    KNOWN_THEMES = {
        "issavi", "roshamuul", "falcon", "cobra", "lion", "asura",
        "mirror", "library", "soulwar", "ferumbras", "thais", "carlin",
        "venore", "edron", "darashia", "ankrahmun", "port hope",
        "yalahar", "svargrond", "liberty bay", "kazordoon", "ab'dendriel",
        "feyrist", "oramond", "roshamuul",
    }

    KNOWN_TYPES = {
        "hunt", "dungeon", "city", "boss", "hybrid",
    }

    def interpret(self, prompt: str) -> PromptIntent:
        lower = prompt.lower()

        # Detect themes
        themes = [t for t in self.KNOWN_THEMES if t in lower]
        theme_mapping = {
            "roshamuul": "roshamuul",  # handle both spellings
        }
        themes = [theme_mapping.get(t, t) for t in themes]

        # Detect level range
        level_range = self._extract_level_range(prompt)

        # Detect type
        map_type = self._extract_type(prompt)

        return PromptIntent(
            theme=themes,
            level_range=level_range,
            type=map_type,
            raw_prompt=prompt,
        )

    def _extract_level_range(self, prompt: str) -> List[int]:
        import re

        # Pattern: "nivel X-Y" or "level X-Y" or "X-Y"
        patterns = [
            r'(?:nivel|level)\s*(\d+)\s*[-–a]+\s*(\d+)',
            r'(\d{2,4})\s*[-–]\s*(\d{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                lo, hi = int(match.group(1)), int(match.group(2))
                if 1 <= lo <= 2000 and 1 <= hi <= 2000:
                    return [min(lo, hi), max(lo, hi)]

        return [300, 500]  # default

    def _extract_type(self, prompt: str) -> str:
        lower = prompt.lower()
        for t in sorted(self.KNOWN_TYPES, key=len, reverse=True):
            if t in lower:
                return t

        # Spanish language fallbacks
        if "ciudad" in lower:
            return "city"
        if "mazmorra" in lower or "dungeon" in lower or "calabozo" in lower:
            return "dungeon"
        if "jefe" in lower or "boss" in lower:
            return "boss"

        return "hunt"

    def to_dict(self, intent: PromptIntent) -> Dict:
        return {
            "theme": intent.theme,
            "level_range": intent.level_range,
            "type": intent.type,
            "raw_prompt": intent.raw_prompt,
        }
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DialogLine:
    """A single line of NPC dialog."""

    speaker: str = ""
    text: str = ""
    mood: str = "neutral"  # "neutral", "happy", "angry", "sad", "urgent"
    response_options: List[str] = field(default_factory=list)
    next_dialog_id: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)

    def to_dialog(self) -> str:
        return f"[{self.speaker}]: {self.text}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "mood": self.mood,
            "response_options": self.response_options,
            "next_dialog_id": self.next_dialog_id,
            "conditions": self.conditions,
        }


# Dialog templates per mood and role
NPC_DIALOGS: Dict[str, Dict[str, List[str]]] = {
    "quest_giver": {
        "neutral": [
            "We need someone capable for a dangerous mission.",
            "I have a task that requires a brave adventurer.",
            "The council has authorized me to hire mercenaries.",
        ],
        "urgent": [
            "Time is running out! The enemy grows stronger every hour!",
            "If we don't act now, all will be lost!",
            "Please, you must hurry! Lives are at stake!",
        ],
    },
    "merchant": {
        "neutral": [
            "I have wares from across the land.",
            "Looking for something special? I've got it.",
            "My prices are fair, considering the danger.",
        ],
        "happy": [
            "Business is booming! How can I help you?",
            "You look like someone who appreciates quality goods.",
        ],
    },
    "ally": {
        "neutral": [
            "I've been tracking the enemy's movements.",
            "We should plan our approach carefully.",
            "I know a shortcut through the mountains.",
        ],
        "urgent": [
            "We've been spotted! Get ready to fight!",
            "The enemy is closing in on our position!",
        ],
    },
    "enemy": {
        "angry": [
            "You've been a thorn in my side for too long!",
            "This is where your journey ends!",
            "No one has ever survived facing me!",
        ],
    },
}


class DialogGenerator:
    """Generates NPC dialog trees for the campaign."""

    def __init__(self, seed: int = 42):
        self._seed = seed

    def generate(
        self, npc_name: str, role: str = "quest_giver", dialog_count: int = 3
    ) -> List[DialogLine]:
        """
        Generate a dialog tree for an NPC.

        Args:
            npc_name: Name of the NPC speaking.
            role: Role of the NPC.
            dialog_count: Number of dialog lines to generate.

        Returns:
            List of DialogLine objects.
        """
        dialogs: List[DialogLine] = []
        templates = NPC_DIALOGS.get(role, NPC_DIALOGS.get("quest_giver", {}))

        moods = list(templates.keys())
        lines: List[str] = []
        for mood in moods:
            lines.extend(templates[mood])

        for i in range(dialog_count):
            text = lines[i % len(lines)]
            mood = moods[i % len(moods)] if moods else "neutral"

            response_options = self._generate_responses(role, mood)

            dialogs.append(
                DialogLine(
                    speaker=npc_name,
                    text=text,
                    mood=mood,
                    response_options=response_options,
                    next_dialog_id=f"dialog_{i + 1}" if i < dialog_count - 1 else "",
                )
            )

        return dialogs

    def _generate_responses(self, role: str, mood: str) -> List[str]:
        """Generate player response options."""
        if mood == "urgent":
            return ["I'll help right away!", "Tell me what to do."]
        if role == "merchant":
            return ["Show me your wares.", "I'll come back later."]
        if role == "enemy":
            return ["Prepare to fight!", "I don't want trouble."]
        return ["I accept the quest.", "Tell me more.", "Not now."]

    def generate_boss_dialog(self, boss_name: str) -> List[DialogLine]:
        """Generate boss encounter dialog."""
        return [
            DialogLine(
                speaker=boss_name,
                text=f"I am {boss_name}, the destroyer of worlds! You dare challenge ME?!",
                mood="angry",
                response_options=["I will stop you!"],
                next_dialog_id="boss_fight",
            ),
            DialogLine(
                speaker=boss_name,
                text="You think you can defeat me? I have consumed a thousand souls!",
                mood="angry",
                response_options=["Your reign of terror ends now!"],
                next_dialog_id="boss_fight_start",
            ),
        ]

    def generate_quest_dialog(self, npc_name: str, quest_name: str) -> List[DialogLine]:
        """Generate quest acceptance dialog."""
        return [
            DialogLine(
                speaker=npc_name,
                text=f"I need you to complete a mission: {quest_name}. Are you up to the task?",
                mood="neutral",
                response_options=["I accept!", "Tell me more.", "Not now."],
                next_dialog_id="quest_offer",
            ),
            DialogLine(
                speaker=npc_name,
                text=f"Excellent! Report back when you've completed {quest_name}. May the gods protect you.",
                mood="happy",
                response_options=["I won't let you down!"],
                next_dialog_id="quest_accepted",
                conditions={"quest_accepted": True},
            ),
        ]

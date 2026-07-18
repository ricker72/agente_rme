from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_quest_anchors(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    anchors = []
    for quest in sorted(blueprint.get("quests", []), key=lambda item: item["id"]):
        anchors.append(
            {
                "id": f"quest_anchor_{quest['id']}",
                "quest_ref": quest["id"],
                "anchor_type": "future_quest",
                "quest_implemented": False,
                "logical_only": True,
            }
        )
    for boss in sorted(blueprint.get("bosses", []), key=lambda item: item["id"]):
        anchors.append(
            {
                "id": f"boss_anchor_{boss['id']}",
                "boss_ref": boss["id"],
                "anchor_type": "future_boss",
                "quest_implemented": False,
                "logical_only": True,
            }
        )
    return {"artifact": "QUEST_ANCHOR_MODEL", "logical_only": True, "anchors": anchors}

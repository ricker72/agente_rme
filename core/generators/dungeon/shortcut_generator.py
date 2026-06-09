from __future__ import annotations

from typing import List, Dict

from .room_generator import Room


class ShortcutGenerator:
    def create_shortcuts(self, floor) -> List[Dict[str, object]]:
        shortcuts: List[Dict[str, object]] = []
        if floor.rooms:
            entrance = floor.rooms[0].center()
            boss = floor.rooms[-1].center()
            shortcuts.append({
                "type": "ladder",
                "from": entrance,
                "to": boss,
                "description": "Acceso rápido entre entrada y arena del jefe.",
            })
            shortcuts.append({
                "type": "teleport",
                "from": (entrance[0] + 2, entrance[1]),
                "to": (boss[0] - 2, boss[1]),
                "description": "Teletransportador de emergencia.",
            })
        return shortcuts

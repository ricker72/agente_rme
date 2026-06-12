"""
Spawn Encoder — convierte spawns de WorldModel a nodos OTBM SPAWN_AREA + MONSTER.

Genera nodos OTBM para spawns y también prepara datos para monster.xml.

No incrusta lógica Lua — solo produce nodos OTBM binarios.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .node_encoder import NodeEncoder


class SpawnEncoder:
    """
    Codifica spawns del WorldModel a nodos OTBM SPAWN_AREA/MONSTER.

    Spawn(
        monster="Dragon",
        respawn=60,
        radius=5
    )
    ↓
    SPAWN_AREA (center_x, center_y, z, radius)
      └── MONSTER (name, direction, spawntime)
    """

    def __init__(self):
        self.node = NodeEncoder()

    def encode_spawn(self, x: int, y: int, z: int, spawn: Any) -> bytes:
        """
        Codifica un spawn individual a nodo SPAWN_AREA + MONSTER.

        Args:
            x, y, z: Coordenadas del spawn.
            spawn: Spawn dataclass o dict con monster, respawn, radius.

        Returns:
            bytes: Nodo OTBM SPAWN_AREA conteniendo un MONSTER child.
        """
        monster_name = self._get_monster_name(spawn)
        interval = self._get_respawn(spawn)
        radius = self._get_radius(spawn)

        monster_node = self.node.encode_monster(
            name=monster_name,
            direction=2,  # South (default)
            spawntime=interval,
        )
        return self.node.encode_spawn_area(
            center_x=x,
            center_y=y,
            center_z=z,
            radius=radius,
            children=monster_node,
        )

    def encode_spawns_container(self, spawn_nodes: bytes) -> bytes:
        """
        Envuelve múltiples spawns en un nodo SPAWNS contenedor.

        Args:
            spawn_nodes: bytes concatenados de nodos SPAWN_AREA.

        Returns:
            bytes: Nodo OTBM SPAWNS.
        """
        return self.node.encode_spawns(spawn_nodes)

    def extract_monster_names(self, world_model: Any) -> List[Dict[str, Any]]:
        """
        Extrae nombres de monstruos del WorldModel para monster.xml.

        Args:
            world_model: WorldModel instance.

        Returns:
            Lista de dicts: [{"name": "Dragon", "respawn": 60}, ...]
        """
        monsters: Dict[str, int] = {}
        tiles = getattr(world_model, "tiles", {})

        for tile in tiles.values():
            spawn = getattr(tile, "spawn", None)
            if spawn is not None:
                name = self._get_monster_name(spawn)
                respawn = self._get_respawn(spawn)
                if name:
                    monsters[name] = max(monsters.get(name, 0), respawn)

        # También revisar spawns a nivel de world_model
        for spawn in getattr(world_model, "spawns", []):
            name = self._get_monster_name(spawn)
            respawn = self._get_respawn(spawn)
            if name:
                monsters[name] = max(monsters.get(name, 0), respawn)

        return [{"name": k, "respawn": v} for k, v in sorted(monsters.items())]

    def generate_monster_xml(self, world_model: Any) -> str:
        """
        Genera XML de monstruos para monster.xml.

        Args:
            world_model: WorldModel instance.

        Returns:
            String XML: <monsters><monster name="..." respawn="..." />...</monsters>
        """
        entries = self.extract_monster_names(world_model)
        lines = ["<monsters>"]
        for e in entries:
            lines.append(f'  <monster name="{e["name"]}" respawn="{e["respawn"]}" />')
        lines.append("</monsters>")
        return "\n".join(lines)

    @staticmethod
    def _get_monster_name(spawn: Any) -> str:
        """Extrae el nombre del monstruo de un spawn en cualquier formato."""
        if isinstance(spawn, dict):
            return str(spawn.get("monster", spawn.get("name", "")))
        return str(getattr(spawn, "monster", getattr(spawn, "name", "")))

    @staticmethod
    def _get_respawn(spawn: Any) -> int:
        """Extrae el tiempo de respawn."""
        if isinstance(spawn, dict):
            return int(spawn.get("respawn", spawn.get("interval", 60)))
        return int(getattr(spawn, "respawn", getattr(spawn, "interval", 60)))

    @staticmethod
    def _get_radius(spawn: Any) -> int:
        """Extrae el radio del spawn."""
        if isinstance(spawn, dict):
            return int(spawn.get("radius", spawn.get("spawn_radius", 3)))
        return int(getattr(spawn, "radius", getattr(spawn, "spawn_radius", 3)))

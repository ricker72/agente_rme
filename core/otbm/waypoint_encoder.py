"""
Waypoint Encoder — exporta waypoints del WorldModel a nodos OTBM.

Si existen regiones o puntos definidos, genera nodos WAYPOINT.

También prepara datos para waypoints.xml.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .node_encoder import NodeEncoder


class WaypointEncoder:
    """
    Codifica waypoints a nodos OTBM WAYPOINT.

    Los waypoints se derivan de:
      - Regiones con coordenadas definidas
      - Waypoints explícitos en world_model.waypoints
      - Puntos de entrada de estructuras (temple_x, temple_y)
    """

    def __init__(self):
        self.node = NodeEncoder()

    def extract_waypoints(self, world_model: Any) -> List[Dict[str, Any]]:
        """
        Extrae lista de waypoints del WorldModel.

        Args:
            world_model: WorldModel instance.

        Returns:
            Lista de dicts: [{"name": "...", "x": ..., "y": ..., "z": ...}].
        """
        waypoints: List[Dict[str, Any]] = []

        # 1. Waypoints explícitos
        explicit = getattr(world_model, "waypoints", []) or []
        for wp in explicit:
            if isinstance(wp, dict):
                waypoints.append(
                    {
                        "name": str(wp.get("name", "waypoint")),
                        "x": int(wp.get("x", 0)),
                        "y": int(wp.get("y", 0)),
                        "z": int(wp.get("z", 7)),
                    }
                )
            else:
                waypoints.append(
                    {
                        "name": str(getattr(wp, "name", "waypoint")),
                        "x": int(getattr(wp, "x", 0)),
                        "y": int(getattr(wp, "y", 0)),
                        "z": int(getattr(wp, "z", 7)),
                    }
                )

        # 2. Regiones como waypoints
        regions = getattr(world_model, "regions", [])
        for region in regions:
            name = getattr(region, "name", "")
            if name and not any(w["name"] == name for w in waypoints):
                # Usar centro de tiles de la región o default
                waypoints.append(
                    {
                        "name": name,
                        "x": 0,
                        "y": 0,
                        "z": 7,
                    }
                )

        # 3. Puntos de templo de towns/cities
        cities = getattr(world_model, "cities", []) or []
        for city in cities:
            name = (
                city.get("name", "")
                if isinstance(city, dict)
                else getattr(city, "name", "")
            )
            if name and not any(w["name"] == f"{name}_temple" for w in waypoints):
                tx = (
                    city.get("temple_x", 0)
                    if isinstance(city, dict)
                    else getattr(city, "temple_x", 0)
                )
                ty = (
                    city.get("temple_y", 0)
                    if isinstance(city, dict)
                    else getattr(city, "temple_y", 0)
                )
                tz = (
                    city.get("temple_z", 7)
                    if isinstance(city, dict)
                    else getattr(city, "temple_z", 7)
                )
                waypoints.append(
                    {
                        "name": f"{name}_temple",
                        "x": int(tx),
                        "y": int(ty),
                        "z": int(tz),
                    }
                )

        return waypoints

    def encode_waypoint(self, name: str, x: int, y: int, z: int) -> bytes:
        """
        Codifica un waypoint individual a nodo OTBM WAYPOINT.

        Args:
            name: Nombre del waypoint.
            x, y, z: Coordenadas.

        Returns:
            bytes: Nodo OTBM WAYPOINT.
        """
        return self.node.encode_waypoint(name=name, x=x, y=y, z=z)

    def encode_waypoints_container(self, waypoint_nodes: bytes) -> bytes:
        """
        Envuelve múltiples waypoints en nodo WAYPOINTS.

        Args:
            waypoint_nodes: bytes concatenados de nodos WAYPOINT.

        Returns:
            bytes: Nodo OTBM WAYPOINTS.
        """
        return self.node.encode_waypoints(waypoint_nodes)

    def generate_waypoint_xml(self, world_model: Any) -> str:
        """
        Genera XML de waypoints para waypoints.xml.

        Args:
            world_model: WorldModel instance.

        Returns:
            String XML.
        """
        wps = self.extract_waypoints(world_model)
        if not wps:
            return ""

        lines = ["<waypoints>"]
        for wp in wps:
            lines.append(
                f'  <waypoint name="{wp["name"]}" x="{wp["x"]}" y="{wp["y"]}" z="{wp["z"]}" />'
            )
        lines.append("</waypoints>")
        return "\n".join(lines)

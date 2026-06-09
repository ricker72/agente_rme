"""
HITO 12 — Spawn Analyzer: analiza spawns desde .otbm (vía pipeline) y .xml.
Soporta análisis binario directo y vía OTBMImporter/NodeDecoder.
"""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


class SpawnAnalyzer:
    """Analiza spawns de monstruos desde OTBM o XML."""

    # Marcadores binarios OTBM
    _NODE_MONSTER = 0x0F
    _NODE_SPAWN_AREA = 0x06

    def __init__(self, otbm_importer: Optional[Any] = None):
        """
        Args:
            otbm_importer: Instancia opcional de OTBMImporter.
        """
        self._otbm_importer = otbm_importer

    # ------------------------------------------------------------------
    # Análisis desde OTBM (world_dict)
    # ------------------------------------------------------------------

    def analyze_otbm_spawns(self, spawns_raw: List[Dict[str, Any]]) -> List[Dict[str, object]]:
        """Analiza spawns desde lista extraída del world_dict.

        Args:
            spawns_raw: Lista de spawns del world_dict de WorldBuilder.

        Returns:
            Lista estandarizada de spawns con metadata.
        """
        if not spawns_raw:
            return []

        results = []
        for sp in spawns_raw:
            entry = {
                "monster": sp.get("monster", sp.get("name", "unknown")),
                "x": int(sp.get("x", 0)),
                "y": int(sp.get("y", 0)),
                "z": int(sp.get("z", 0)),
                "radius": int(sp.get("radius", 0)),
            }
            if "respawn" in sp:
                entry["respawn"] = int(sp["respawn"])
            if "direction" in sp:
                entry["direction"] = int(sp["direction"])
            if "spawntime" in sp:
                entry["spawntime"] = int(sp["spawntime"])
            results.append(entry)

        return results

    # ------------------------------------------------------------------
    # Análisis OTBM directo (bytes)
    # ------------------------------------------------------------------

    def analyze_otbm_direct(self, data: bytes) -> List[Dict[str, object]]:
        """Extrae y analiza spawns directamente desde bytes OTBM.

        Busca estructura: SPAWNS -> SPAWN_AREA -> MONSTER.
        """
        spawns = []

        # Buscar todos los nodos SPAWN_AREA (0x06) con hijos MONSTER (0x0F)
        offset = 0
        while True:
            idx = data.find(bytes([self._NODE_SPAWN_AREA]), offset)
            if idx == -1 or idx + 3 >= len(data):
                break
            try:
                area_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + area_size > len(data):
                    offset = idx + 1
                    continue

                area_payload = data[idx + 3 : idx + 3 + area_size]
                if len(area_payload) < 6:
                    offset = idx + 3 + area_size
                    continue

                center_x = struct.unpack_from("<H", area_payload, 0)[0]
                center_y = struct.unpack_from("<H", area_payload, 2)[0]
                center_z = area_payload[4]
                radius = area_payload[5]

                # Buscar hijos MONSTER dentro del área
                monsters = self._parse_monsters_in_area(
                    data, idx + 3 + 6, idx + 3 + area_size
                )
                for monster in monsters:
                    spawns.append({
                        "monster": monster.get("name", "unknown"),
                        "x": center_x,
                        "y": center_y,
                        "z": center_z,
                        "radius": radius,
                        "direction": monster.get("direction", 2),
                        "spawntime": monster.get("spawntime", 60),
                    })

                offset = idx + 3 + area_size

            except (struct.error, IndexError):
                offset = idx + 1

        return spawns

    def _parse_monsters_in_area(
        self, data: bytes, start: int, end: int
    ) -> List[Dict[str, Any]]:
        """Busca nodos MONSTER dentro de un rango de bytes."""
        monsters = []
        offset = start
        while offset < end:
            idx = data.find(bytes([self._NODE_MONSTER]), offset)
            if idx == -1 or idx >= end or idx + 3 >= end:
                break
            try:
                mon_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + mon_size > end:
                    offset = idx + 1
                    continue
                mon_payload = data[idx + 3 : idx + 3 + mon_size]
                name, name_offset = _read_string(mon_payload, 0)
                direction = mon_payload[name_offset] if name_offset < len(mon_payload) else 2
                spawntime = 60
                if name_offset + 5 <= len(mon_payload):
                    spawntime = struct.unpack_from("<I", mon_payload, name_offset + 1)[0]
                monsters.append({
                    "name": name,
                    "direction": direction,
                    "spawntime": spawntime,
                })
                offset = idx + 3 + mon_size
            except (struct.error, IndexError):
                offset = idx + 1
        return monsters

    # ------------------------------------------------------------------
    # Análisis XML
    # ------------------------------------------------------------------

    def analyze_spawn_xml(self, root: ET.Element) -> List[Dict[str, object]]:
        """Extrae spawns desde XML (<spawns><spawn>...)."""
        spawns = []
        for spawn in root.findall("spawns/spawn"):
            spawns.append({
                "monster": spawn.get("monster", ""),
                "x": int(spawn.get("x", 0)),
                "y": int(spawn.get("y", 0)),
                "z": int(spawn.get("z", 0)),
                "radius": int(spawn.get("radius", 0)),
            })
        return spawns

    def analyze_monster_file(self, path: str) -> Dict[str, object]:
        """Analiza archivo monster.xml externo."""
        tree = ET.parse(path)
        root = tree.getroot()
        counts = Counter()
        for monster in root.findall("monster"):
            counts[monster.get("name", "unknown")] += 1
        return {
            "monster_density": len(counts),
            "monster_counts": dict(counts),
            "zone_classifications": self._classify_zones(counts),
        }

    # ------------------------------------------------------------------
    # Clasificación y agregación
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_zones(counts: Counter) -> Dict[str, str]:
        if not counts:
            return {}
        total = sum(counts.values())
        if total > 200:
            return {"zone": "endgame"}
        if total > 100:
            return {"zone": "hard"}
        if total > 50:
            return {"zone": "medium"}
        return {"zone": "easy"}

    @staticmethod
    def summarize_spawns(spawns: List[Dict[str, object]]) -> Dict[str, object]:
        """Genera resumen estadístico de spawns."""
        if not spawns:
            return {
                "total_spawns": 0,
                "unique_monsters": 0,
                "top_monsters": [],
                "avg_radius": 0.0,
                "zone_classification": "empty",
            }

        monster_counts = Counter()
        radii = []
        floors = set()

        for sp in spawns:
            monster_counts[sp.get("monster", "unknown")] += 1
            radii.append(int(sp.get("radius", 0)))
            floors.add(int(sp.get("z", 0)))

        avg_radius = sum(radii) / len(radii) if radii else 0.0
        top = monster_counts.most_common(10)

        zone = SpawnAnalyzer._classify_zones(monster_counts)

        return {
            "total_spawns": len(spawns),
            "unique_monsters": len(monster_counts),
            "top_monsters": [{"name": n, "count": c} for n, c in top],
            "avg_radius": round(avg_radius, 2),
            "floors_with_spawns": sorted(floors),
            "zone_classification": zone.get("zone", "unknown"),
        }


def _read_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Lee un string length-prefixed (uint16) desde bytes."""
    if offset + 2 > len(data):
        return "", offset
    length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    if offset + length > len(data):
        return "", offset - 2
    try:
        s = data[offset : offset + length].decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        s = data[offset : offset + length].decode("latin-1", errors="replace")
    return s, offset + length
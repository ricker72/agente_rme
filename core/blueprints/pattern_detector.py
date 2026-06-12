"""
HITO 13 — Pattern Detector: detecta patrones constructivos repetitivos
en tiles, items y spawns del WorldModel.

Detecta:
  - Wall patterns (rectangulos, pasillos, habitaciones delimitadas)
  - Floor patterns (zonas de suelo homogeneo)
  - Decoration clusters (grupos de decoraciones)
  - Spawn patterns (grupos de spawns)
  - Entrance/exit points (puntos de acceso)
  - Repeating structural motifs
  - Room detection basada en muros

Los patrones se expresan como BoundingBox + tipo + confianza.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class Pattern:
    """Un patron constructivo detectado."""

    pattern_type: str  # "wall", "floor", "decoration_cluster", "spawn_cluster", "room", "corridor", "entrance"
    bounds: Tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)
    confidence: float  # 0.0 - 1.0
    tile_ids: List[int] = field(default_factory=list)
    item_ids: List[int] = field(default_factory=list)
    spawn_names: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "bounds": list(self.bounds),
            "confidence": self.confidence,
            "tile_ids": self.tile_ids[:20],
            "item_ids": self.item_ids[:20],
            "spawn_names": self.spawn_names[:10],
            "description": self.description,
        }


class PatternDetector:
    """
    Detecta patrones constructivos en datos de tiles, items y spawns.

    Trabaja con datos agregados (dicts de conteo) y con datos posicionales
    (listas de tiles con x, y) cuando estan disponibles.
    """

    # Muro IDs (referencia rapida)
    WALL_IDS: Set[int] = {
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007,
        1008,
        1009,
        2100,
        2101,
        2102,
        2103,
        2104,
        2105,
    }

    # Puerta IDs
    DOOR_IDS: Set[int] = {
        1209,
        1210,
        1211,
        1212,
        1213,
        1214,
        1215,
        1216,
        1217,
        1220,
        1221,
        1222,
        1223,
        1224,
        1225,
        5000,
        5001,
        5002,
        5003,
        5004,
        5005,
        5006,
    }

    def detect(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
        spawns: List[Dict[str, Any]],
        map_size: Optional[Dict[str, int]] = None,
    ) -> List[Pattern]:
        """
        Detecta todos los patrones constructivos.

        Args:
            tiles: Lista de tile dicts con claves: x, y, z, ground, items.
            items: Dict {item_key: count} de items agregados.
            spawns: Lista de spawn dicts con claves: x, y, monster, radius.
            map_size: Dict {"width": w, "height": h} opcional.

        Returns:
            Lista de Pattern detectados.
        """
        patterns: List[Pattern] = []

        # Spawn clusters (se pueden detectar sin tiles)
        spawn_patterns = self._detect_spawn_clusters(spawns)
        patterns.extend(spawn_patterns)

        if not tiles:
            return patterns

        # 1. Detectar habitaciones (rooms) mediante bounding boxes agrupadas
        rooms = self._detect_rooms(tiles)
        patterns.extend(rooms)

        # 2. Detectar pasillos (corridors)
        corridors = self._detect_corridors(tiles)
        patterns.extend(corridors)

        # 3. Detectar patrones de suelo (floor patterns)
        floor_patterns = self._detect_floor_patterns(tiles, items)
        patterns.extend(floor_patterns)

        # 4. Detectar clusters de decoraciones
        deco_patterns = self._detect_decoration_clusters(tiles, items)
        patterns.extend(deco_patterns)

        # 5. Detectar entradas (entrances) basadas en puertas
        entrances = self._detect_entrances(tiles, items)
        patterns.extend(entrances)

        return patterns

    # ------------------------------------------------------------------
    # Room detection
    # ------------------------------------------------------------------

    def _detect_rooms(self, tiles: List[Dict[str, Any]]) -> List[Pattern]:
        """Detecta habitaciones analizando bounding boxes de items agrupados."""
        patterns: List[Pattern] = []

        # Agrupar items por tipo en el espacio
        wall_tiles = []
        door_tiles = []

        for tile in tiles:
            tile_items = tile.get("items", []) + tile.get("all_items", [])
            for item in tile_items:
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                if isinstance(item_id, int):
                    if item_id in self.WALL_IDS:
                        wall_tiles.append((tile["x"], tile["y"]))
                    elif item_id in self.DOOR_IDS:
                        door_tiles.append((tile["x"], tile["y"]))

        # Si hay muros, intentar agrupar en habitaciones
        if wall_tiles:
            rooms = self._cluster_positions(wall_tiles, min_points=8)
            for i, cluster in enumerate(rooms):
                if len(cluster) >= 8:
                    xs = [p[0] for p in cluster]
                    ys = [p[1] for p in cluster]
                    bounds = (min(xs), min(ys), max(xs), max(ys))
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]

                    # Validar que parece una habitacion
                    if 3 <= width <= 50 and 3 <= height <= 50:
                        patterns.append(
                            Pattern(
                                pattern_type="room",
                                bounds=bounds,
                                confidence=min(0.9, len(cluster) / 20.0),
                                tile_ids=sorted(
                                    set(
                                        t.get("ground", 0)
                                        for t in tiles
                                        if bounds[0] <= t.get("x", 0) <= bounds[2]
                                        and bounds[1] <= t.get("y", 0) <= bounds[3]
                                    )
                                ),
                                description=f"Room {i + 1}: {width}x{height} tiles, {len(cluster)} walls",
                            )
                        )

        # Si hay puertas, marcar entradas
        if door_tiles:
            for dx, dy in door_tiles:
                patterns.append(
                    Pattern(
                        pattern_type="entrance",
                        bounds=(dx, dy, dx, dy),
                        confidence=0.8,
                        description=f"Entrance at ({dx},{dy})",
                    )
                )

        return patterns

    # ------------------------------------------------------------------
    # Corridor detection
    # ------------------------------------------------------------------

    def _detect_corridors(self, tiles: List[Dict[str, Any]]) -> List[Pattern]:
        """Detecta pasillos: zonas estrechas y alargadas con suelo uniforme."""
        patterns: List[Pattern] = []

        # Agrupar tiles por tipo de suelo
        ground_groups: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for tile in tiles:
            ground = tile.get("ground")
            if ground is not None:
                try:
                    gid = int(ground)
                except (ValueError, TypeError):
                    continue
                ground_groups[gid].append((tile["x"], tile["y"]))

        # Para cada grupo de suelo, buscar regiones con forma de pasillo
        for gid, positions in ground_groups.items():
            if len(positions) < 5:
                continue

            clusters = self._cluster_positions(positions, min_points=5)
            for cluster in clusters:
                if len(cluster) < 5:
                    continue

                xs = [p[0] for p in cluster]
                ys = [p[1] for p in cluster]
                width = max(xs) - min(xs)
                height = max(ys) - min(ys)

                # Un pasillo es estrecho en una dimension y largo en otra
                is_corridor = (
                    width >= 5 and height <= 3 and width / max(height, 1) >= 3
                ) or (height >= 5 and width <= 3 and height / max(width, 1) >= 3)

                if is_corridor:
                    patterns.append(
                        Pattern(
                            pattern_type="corridor",
                            bounds=(min(xs), min(ys), max(xs), max(ys)),
                            confidence=min(0.85, len(cluster) / 30.0),
                            tile_ids=[gid],
                            description=f"Corridor: {width}x{height} tiles, ground_id={gid}",
                        )
                    )

        return patterns

    # ------------------------------------------------------------------
    # Floor pattern detection
    # ------------------------------------------------------------------

    def _detect_floor_patterns(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
    ) -> List[Pattern]:
        """Detecta patrones de suelo: zonas homogeneas de gran tamano."""
        patterns: List[Pattern] = []

        if not tiles:
            return patterns

        # Encontrar el suelo dominante
        ground_counts: Dict[int, int] = defaultdict(int)
        for tile in tiles:
            ground = tile.get("ground")
            if ground is not None:
                try:
                    gid = int(ground)
                except (ValueError, TypeError):
                    continue
                ground_counts[gid] += 1

        total = sum(ground_counts.values())
        if total == 0:
            return patterns

        # Suelos que cubren >15% del area
        for gid, count in ground_counts.items():
            pct = count / total
            if pct > 0.15:
                # Encontrar el bounding box de este suelo
                xs = [t["x"] for t in tiles if int(t.get("ground", 0)) == gid]
                ys = [t["y"] for t in tiles if int(t.get("ground", 0)) == gid]
                if xs and ys:
                    patterns.append(
                        Pattern(
                            pattern_type="floor",
                            bounds=(min(xs), min(ys), max(xs), max(ys)),
                            confidence=min(1.0, pct * 3),
                            tile_ids=[gid],
                            description=f"Floor zone: ground_id={gid}, coverage={pct:.1%}",
                        )
                    )

        return patterns

    # ------------------------------------------------------------------
    # Decoration cluster detection
    # ------------------------------------------------------------------

    def _detect_decoration_clusters(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
    ) -> List[Pattern]:
        """Detecta clusters de decoraciones (items no-estructurales)."""
        patterns: List[Pattern] = []

        deco_positions: List[Tuple[int, int, int]] = []

        for tile in tiles:
            tile_items = tile.get("items", []) + tile.get("all_items", [])
            for item in tile_items:
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                if isinstance(item_id, int):
                    if item_id not in self.WALL_IDS and item_id not in self.DOOR_IDS:
                        deco_positions.append((tile["x"], tile["y"], item_id))

        if not deco_positions:
            return patterns

        # Agrupar decoraciones por posicion
        deco_xy = [(x, y) for x, y, _ in deco_positions]
        clusters = self._cluster_positions(deco_xy, min_points=3)

        for i, cluster in enumerate(clusters):
            if len(cluster) >= 3:
                xs = [p[0] for p in cluster]
                ys = [p[1] for p in cluster]
                # Obtener los item_ids en este cluster
                item_ids = list(
                    set(
                        iid
                        for x, y, iid in deco_positions
                        if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys)
                    )
                )

                patterns.append(
                    Pattern(
                        pattern_type="decoration_cluster",
                        bounds=(min(xs), min(ys), max(xs), max(ys)),
                        confidence=min(0.9, len(cluster) / 15.0),
                        item_ids=item_ids[:20],
                        description=f"Decoration cluster {i + 1}: {len(cluster)} decorations",
                    )
                )

        return patterns

    # ------------------------------------------------------------------
    # Entrance detection
    # ------------------------------------------------------------------

    def _detect_entrances(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
    ) -> List[Pattern]:
        """Detecta entradas basadas en puertas."""
        patterns: List[Pattern] = []

        entrance_count = 0
        for tile in tiles:
            tile_items = tile.get("items", []) + tile.get("all_items", [])
            for item in tile_items:
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                if isinstance(item_id, int) and item_id in self.DOOR_IDS:
                    entrance_count += 1
                    patterns.append(
                        Pattern(
                            pattern_type="entrance",
                            bounds=(tile["x"], tile["y"], tile["x"], tile["y"]),
                            confidence=0.85,
                            item_ids=[item_id],
                            description=f"Entrance at ({tile['x']},{tile['y']}), door_id={item_id}",
                        )
                    )

        # Si hay muchas puertas, condensar en un solo patron
        if entrance_count > 10:
            all_xs = [p.bounds[0] for p in patterns[-entrance_count:]]
            all_ys = [p.bounds[1] for p in patterns[-entrance_count:]]
            patterns = [p for p in patterns if p.pattern_type != "entrance"]
            patterns.append(
                Pattern(
                    pattern_type="entrance",
                    bounds=(min(all_xs), min(all_ys), max(all_xs), max(all_ys)),
                    confidence=0.7,
                    description=f"Multiple entrances: {entrance_count} doors",
                )
            )

        return patterns

    # ------------------------------------------------------------------
    # Spawn cluster detection
    # ------------------------------------------------------------------

    def _detect_spawn_clusters(self, spawns: List[Dict[str, Any]]) -> List[Pattern]:
        """Detecta clusters de spawns."""
        patterns: List[Pattern] = []

        if not spawns:
            return patterns

        positions = []
        for sp in spawns:
            x = sp.get("x", 0)
            y = sp.get("y", 0)
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                positions.append((int(x), int(y)))

        if not positions:
            return patterns

        clusters = self._cluster_positions(positions, min_points=2, radius=15)

        for i, cluster in enumerate(clusters):
            if len(cluster) >= 2:
                xs = [p[0] for p in cluster]
                ys = [p[1] for p in cluster]
                # Encontrar spawn names en este cluster
                names = [
                    sp.get("monster", "")
                    for sp in spawns
                    if min(xs) <= sp.get("x", 0) <= max(xs)
                    and min(ys) <= sp.get("y", 0) <= max(ys)
                ]

                unique_names = list(set(names))
                patterns.append(
                    Pattern(
                        pattern_type="spawn_cluster",
                        bounds=(min(xs), min(ys), max(xs), max(ys)),
                        confidence=min(0.95, len(cluster) / 10.0),
                        spawn_names=unique_names[:10],
                        description=f"Spawn cluster {i + 1}: {len(cluster)} spawns, "
                        f"monsters: {', '.join(unique_names[:5])}",
                    )
                )

        return patterns

    # ------------------------------------------------------------------
    # Spatial clustering utility
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_positions(
        positions: List[Tuple[int, int]],
        min_points: int = 3,
        radius: int = 8,
    ) -> List[List[Tuple[int, int]]]:
        """
        Agrupa posiciones (x,y) en clusters espaciales usando DBSCAN simple.

        Args:
            positions: Lista de tuplas (x, y).
            min_points: Minimo de puntos para formar un cluster.
            radius: Radio de vecindad.

        Returns:
            Lista de clusters, cada uno es una lista de (x, y).
        """
        if len(positions) < min_points:
            return []

        visited: Set[Tuple[int, int]] = set()
        clusters: List[List[Tuple[int, int]]] = []

        # Construir un indice espacial simple (grid hash)
        grid: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        cell_size = radius
        for pos in positions:
            cell = (pos[0] // cell_size, pos[1] // cell_size)
            grid[cell].append(pos)

        # Para cada punto no visitado, expandir cluster
        for pos in positions:
            if pos in visited:
                continue

            cluster: List[Tuple[int, int]] = []
            queue = [pos]
            visited.add(pos)

            while queue:
                current = queue.pop(0)
                cluster.append(current)

                # Buscar vecinos en celdas adyacentes
                cx = current[0] // cell_size
                cy = current[1] // cell_size
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        cell = (cx + dx, cy + dy)
                        for neighbor in grid.get(cell, []):
                            if neighbor in visited:
                                continue
                            dist = max(
                                abs(neighbor[0] - current[0]),
                                abs(neighbor[1] - current[1]),
                            )
                            if dist <= radius:
                                visited.add(neighbor)
                                queue.append(neighbor)

            if len(cluster) >= min_points:
                clusters.append(cluster)

        return clusters

    # ------------------------------------------------------------------
    # Analisis agregado (sin datos posicionales)
    # ------------------------------------------------------------------

    def detect_aggregate(
        self,
        tiles_stats: Dict[str, int],
        items_stats: Dict[str, int],
        spawn_count: int,
        house_count: int,
        waypoint_count: int,
    ) -> List[Pattern]:
        """
        Version agregada para cuando no hay datos posicionales por tile.

        Produce patrones inferidos de las estadisticas globales.
        """
        patterns: List[Pattern] = []

        # Patron de muros
        wall_count = 0
        for item_key, count in items_stats.items():
            try:
                item_id = int(item_key.replace("item_", ""))
            except (ValueError, AttributeError):
                continue
            if item_id in self.WALL_IDS:
                wall_count += count

        if wall_count > 20:
            patterns.append(
                Pattern(
                    pattern_type="wall",
                    bounds=(0, 0, 0, 0),
                    confidence=min(0.9, wall_count / 200.0),
                    description=f"Wall pattern: {wall_count} wall items",
                )
            )

        # Patron de suelo dominante
        if tiles_stats:
            dominant = max(tiles_stats, key=tiles_stats.get)
            dom_count = tiles_stats[dominant]
            total = sum(tiles_stats.values())
            if dom_count / max(total, 1) > 0.4:
                patterns.append(
                    Pattern(
                        pattern_type="floor",
                        bounds=(0, 0, 0, 0),
                        confidence=min(1.0, dom_count / total * 2),
                        description=f"Dominant floor: {dominant} ({dom_count} tiles)",
                    )
                )

        # Patron de spawns
        if spawn_count > 5:
            patterns.append(
                Pattern(
                    pattern_type="spawn_cluster",
                    bounds=(0, 0, 0, 0),
                    confidence=min(0.8, spawn_count / 30.0),
                    description=f"Spawn pattern: {spawn_count} spawns",
                )
            )

        # Patron de estructuras
        if house_count > 3:
            patterns.append(
                Pattern(
                    pattern_type="room",
                    bounds=(0, 0, 0, 0),
                    confidence=min(0.7, house_count / 15.0),
                    description=f"Structure pattern: {house_count} buildings",
                )
            )

        return patterns

    # ------------------------------------------------------------------
    # Repeating pattern search
    # ------------------------------------------------------------------

    def find_repeating_patterns(
        self,
        tiles: List[Dict[str, Any]],
        min_repetitions: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Busca secuencias de tiles que se repiten (motivos).

        Util para detectar:
          - Muros repetitivos (almenas, torres)
          - Patrones de suelo (damero, mosaico)
          - Estructuras modulares

        Args:
            tiles: Lista de tile dicts.
            min_repetitions: Minimo de repeticiones para reportar.

        Returns:
            Lista de motivos repetitivos con su frecuencia.
        """
        if len(tiles) < 4:
            return []

        # Crear una "firma" para cada tile basada en ground + primeros items
        signatures: List[str] = []
        for tile in sorted(tiles, key=lambda t: (t.get("y", 0), t.get("x", 0))):
            ground = str(tile.get("ground", "0"))
            items = tile.get("items", [])[:3]
            item_ids = "_".join(
                str(i.get("item_id", i)) if isinstance(i, dict) else str(i)
                for i in items
            )
            signatures.append(f"{ground}|{item_ids}")

        # Contar secuencias repetidas (bigramas, trigramas)
        patterns: Dict[str, int] = Counter()

        for window_size in (2, 3, 4):
            for i in range(len(signatures) - window_size + 1):
                seq = " -> ".join(signatures[i : i + window_size])
                patterns[seq] += 1

        # Filtrar resultados significativos
        result = []
        for seq, count in patterns.most_common(20):
            if count >= min_repetitions:
                result.append(
                    {
                        "sequence": seq,
                        "repetitions": count,
                        "window_size": len(seq.split(" -> ")),
                    }
                )

        return result

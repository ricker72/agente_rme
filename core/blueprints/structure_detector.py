"""
HITO 13 — Structure Detector: detecta estructuras constructivas complejas
a partir de los datos del WorldModel.

Detecta:
  - Habitaciones (rooms) con bounding box, area y tipo
  - Pasillos (corridors) con orientacion y dimensiones
  - Edificios completos (agrupaciones de habitaciones)
  - Zonas tematicas (temple, hunt, city, dungeon)
  - Patrones de layout (grid, radial, linear, organic)
  - Jerarquia estructural (main > secondary > tertiary)
  - Puntos de interes (temple, depot, arena)
  - Bordes naturales vs artificiales

La salida es un dict estructurado que alimenta directamente
al Blueprint Extractor para generar Blueprint objects.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class DetectedStructure:
    """Estructura constructiva detectada."""
    structure_type: str  # "room", "corridor", "building", "zone", "poi"
    name: str = ""
    bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (min_x, min_y, max_x, max_y)
    area: int = 0
    confidence: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)
    sub_structures: List["DetectedStructure"] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_type": self.structure_type,
            "name": self.name,
            "bounds": list(self.bounds),
            "area": self.area,
            "confidence": self.confidence,
            "properties": self.properties,
            "sub_structures": [s.to_dict() for s in self.sub_structures],
            "description": self.description,
        }


class StructureDetector:
    """
    Detecta estructuras constructivas complejas en datos del WorldModel.

    Opera en dos modos:
      1. Con tiles posicionales: analisis espacial completo.
      2. Con estadisticas agregadas: inferencia estructural.
    """

    # Tipos de estructura
    STRUCTURE_TYPES = [
        "room", "corridor", "hall", "chamber",
        "building", "temple", "depot", "arena",
        "market", "housing_block", "city_center",
        "dungeon_level", "cavern", "mine",
        "wall_segment", "bridge", "staircase",
    ]

    # IDs de items que indican puntos de interes (POI)
    POI_ITEM_IDS: Dict[int, str] = {
        5000: "depot",
        5001: "depot",
        5002: "temple",
        5003: "temple",
        5004: "arena",
        5005: "market",
        5006: "housing",
    }

    def detect(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
        waypoints: List[Dict[str, Any]],
        map_size: Optional[Dict[str, int]] = None,
    ) -> List[DetectedStructure]:
        """
        Detecta todas las estructuras constructivas.

        Args:
            tiles: Lista de tile dicts posicionales.
            items: Dict {item_key: count} de items.
            spawns: Lista de spawns.
            houses: Lista de houses/edificios.
            waypoints: Lista de waypoints.
            map_size: Dict {"width": w, "height": h}.

        Returns:
            Lista de DetectedStructure ordenadas por relevancia.
        """
        structures: List[DetectedStructure] = []

        if not tiles:
            return structures

        width = map_size.get("width", 100) if map_size else 100
        height = map_size.get("height", 100) if map_size else 100

        # 1. Rooms (habitaciones)
        rooms = self._detect_rooms_structured(tiles)
        structures.extend(rooms)

        # 2. Corridors (pasillos)
        corridors = self._detect_corridors_structured(tiles)
        structures.extend(corridors)

        # 3. Buildings (agrupaciones de habitaciones)
        buildings = self._group_into_buildings(rooms, corridors)
        structures.extend(buildings)

        # 4. Zones (zonas tematicas)
        zones = self._detect_zones(tiles, items, spawns, houses)
        structures.extend(zones)

        # 5. Points of Interest
        pois = self._detect_pois(tiles, items, houses, waypoints)
        structures.extend(pois)

        # 6. Layout type
        layout = self._detect_layout(tiles, width, height)
        structures.append(layout)

        # 7. Structural hierarchy
        hierarchy = self._build_hierarchy(structures)
        structures.append(hierarchy)

        # Filtrar y ordenar por confianza
        structures = [s for s in structures if s.confidence > 0.1]
        structures.sort(key=lambda s: s.confidence, reverse=True)

        return structures

    # ------------------------------------------------------------------
    # Room detection (estructurada)
    # ------------------------------------------------------------------

    def _detect_rooms_structured(
        self, tiles: List[Dict[str, Any]]
    ) -> List[DetectedStructure]:
        """Detecta habitaciones como estructuras."""
        structures: List[DetectedStructure] = []

        # Agrupar tiles por bounding boxes basados en densidad
        positions = [(t["x"], t["y"]) for t in tiles]
        clusters = self._cluster_density(positions, cell_size=10)

        for i, cluster in enumerate(clusters):
            if len(cluster) < 5:
                continue

            xs = [p[0] for p in cluster]
            ys = [p[1] for p in cluster]
            bx = (min(xs), min(ys), max(xs), max(ys))
            area = (bx[2] - bx[0]) * (bx[3] - bx[1])

            # Obtener grounds en esta region
            grounds = set()
            for t in tiles:
                if bx[0] <= t["x"] <= bx[2] and bx[1] <= t["y"] <= bx[3]:
                    ground = t.get("ground")
                    if ground is not None:
                        try:
                            grounds.add(int(ground))
                        except (ValueError, TypeError):
                            pass

            room_type = self._classify_room_type(grounds, bx)

            structures.append(DetectedStructure(
                structure_type="room",
                name=f"room_{i+1}",
                bounds=bx,
                area=area,
                confidence=min(0.95, len(cluster) / 50.0),
                properties={
                    "grounds": list(grounds)[:10],
                    "tile_count": len(cluster),
                    "room_type": room_type,
                },
                description=f"Room {i+1}: {bx[2]-bx[0]}x{bx[3]-bx[1]}, "
                            f"{len(cluster)} tiles, type={room_type}",
            ))

        return structures

    # ------------------------------------------------------------------
    # Corridor detection (estructurada)
    # ------------------------------------------------------------------

    def _detect_corridors_structured(
        self, tiles: List[Dict[str, Any]]
    ) -> List[DetectedStructure]:
        """Detecta pasillos como estructuras."""
        structures: List[DetectedStructure] = []

        # Agrupar por suelo y buscar formas alargadas
        ground_groups: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for t in tiles:
            ground = t.get("ground")
            if ground is not None:
                try:
                    gid = int(ground)
                except (ValueError, TypeError):
                    continue
                ground_groups[gid].append((t["x"], t["y"]))

        idx = 0
        for gid, positions in ground_groups.items():
            if len(positions) < 5:
                continue

            clusters = self._cluster_density(positions, cell_size=5)
            for cluster in clusters:
                if len(cluster) < 5:
                    continue

                xs = [p[0] for p in cluster]
                ys = [p[1] for p in cluster]
                w = max(xs) - min(xs)
                h = max(ys) - min(ys)

                # Determinar si es pasillo
                if w >= 4 and h <= 3 and w / max(h, 1) >= 3:
                    orientation = "horizontal"
                    is_corridor = True
                elif h >= 4 and w <= 3 and h / max(w, 1) >= 3:
                    orientation = "vertical"
                    is_corridor = True
                else:
                    is_corridor = False

                if is_corridor:
                    idx += 1
                    bx = (min(xs), min(ys), max(xs), max(ys))
                    structures.append(DetectedStructure(
                        structure_type="corridor",
                        name=f"corridor_{idx}",
                        bounds=bx,
                        area=(bx[2] - bx[0]) * (bx[3] - bx[1]),
                        confidence=min(0.9, len(cluster) / 40.0),
                        properties={
                            "orientation": orientation,
                            "length": max(w, h),
                            "width": min(w, h),
                            "ground_id": gid,
                        },
                        description=f"Corridor {idx}: {orientation}, "
                                    f"length={max(w,h)}, ground={gid}",
                    ))

        return structures

    # ------------------------------------------------------------------
    # Building detection (agrupacion)
    # ------------------------------------------------------------------

    def _group_into_buildings(
        self,
        rooms: List[DetectedStructure],
        corridors: List[DetectedStructure],
    ) -> List[DetectedStructure]:
        """Agrupa habitaciones y pasillos en edificios."""
        structures: List[DetectedStructure] = []

        if not rooms:
            return structures

        # Agrupar por proximidad espacial
        all_structures = rooms + corridors
        merged: Set[int] = set()
        building_idx = 0

        for i, struct in enumerate(all_structures):
            if i in merged:
                continue

            # Encontrar estructuras cercanas
            building_parts = [struct]
            merged.add(i)

            for j, other in enumerate(all_structures):
                if j in merged:
                    continue
                if self._are_adjacent(struct.bounds, other.bounds, margin=5):
                    building_parts.append(other)
                    merged.add(j)

            if len(building_parts) >= 2:
                building_idx += 1
                all_bx = [s.bounds for s in building_parts]
                bx = (
                    min(b[0] for b in all_bx),
                    min(b[1] for b in all_bx),
                    max(b[2] for b in all_bx),
                    max(b[3] for b in all_bx),
                )
                area = (bx[2] - bx[0]) * (bx[3] - bx[1])

                structures.append(DetectedStructure(
                    structure_type="building",
                    name=f"building_{building_idx}",
                    bounds=bx,
                    area=area,
                    confidence=min(0.85, len(building_parts) / 5.0),
                    sub_structures=building_parts,
                    properties={
                        "room_count": sum(
                            1 for s in building_parts if s.structure_type == "room"
                        ),
                        "corridor_count": sum(
                            1 for s in building_parts if s.structure_type == "corridor"
                        ),
                        "total_parts": len(building_parts),
                    },
                    description=f"Building {building_idx}: {len(building_parts)} parts, "
                                f"area={area}",
                ))

        return structures

    # ------------------------------------------------------------------
    # Zone detection
    # ------------------------------------------------------------------

    def _detect_zones(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
    ) -> List[DetectedStructure]:
        """Detecta zonas tematicas."""
        structures: List[DetectedStructure] = []

        if not tiles:
            return structures

        # Calcular bounding box total
        all_xs = [t["x"] for t in tiles]
        all_ys = [t["y"] for t in tiles]
        if not all_xs:
            return structures

        total_bounds = (min(all_xs), min(all_ys), max(all_xs), max(all_ys))

        # Zona de spawns (hunting)
        if spawns:
            spawn_positions = [
                (sp["x"], sp["y"]) for sp in spawns
                if isinstance(sp.get("x"), (int, float))
                and isinstance(sp.get("y"), (int, float))
            ]
            if spawn_positions:
                sx = [p[0] for p in spawn_positions]
                sy = [p[1] for p in spawn_positions]
                spawn_area = (
                    (max(sx) - min(sx)) * (max(sy) - min(sy))
                )
                structures.append(DetectedStructure(
                    structure_type="zone",
                    name="hunting_zone",
                    bounds=(min(sx), min(sy), max(sx), max(sy)),
                    area=spawn_area,
                    confidence=min(0.9, len(spawns) / 20.0),
                    properties={
                        "zone_type": "hunting",
                        "spawn_count": len(spawns),
                        "unique_monsters": len(set(
                            sp.get("monster", "") for sp in spawns
                        )),
                    },
                    description=f"Hunting zone: {len(spawns)} spawns",
                ))

        # Zona urbana (houses)
        if houses:
            house_positions = [
                (h.get("temple_x", h.get("x", 0)),
                 h.get("temple_y", h.get("y", 0)))
                for h in houses
            ]
            hx = [p[0] for p in house_positions]
            hy = [p[1] for p in house_positions]
            structures.append(DetectedStructure(
                structure_type="zone",
                name="urban_zone",
                bounds=(min(hx), min(hy), max(hx), max(hy)),
                area=(max(hx) - min(hx)) * (max(hy) - min(hy)),
                confidence=min(0.85, len(houses) / 10.0),
                properties={
                    "zone_type": "urban",
                    "house_count": len(houses),
                    "city_names": [h.get("name", "") for h in houses if h.get("name")],
                },
                description=f"Urban zone: {len(houses)} buildings",
            ))

        return structures

    # ------------------------------------------------------------------
    # Points of Interest
    # ------------------------------------------------------------------

    def _detect_pois(
        self,
        tiles: List[Dict[str, Any]],
        items: Dict[str, int],
        houses: List[Dict[str, Any]],
        waypoints: List[Dict[str, Any]],
    ) -> List[DetectedStructure]:
        """Detecta puntos de interes."""
        structures: List[DetectedStructure] = []

        # Detectar POIs por items especiales
        for tile in tiles:
            tile_items = tile.get("items", []) + tile.get("all_items", [])
            for item in tile_items:
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                if isinstance(item_id, int) and item_id in self.POI_ITEM_IDS:
                    poi_type = self.POI_ITEM_IDS[item_id]
                    structures.append(DetectedStructure(
                        structure_type="poi",
                        name=f"{poi_type}_{item_id}",
                        bounds=(tile["x"], tile["y"], tile["x"], tile["y"]),
                        area=1,
                        confidence=0.9,
                        properties={"poi_type": poi_type, "item_id": item_id},
                        description=f"POI: {poi_type} at ({tile['x']},{tile['y']})",
                    ))

        # Waypoints como POIs
        for wp in waypoints:
            structures.append(DetectedStructure(
                structure_type="poi",
                name=f"waypoint_{wp.get('name', 'unknown')}",
                bounds=(wp["x"], wp["y"], wp["x"], wp["y"]),
                area=1,
                confidence=0.7,
                properties={
                    "poi_type": "waypoint",
                    "name": wp.get("name", ""),
                },
                description=f"Waypoint: {wp.get('name', '')}",
            ))

        # Temple como POI especial
        for house in houses:
            name = str(house.get("name", "")).lower()
            if "temple" in name:
                tx = house.get("temple_x", house.get("x", 0))
                ty = house.get("temple_y", house.get("y", 0))
                structures.append(DetectedStructure(
                    structure_type="poi",
                    name=f"temple_{house.get('id', 0)}",
                    bounds=(tx, ty, tx, ty),
                    area=1,
                    confidence=1.0,
                    properties={
                        "poi_type": "temple",
                        "temple_id": house.get("id", 0),
                    },
                    description=f"Temple at ({tx},{ty})",
                ))

        return structures

    # ------------------------------------------------------------------
    # Layout detection
    # ------------------------------------------------------------------

    def _detect_layout(
        self,
        tiles: List[Dict[str, Any]],
        width: int,
        height: int,
    ) -> DetectedStructure:
        """Detecta el tipo de layout general."""
        if not tiles:
            return DetectedStructure(
                structure_type="layout",
                name="layout",
                confidence=0.0,
                properties={"layout_type": "unknown"},
                description="Unknown layout",
            )

        # Analizar distribucion espacial
        xs = [t["x"] for t in tiles]
        ys = [t["y"] for t in tiles]

        x_span = max(xs) - min(xs)
        y_span = max(ys) - min(ys)

        # Calcular dispersion (std dev)
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        std_x = (sum((x - mean_x) ** 2 for x in xs) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in ys) / n) ** 0.5

        # Determinar tipo de layout
        if n < 10:
            layout_type = "sparse"
        elif std_x < x_span * 0.15 and std_y < y_span * 0.15:
            layout_type = "clustered"
        elif std_x > x_span * 0.4 and std_y > y_span * 0.4:
            layout_type = "organic"
        elif std_x < x_span * 0.2 or std_y < y_span * 0.2:
            layout_type = "linear"
        else:
            layout_type = "grid"

        confidence_map = {
            "grid": 0.8,
            "linear": 0.75,
            "organic": 0.7,
            "clustered": 0.85,
            "sparse": 0.9,
        }

        return DetectedStructure(
            structure_type="layout",
            name="layout",
            bounds=(min(xs), min(ys), max(xs), max(ys)),
            area=x_span * y_span,
            confidence=confidence_map.get(layout_type, 0.5),
            properties={
                "layout_type": layout_type,
                "x_span": x_span,
                "y_span": y_span,
                "std_dev_x": round(std_x, 2),
                "std_dev_y": round(std_y, 2),
                "tile_density": n / max(x_span * y_span, 1),
            },
            description=f"Layout: {layout_type} ({n} tiles, "
                        f"{x_span}x{y_span} area)",
        )

    # ------------------------------------------------------------------
    # Structural hierarchy
    # ------------------------------------------------------------------

    def _build_hierarchy(
        self, structures: List[DetectedStructure]
    ) -> DetectedStructure:
        """Construye la jerarquia estructural."""
        rooms = [s for s in structures if s.structure_type == "room"]
        corridors = [s for s in structures if s.structure_type == "corridor"]
        buildings = [s for s in structures if s.structure_type == "building"]
        zones = [s for s in structures if s.structure_type == "zone"]
        pois = [s for s in structures if s.structure_type == "poi"]

        return DetectedStructure(
            structure_type="hierarchy",
            name="structural_hierarchy",
            confidence=0.9,
            properties={
                "levels": {
                    "primary": len(buildings) + len(zones),
                    "secondary": len(rooms),
                    "tertiary": len(corridors) + len(pois),
                },
                "total_structures": len(structures),
                "summary": {
                    "rooms": len(rooms),
                    "corridors": len(corridors),
                    "buildings": len(buildings),
                    "zones": len(zones),
                    "pois": len(pois),
                },
            },
            description=f"Hierarchy: {len(buildings)} buildings, "
                        f"{len(rooms)} rooms, {len(corridors)} corridors, "
                        f"{len(pois)} POIs",
        )

    # ------------------------------------------------------------------
    # Detect from aggregate stats
    # ------------------------------------------------------------------

    def detect_aggregate(
        self,
        tiles_stats: Dict[str, int],
        items_stats: Dict[str, int],
        spawn_count: int,
        house_count: int,
        waypoint_count: int,
        map_size: Optional[Dict[str, int]] = None,
    ) -> List[DetectedStructure]:
        """
        Version agregada basada en estadisticas sin datos posicionales.

        Produce inferencias estructurales de alto nivel.
        """
        structures: List[DetectedStructure] = []

        width = map_size.get("width", 100) if map_size else 100
        height = map_size.get("height", 100) if map_size else 100
        total_tiles = sum(tiles_stats.values())
        area = width * height

        # Inferir layout tipo
        tile_density = total_tiles / max(area, 1)
        if tile_density > 0.8:
            layout_type = "dense"
        elif tile_density > 0.4:
            layout_type = "grid"
        elif tile_density > 0.15:
            layout_type = "organic"
        else:
            layout_type = "sparse"

        structures.append(DetectedStructure(
            structure_type="layout",
            name="layout",
            bounds=(0, 0, width, height),
            area=area,
            confidence=0.7,
            properties={
                "layout_type": layout_type,
                "tile_density": round(tile_density, 4),
                "total_tiles": total_tiles,
            },
            description=f"Layout: {layout_type}, density={tile_density:.3f}",
        ))

        # Inferir habitaciones
        unique_tiles = len(tiles_stats)
        if unique_tiles >= 3:
            estimated_rooms = max(1, unique_tiles // 3)
            structures.append(DetectedStructure(
                structure_type="room",
                name="estimated_rooms",
                confidence=0.5,
                properties={
                    "estimated_count": estimated_rooms,
                    "unique_grounds": unique_tiles,
                },
                description=f"Estimated {estimated_rooms} rooms from {unique_tiles} grounds",
            ))

        # Zonas
        if spawn_count > 0:
            structures.append(DetectedStructure(
                structure_type="zone",
                name="hunting_zone",
                confidence=min(0.7, spawn_count / 20.0),
                properties={
                    "zone_type": "hunting",
                    "spawn_count": spawn_count,
                },
                description=f"Hunting zone: {spawn_count} spawns",
            ))

        if house_count > 0:
            structures.append(DetectedStructure(
                structure_type="zone",
                name="urban_zone",
                confidence=min(0.7, house_count / 10.0),
                properties={
                    "zone_type": "urban",
                    "house_count": house_count,
                },
                description=f"Urban zone: {house_count} buildings",
            ))

        # Jerarquia
        structures.append(DetectedStructure(
            structure_type="hierarchy",
            name="structural_hierarchy",
            confidence=0.8,
            properties={
                "levels": {
                    "primary": house_count + (1 if spawn_count > 10 else 0),
                    "secondary": max(1, unique_tiles // 2),
                    "tertiary": waypoint_count + spawn_count,
                },
                "total_structures": len(structures),
                "summary": {
                    "rooms": max(1, unique_tiles // 3),
                    "corridors": 0,
                    "buildings": house_count,
                    "zones": (1 if spawn_count > 0 else 0) + (1 if house_count > 0 else 0),
                    "pois": waypoint_count,
                },
            },
            description=f"Hierarchy: {house_count} buildings, "
                        f"{waypoint_count} POIs",
        ))

        return structures

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_density(
        positions: List[Tuple[int, int]],
        cell_size: int = 10,
    ) -> List[List[Tuple[int, int]]]:
        """Agrupa posiciones por densidad usando grid hashing."""
        if not positions:
            return []

        # Grid hash
        grid: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        for pos in positions:
            cell = (pos[0] // cell_size, pos[1] // cell_size)
            grid[cell].append(pos)

        visited: Set[Tuple[int, int]] = set()
        clusters: List[List[Tuple[int, int]]] = []

        for pos in positions:
            if pos in visited:
                continue

            cluster: List[Tuple[int, int]] = []
            queue = [pos]
            visited.add(pos)

            while queue:
                current = queue.pop(0)
                cluster.append(current)

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
                            if dist <= cell_size:
                                visited.add(neighbor)
                                queue.append(neighbor)

            if cluster:
                clusters.append(cluster)

        return clusters

    @staticmethod
    def _are_adjacent(
        bounds1: Tuple[int, int, int, int],
        bounds2: Tuple[int, int, int, int],
        margin: int = 5,
    ) -> bool:
        """Determina si dos bounding boxes son adyacentes."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2

        # Expandir para detectar cercania
        x1_min -= margin
        y1_min -= margin
        x1_max += margin
        y1_max += margin

        # Verificar interseccion
        return not (
            x1_max < x2_min
            or x2_max < x1_min
            or y1_max < y2_min
            or y2_max < y1_min
        )

    @staticmethod
    def _classify_room_type(
        grounds: Set[int], bounds: Tuple[int, int, int, int]
    ) -> str:
        """Clasifica el tipo de habitacion por sus suelos."""
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        area = width * height

        # IDs de suelo por tipo
        temple_grounds = {415}  # polished_stone
        dungeon_grounds = {416}  # mossy_stone
        city_grounds = {396}  # yalahar_floor
        natural_grounds = {393}  # sandstone_floor

        if grounds & temple_grounds:
            return "temple_room"
        elif grounds & dungeon_grounds:
            return "dungeon_room"
        elif grounds & city_grounds:
            return "city_room"
        elif grounds & natural_grounds:
            return "natural_room"

        # Por tamano
        if area > 100:
            return "hall"
        elif area > 25:
            return "chamber"
        elif width > height * 3 or height > width * 3:
            return "corridor"
        else:
            return "room"
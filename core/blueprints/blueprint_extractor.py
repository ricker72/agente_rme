"""
HITO 13 â€” Blueprint Extractor: orquesta todo el pipeline de extraccion
de blueprints desde datos OTBM â†’ WorldModel â†’ Blueprint.

Pipeline completo:
    1. OTBM Importer: lee .otbm â†’ WorldModel dict
    2. Map Analyzer: extrae tiles, items, spawns, houses, waypoints
    3. Theme Classifier: clasifica el tema/estilo
    4. Pattern Detector: detecta patrones constructivos
    5. Structure Detector: detecta estructuras (rooms, corridors, buildings)
    6. Blueprint Builder: construye Blueprint objects con tiles
    7. Save: guarda automaticamente en data/blueprints/

Usage:
    extractor = BlueprintExtractor()
    bp = extractor.extract_from_otbm("output/issavi.otbm")
    # O desde WorldModel dict:
    bp = extractor.extract_from_world_dict(world_dict, source_name="issavi")
    # O desde analisis MapAnalysis:
    bp = extractor.extract_from_analysis(map_analysis)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from .theme_classifier import ThemeClassifier
from .pattern_detector import PatternDetector
from .structure_detector import StructureDetector


@dataclass
class ExtractionResult:
    """Resultado completo de la extraccion."""
    blueprint: Optional[Blueprint] = None
    success: bool = False
    theme: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    structures: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    saved_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "blueprint": self.blueprint.to_dict() if self.blueprint else None,
            "theme": self.theme,
            "patterns": self.patterns,
            "structures": self.structures,
            "stats": self.stats,
            "saved_path": self.saved_path,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class BlueprintExtractor:
    """
    Extrae Blueprints desde datos OTBM / WorldModel / MapAnalysis.

    Es el punto de entrada principal para el pipeline HITO 13:
        OTBM â†’ WorldModel â†’ Blueprint
    """

    def __init__(self, output_dir: str = "data/blueprints/"):
        """
        Args:
            output_dir: Directorio donde guardar los blueprints extraidos.
        """
        self.output_dir = Path(output_dir)
        self.theme_classifier = ThemeClassifier()
        self.pattern_detector = PatternDetector()
        self.structure_detector = StructureDetector()

    # ------------------------------------------------------------------
    # Metodos principales de extraccion
    # ------------------------------------------------------------------

    def extract_from_otbm(
        self,
        otbm_path: str,
        save: bool = True,
    ) -> ExtractionResult:
        """
        Extrae blueprint desde un archivo .otbm.

        Pipeline completo: OTBM â†’ WorldModel â†’ MapAnalysis â†’ Blueprint.

        Args:
            otbm_path: Ruta al archivo .otbm.
            save: Si True, guarda automaticamente en data/blueprints/.

        Returns:
            ExtractionResult con el blueprint extraido.
        """
        result = ExtractionResult()

        if not os.path.exists(otbm_path):
            result.errors.append(f"File not found: {otbm_path}")
            return result

        source_name = Path(otbm_path).stem

        try:
            # 1. Importar OTBM â†’ WorldModel dict
            world_dict = self._import_otbm(otbm_path)
            if not world_dict:
                result.errors.append(f"Failed to import OTBM: {otbm_path}")
                return result

            # 2. Extraer desde WorldModel dict
            return self.extract_from_world_dict(world_dict, source_name=source_name, save=save)

        except Exception as e:
            result.errors.append(f"Extraction error: {e}")
            return result

    def extract_from_world_dict(
        self,
        world_dict: Dict[str, Any],
        source_name: str = "unknown",
        save: bool = True,
    ) -> ExtractionResult:
        """
        Extrae blueprint desde un WorldModel dict.

        Args:
            world_dict: Dict en formato WorldModel (output de WorldBuilder o OTBMImporter).
            source_name: Nombre para el blueprint.
            save: Si True, guarda automaticamente.

        Returns:
            ExtractionResult con el blueprint extraido.
        """
        result = ExtractionResult()
        result.stats["source"] = source_name
        result.stats["timestamp"] = datetime.now().isoformat()

        # Validar que el world_dict tiene datos significativos
        tiles_raw = world_dict.get("tiles", [])
        spawns_raw = world_dict.get("spawns", [])
        cities_raw = world_dict.get("cities", [])
        waypoints_raw = world_dict.get("waypoints", [])

        if not world_dict or (not tiles_raw and not spawns_raw and not cities_raw and not waypoints_raw):
            result.errors.append("Empty or invalid world_dict: no tiles, spawns, cities, or waypoints found")
            return result

        try:
            width = world_dict.get("width", 0)
            height = world_dict.get("height", 0)
            description = world_dict.get("description", "")

            result.stats["tile_count"] = len(tiles_raw)
            result.stats["spawn_count"] = len(spawns_raw)
            result.stats["city_count"] = len(cities_raw)
            result.stats["waypoint_count"] = len(waypoints_raw)
            result.stats["map_size"] = {"width": width, "height": height}

            # 3. Analizar tiles e items (estadisticas agregadas)
            tile_stats, item_stats = self._aggregate_stats(tiles_raw)

            # Convertir cities a formato houses
            houses = self._cities_to_houses(cities_raw)

            # 4. Clasificar tema
            theme_result = self.theme_classifier.classify(
                tiles=tile_stats,
                items=item_stats,
                spawns=spawns_raw,
                houses=houses,
            )
            result.theme = theme_result

            # Metadatos extendidos
            metadata_dict = self.theme_classifier.classify_with_metadata(
                tiles=tile_stats,
                items=item_stats,
                spawns=spawns_raw,
                houses=houses,
            )

            # 5. Detectar patrones
            patterns = self.pattern_detector.detect(
                tiles=tiles_raw,
                items=item_stats,
                spawns=spawns_raw,
                map_size={"width": width, "height": height},
            )
            result.patterns = [p.to_dict() for p in patterns]

            # Patrones agregados (fallback si no hay posicionales)
            if not patterns and tile_stats:
                agg_patterns = self.pattern_detector.detect_aggregate(
                    tiles_stats=tile_stats,
                    items_stats=item_stats,
                    spawn_count=len(spawns_raw),
                    house_count=len(houses),
                    waypoint_count=len(waypoints_raw),
                )
                result.patterns = [p.to_dict() for p in agg_patterns]

            # 6. Detectar estructuras
            structures = self.structure_detector.detect(
                tiles=tiles_raw,
                items=item_stats,
                spawns=spawns_raw,
                houses=houses,
                waypoints=waypoints_raw,
                map_size={"width": width, "height": height},
            )
            result.structures = [s.to_dict() for s in structures]

            if not structures and tile_stats:
                agg_structures = self.structure_detector.detect_aggregate(
                    tiles_stats=tile_stats,
                    items_stats=item_stats,
                    spawn_count=len(spawns_raw),
                    house_count=len(houses),
                    waypoint_count=len(waypoints_raw),
                    map_size={"width": width, "height": height},
                )
                result.structures = [s.to_dict() for s in agg_structures]

            # 7. Construir Blueprint
            bp = self._build_blueprint(
                source_name=source_name,
                tiles_raw=tiles_raw,
                tile_stats=tile_stats,
                item_stats=item_stats,
                spawns=spawns_raw,
                houses=houses,
                waypoints=waypoints_raw,
                theme_result=theme_result,
                metadata_dict=metadata_dict,
                patterns=result.patterns,
                structures=result.structures,
                description=description,
                width=width,
                height=height,
            )
            result.blueprint = bp

            # 8. Guardar si se solicita
            if save and bp is not None:
                saved_path = self._save_blueprint(bp)
                result.saved_path = saved_path

            result.success = True

        except Exception as e:
            result.errors.append(f"Extraction error: {e}")

        return result

    def extract_from_analysis(
        self,
        analysis: Any,  # MapAnalysis
        save: bool = True,
    ) -> ExtractionResult:
        """
        Extrae blueprint desde un MapAnalysis object (de HITO 12).

        Args:
            analysis: MapAnalysis dataclass con los datos analizados.
            save: Si True, guarda automaticamente.

        Returns:
            ExtractionResult con el blueprint extraido.
        """
        result = ExtractionResult()

        try:
            source_name = Path(analysis.source).stem if hasattr(analysis, "source") else "analysis"
            result.stats["source"] = source_name
            result.stats["timestamp"] = datetime.now().isoformat()

            # Datos del analisis
            tile_stats = analysis.tiles if hasattr(analysis, "tiles") else {}
            item_stats = analysis.items if hasattr(analysis, "items") else {}
            houses = analysis.houses if hasattr(analysis, "houses") else []
            spawns = analysis.spawns if hasattr(analysis, "spawns") else []
            waypoints = analysis.waypoints if hasattr(analysis, "waypoints") else []
            map_size = analysis.map_size if hasattr(analysis, "map_size") else {"width": 100, "height": 100}

            result.stats["tile_count"] = sum(tile_stats.values()) if tile_stats else analysis.tile_count
            result.stats["spawn_count"] = len(spawns)
            result.stats["city_count"] = len(houses)
            result.stats["waypoint_count"] = len(waypoints)
            result.stats["map_size"] = map_size

            # Clasificar tema
            theme_result = self.theme_classifier.classify(
                tiles=tile_stats,
                items=item_stats,
                spawns=spawns,
                houses=houses,
            )
            result.theme = theme_result

            metadata_dict = self.theme_classifier.classify_with_metadata(
                tiles=tile_stats,
                items=item_stats,
                spawns=spawns,
                houses=houses,
            )

            # Patrones (modo agregado)
            patterns = self.pattern_detector.detect_aggregate(
                tiles_stats=tile_stats,
                items_stats=item_stats,
                spawn_count=len(spawns),
                house_count=len(houses),
                waypoint_count=len(waypoints),
            )
            result.patterns = [p.to_dict() for p in patterns]

            # Estructuras (modo agregado)
            structures = self.structure_detector.detect_aggregate(
                tiles_stats=tile_stats,
                items_stats=item_stats,
                spawn_count=len(spawns),
                house_count=len(houses),
                waypoint_count=len(waypoints),
                map_size=map_size,
            )
            result.structures = [s.to_dict() for s in structures]

            # Construir Blueprint
            bp = self._build_blueprint(
                source_name=source_name,
                tiles_raw=[],
                tile_stats=tile_stats,
                item_stats=item_stats,
                spawns=spawns,
                houses=houses,
                waypoints=waypoints,
                theme_result=theme_result,
                metadata_dict=metadata_dict,
                patterns=result.patterns,
                structures=result.structures,
                description="",
                width=map_size.get("width", 100),
                height=map_size.get("height", 100),
            )
            result.blueprint = bp

            if save and bp is not None:
                result.saved_path = self._save_blueprint(bp)

            result.success = True

        except Exception as e:
            result.errors.append(f"Analysis extraction error: {e}")

        return result

    # ------------------------------------------------------------------
    # OTBM Import helper
    # ------------------------------------------------------------------

    @staticmethod
    def _import_otbm(otbm_path: str) -> Optional[Dict[str, Any]]:
        """Importa un archivo .otbm usando el pipeline OTBMImporter."""
        try:
            from core.otbm.otbm_importer import OTBMImporter

            importer = OTBMImporter()
            import_result = importer.import_file(otbm_path)

            if import_result.get("success"):
                return import_result.get("world_dict")
            else:
                # Fallback: intentar con WorldBuilder directamente
                return BlueprintExtractor._import_otbm_fallback(otbm_path)

        except Exception as e:
            return BlueprintExtractor._import_otbm_fallback(otbm_path)
        except Exception:
            return None

    @staticmethod
    def _import_otbm_fallback(otbm_path: str) -> Optional[Dict[str, Any]]:
        """Fallback: usar OtbmParser + WorldBuilder directamente."""
        try:
            from core.otbm.otbm_parser import OtbmParser
            from core.otbm.world_builder import WorldBuilder

            data = Path(otbm_path).read_bytes()
            parser = OtbmParser()
            parsed = parser.parse(data)

            builder = WorldBuilder()
            return builder.build(parsed)
        except Exception as e:
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    # Ground ID to theme-friendly name mapping
    GROUND_ID_TO_NAME: Dict[int, str] = {
        393: "sandstone_floor",
        415: "polished_stone",
        416: "mossy_stone",
        396: "yalahar_floor",
        1053: "roshamuul_floor",
        1056: "roshamuul_stone",
        394: "sandstone",
        395: "dried_earth",
        417: "marble_floor",
        418: "cobblestone",
        419: "dungeon_floor",
        420: "cave_floor",
        421: "stone_floor",
        422: "rough_stone",
        423: "ice_floor",
        424: "snow_floor",
        425: "frozen_ground",
        426: "jungle_floor",
        427: "grass_floor",
        428: "mud_floor",
        429: "swamp_ground",
        430: "forest_floor",
        500: "yalahar_stone",
        501: "exotic_floor",
        502: "mosaic_floor",
        503: "patterned_stone",
    }

    @staticmethod
    def _aggregate_stats(
        tiles_raw: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Agrega estadisticas de tiles e items desde lista de tile dicts.

        Returns:
            (tile_stats, item_stats) donde cada uno es {name: count}.
        """
        from collections import Counter

        tile_counter = Counter()
        item_counter = Counter()

        for tile in tiles_raw:
            # Ground - intentar mapear ID a nombre tematico
            ground = tile.get("ground")
            if ground is not None:
                try:
                    gid = int(ground)
                    # Usar nombre tematico si existe, sino usar ID numerico
                    name = BlueprintExtractor.GROUND_ID_TO_NAME.get(gid, f"ground_{gid}")
                    tile_counter[name] += 1
                except (ValueError, TypeError):
                    tile_counter[f"ground_{ground}"] += 1

            # Items
            for item in tile.get("items", []) + tile.get("all_items", []):
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                if isinstance(item_id, int):
                    item_counter[f"item_{item_id}"] += 1
                else:
                    item_counter[f"item_{item_id}"] += 1

        return dict(tile_counter), dict(item_counter)

    @staticmethod
    def _cities_to_houses(cities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convierte cities/towns a formato houses."""
        houses = []
        for city in cities:
            houses.append({
                "id": city.get("town_id", 0),
                "name": city.get("name", ""),
                "temple_x": city.get("temple_x", city.get("x", 0)),
                "temple_y": city.get("temple_y", city.get("y", 0)),
                "temple_z": city.get("temple_z", city.get("z", 0)),
            })
        return houses

    # ------------------------------------------------------------------
    # Blueprint builder
    # ------------------------------------------------------------------

    def _build_blueprint(
        self,
        source_name: str,
        tiles_raw: List[Dict[str, Any]],
        tile_stats: Dict[str, int],
        item_stats: Dict[str, int],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
        waypoints: List[Dict[str, Any]],
        theme_result: Dict[str, Any],
        metadata_dict: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        structures: List[Dict[str, Any]],
        description: str,
        width: int,
        height: int,
    ) -> Blueprint:
        """
        Construye un Blueprint object a partir de todos los datos extraidos.

        Args:
            source_name: Nombre de la fuente (archivo).
            tiles_raw: Lista de tiles posicionales.
            tile_stats: Estadisticas de tiles {name: count}.
            item_stats: Estadisticas de items {key: count}.
            spawns: Lista de spawns.
            houses: Lista de houses.
            waypoints: Lista de waypoints.
            theme_result: Resultado del ThemeClassifier.
            metadata_dict: Metadatos del ThemeClassifier.
            patterns: Patrones detectados.
            structures: Estructuras detectadas.
            description: Descripcion del mapa.
            width: Ancho del mapa.
            height: Alto del mapa.

        Returns:
            Blueprint instance.
        """
        # Nombre del blueprint
        name = source_name or "unnamed"
        theme = theme_result.get("primary_theme", "generic")
        bp_name = f"{name}_{theme}"

        # Categoria
        category = self._determine_category(
            theme_result=theme_result,
            houses=houses,
            spawns=spawns,
            waypoints=waypoints,
        )

        # Tiles del blueprint (si hay tiles posicionales)
        bp_tiles: List[BlueprintTile] = []
        for tile in tiles_raw[:5000]:  # Limitar a 5000 tiles para rendimiento
            ground = tile.get("ground", 0)
            if ground is not None:
                try:
                    ground_int = int(ground)
                except (ValueError, TypeError):
                    ground_int = 0
            else:
                ground_int = 0

            # Primer item significativo
            items = tile.get("items", [])
            item_id = None
            if items:
                first = items[0]
                item_id = first.get("item_id", first) if isinstance(first, dict) else first

            # Spawn en este tile
            spawn = None
            for sp in spawns:
                if sp.get("x") == tile.get("x") and sp.get("y") == tile.get("y"):
                    spawn = {"monster": sp.get("monster", "unknown")}
                    break

            bp_tiles.append(BlueprintTile(
                x=tile.get("x", 0),
                y=tile.get("y", 0),
                ground=ground_int,
                item=item_id if isinstance(item_id, int) else None,
                spawn=spawn,
            ))

        # Entry point: primer waypoint o primer spawn o centro
        entry = self._determine_entry(waypoints, spawns, houses, width, height)

        # Size
        size = (width, height) if width > 0 and height > 0 else (100, 100)

        # Top grounds (para modo descriptivo)
        top_grounds = sorted(
            tile_stats.items(), key=lambda x: x[1], reverse=True
        )[:5]
        grounds = [int(k.replace("ground_", "")) for k, _ in top_grounds
                   if k.replace("ground_", "").isdigit()]

        # Top items (muros/items)
        wall_ids = {101, 102, 103, 108, 109, 1000, 1001, 2100, 2101}
        walls_items: List[int] = []
        decorations: List[int] = []
        for item_key, count in sorted(item_stats.items(), key=lambda x: x[1], reverse=True):
            try:
                iid = int(item_key.replace("item_", ""))
            except (ValueError, AttributeError):
                continue
            if iid in wall_ids:
                if len(walls_items) < 10:
                    walls_items.append(iid)
            else:
                if len(decorations) < 15:
                    decorations.append(iid)

        # Metadata
        metadata = BlueprintMetadata(
            style=metadata_dict.get("style", theme),
            era=metadata_dict.get("era", "modern"),
            difficulty=metadata_dict.get("difficulty", "safe"),
            tags=metadata_dict.get("tags", [theme]),
            capacity=metadata_dict.get("capacity", "medium"),
            hybrid=metadata_dict.get("hybrid", False),
        )

        return Blueprint(
            name=bp_name,
            theme=theme,
            category=category,
            version="1.0.0",
            size=size,
            entry=entry,
            description=description or f"Blueprint extracted from {source_name}"
                        f" ({len(tiles_raw)} tiles, {len(spawns)} spawns, "
                        f"{len(houses)} houses)",
            tiles=bp_tiles,
            rooms=self._extract_room_dicts(structures),
            features=self._extract_feature_dicts(patterns, structures),
            zones=self._extract_zone_dicts(structures, spawns, houses),
            grounds=grounds,
            walls_items=walls_items,
            decorations=decorations,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Helper methods for blueprint construction
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_category(
        theme_result: Dict[str, Any],
        houses: List[Dict[str, Any]],
        spawns: List[Dict[str, Any]],
        waypoints: List[Dict[str, Any]],
    ) -> str:
        """Determina la categoria del blueprint."""
        theme = theme_result.get("primary_theme", "generic")

        if theme == "temple":
            return "temple"
        elif theme == "dungeon":
            return "dungeon"
        elif theme in ("city", "yalahar"):
            return "city"
        elif theme in ("issavi", "roshamuul"):
            if houses:
                return "city"
            elif spawns:
                return "hunting"
            else:
                return "dungeon"
        elif theme == "hunt":
            return "hunting"
        elif theme in ("jungle", "ice"):
            return "wilderness"
        else:
            # Fallback heuristico
            if len(houses) >= 3:
                return "city"
            elif len(spawns) > 10:
                return "hunting"
            elif len(waypoints) > 5:
                return "dungeon"
            else:
                return "unknown"

    @staticmethod
    def _determine_entry(
        waypoints: List[Dict[str, Any]],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
        width: int,
        height: int,
    ) -> Optional[Tuple[int, int]]:
        """Determina el punto de entrada del blueprint."""
        # Prioridad: primer waypoint > primer temple > centro del mapa
        if waypoints:
            w = waypoints[0]
            return (w.get("x", 0), w.get("y", 0))

        # Buscar temple
        for house in houses:
            name = str(house.get("name", "")).lower()
            if "temple" in name:
                return (
                    house.get("temple_x", house.get("x", 0)),
                    house.get("temple_y", house.get("y", 0)),
                )

        # Primer spawn como referencia
        if spawns:
            s = spawns[0]
            return (s.get("x", 0), s.get("y", 0))

        # Centro del mapa
        if width > 0 and height > 0:
            return (width // 2, height // 2)

        return None

    @staticmethod
    def _extract_room_dicts(structures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrae rooms desde estructuras detectadas."""
        rooms = []
        for s in structures:
            if s.get("structure_type") == "room":
                props = s.get("properties", {})
                bounds = s.get("bounds", [0, 0, 0, 0])
                rooms.append({
                    "name": s.get("name", "room"),
                    "bounds": bounds,
                    "area": s.get("area", 0),
                    "type": props.get("room_type", "room"),
                    "tile_count": props.get("tile_count", 0),
                })
            elif s.get("structure_type") == "building":
                # Extraer sub-rooms del building
                for sub in s.get("sub_structures", []):
                    if sub.get("structure_type") == "room":
                        props = sub.get("properties", {})
                        bounds = sub.get("bounds", [0, 0, 0, 0])
                        rooms.append({
                            "name": f"{s.get('name', 'bld')}_{sub.get('name', 'r')}",
                            "bounds": bounds,
                            "area": sub.get("area", 0),
                            "type": props.get("room_type", "room"),
                            "tile_count": props.get("tile_count", 0),
                        })
        return rooms

    @staticmethod
    def _extract_feature_dicts(
        patterns: List[Dict[str, Any]],
        structures: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extrae features desde patrones y estructuras."""
        features = []
        for p in patterns:
            ptype = p.get("pattern_type", "unknown")
            if ptype not in ("room", "building", "zone"):
                features.append({
                    "type": ptype,
                    "bounds": p.get("bounds", [0, 0, 0, 0]),
                    "confidence": p.get("confidence", 0),
                    "description": p.get("description", ""),
                })
        return features

    @staticmethod
    def _extract_zone_dicts(
        structures: List[Dict[str, Any]],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extrae zonas desde estructuras y datos raw."""
        zones = []
        for s in structures:
            if s.get("structure_type") == "zone":
                props = s.get("properties", {})
                zones.append({
                    "name": s.get("name", "zone"),
                    "type": props.get("zone_type", "unknown"),
                    "bounds": s.get("bounds", [0, 0, 0, 0]),
                    "confidence": s.get("confidence", 0),
                    "description": s.get("description", ""),
                })
        return zones

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def _save_blueprint(self, bp: Blueprint) -> str:
        """
        Guarda un blueprint en data/blueprints/.

        Args:
            bp: Blueprint a guardar.

        Returns:
            Ruta del archivo guardado.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{bp.name}.json"
        filepath = self.output_dir / filename

        data = bp.to_dict()
        # Anadir metadatos de extraccion
        data["_extraction"] = {
            "timestamp": datetime.now().isoformat(),
            "tile_count": len(bp.tiles),
            "category": bp.category,
            "theme": bp.theme,
        }

        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return str(filepath)

    def load_blueprint(self, name: str) -> Optional[Blueprint]:
        """
        Carga un blueprint previamente guardado.

        Args:
            name: Nombre del blueprint (sin extension).

        Returns:
            Blueprint instance o None.
        """
        filepath = self.output_dir / f"{name}.json"
        if not filepath.exists():
            return None

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return Blueprint.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            return None

    def list_blueprints(self) -> List[str]:
        """Lista todos los blueprints guardados."""
        if not self.output_dir.exists():
            return []

        return sorted([
            f.stem for f in self.output_dir.glob("*.json")
            if f.stem != "__init__"
        ])

    # ------------------------------------------------------------------
    # Batch extraction
    # ------------------------------------------------------------------

    def extract_batch(
        self,
        otbm_paths: List[str],
        save: bool = True,
    ) -> List[ExtractionResult]:
        """
        Extrae blueprints de multiples archivos OTBM.

        Args:
            otbm_paths: Lista de rutas a archivos .otbm.
            save: Si True, guarda automaticamente.

        Returns:
            Lista de ExtractionResult.
        """
        results = []
        for path in otbm_paths:
            result = self.extract_from_otbm(path, save=save)
            results.append(result)
        return results

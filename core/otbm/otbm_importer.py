"""
OTBM Importer — reads .otbm files and converts them to WorldModel.

Entry point for importing OTBM maps into the RME Agent system.

Pipeline:
    .otbm file
    -> OtbmParser.parse(bytes) -> raw parsed tree
    -> WorldBuilder.build(parsed) -> WorldModel-compatible dict
    -> WorldBuilder.to_worldmodel(parsed) -> WorldModel instance

Usage:
    importer = OTBMImporter()
    world_model = importer.import_file("map.otbm")
    # world_model is a fully populated WorldModel with tiles, spawns, etc.

Statistics:
    report = importer.import_file("map.otbm")
    print(report["stats"]["tiles"])  # number of tiles imported
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .otbm_parser import OtbmParser, OtbmParseError
from .node_decoder import NodeDecoder, NodeDecodeError
from .tile_decoder import TileDecoder
from .item_decoder import ItemDecoder
from .world_builder import WorldBuilder, WorldBuildError
from .otbm_validator import OtbmValidator


class OTBMImporter:
    """
    Main importer for converting .otbm files into WorldModel instances.

    Provides:
        - import_file(path) -> dict with WorldModel + stats
        - import_bytes(data) -> dict with WorldModel + stats
        - to_worldmodel(path) -> WorldModel instance
        - get_preview(path) -> summary of map contents
    """

    def __init__(self, validate: bool = True):
        """
        Args:
            validate: If True, run validator before parsing.
        """
        self._parser = OtbmParser()
        self._builder = WorldBuilder()
        self._validator = OtbmValidator() if validate else None
        self._node_decoder = NodeDecoder()
        self._tile_decoder = TileDecoder()
        self._item_decoder = ItemDecoder()

    # ------------------------------------------------------------------
    # Main import methods
    # ------------------------------------------------------------------

    def import_file(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Import an .otbm file and return a structured result.

        Args:
            file_path: Path to .otbm file.

        Returns:
            dict with keys:
                - "success": bool
                - "world_model": WorldModel instance (or None on failure)
                - "world_dict": WorldModel-compatible dict
                - "stats": dict of import statistics
                - "map_info": dict of map metadata
                - "errors": list of error messages (if any)
                - "warnings": list of warning messages (if any)
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "stats": {},
                "map_info": {},
            }

        try:
            data = path.read_bytes()
            return self.import_bytes(data, source=str(file_path))
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": {},
                "map_info": {},
            }

    def import_bytes(
        self, data: bytes, source: str = "bytes"
    ) -> Dict[str, Any]:
        """
        Import OTBM data from bytes.

        Args:
            data: Raw .otbm bytes.
            source: Optional source description (for error messages).

        Returns:
            dict with structured result (same keys as import_file).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Validate
        if self._validator:
            try:
                validation = self._validator.validate(data)
                if validation.status == "failure":
                    return {
                        "success": False,
                        "error": f"Validation failed: {validation.errors}",
                        "stats": {},
                        "map_info": {},
                    }
                if validation.warnings:
                    warnings.extend(validation.warnings)
            except Exception as e:
                errors.append(f"Validation error: {e}")

        # Parse
        try:
            parsed = self._parser.parse(data)
        except OtbmParseError as e:
            return {
                "success": False,
                "error": f"Parse error: {e}",
                "stats": {},
                "map_info": {},
            }

        # Build
        try:
            world_dict = self._builder.build(parsed)
            world_model = self._builder.to_worldmodel(parsed)
        except WorldBuildError as e:
            return {
                "success": False,
                "error": f"Build error: {e}",
                "stats": {},
                "map_info": {},
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected build error: {e}",
                "stats": {},
                "map_info": {},
            }

        # Extract map info
        map_info = {
            "version": world_dict.get("version", 0),
            "width": world_dict.get("width", 0),
            "height": world_dict.get("height", 0),
            "item_major": world_dict.get("item_major", 3),
            "item_minor": world_dict.get("item_minor", 57),
            "description": world_dict.get("description", ""),
        }

        # Compute stats
        stats = {
            "tiles": world_dict.get("tile_count", 0),
            "spawns": world_dict.get("spawn_count", 0),
            "cities": world_dict.get("city_count", 0),
            "waypoints": world_dict.get("waypoint_count", 0),
            "file_size": len(data),
            "source": source,
        }

        return {
            "success": True,
            "world_model": world_model,
            "world_dict": world_dict,
            "stats": stats,
            "map_info": map_info,
            "errors": errors,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def to_worldmodel(self, file_path: str | Path) -> Any:
        """
        Import an .otbm file and return a WorldModel instance directly.

        Args:
            file_path: Path to .otbm file.

        Returns:
            WorldModel instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            OtbmParseError: If parsing fails.
            WorldBuildError: If building the WorldModel fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"OTBM file not found: {file_path}")

        data = path.read_bytes()
        parsed = self._parser.parse(data)
        return self._builder.to_worldmodel(parsed)

    def to_worldmodel_from_bytes(self, data: bytes) -> Any:
        """
        Import OTBM from bytes and return a WorldModel instance.

        Args:
            data: Raw .otbm bytes.

        Returns:
            WorldModel instance.

        Raises:
            OtbmParseError: If parsing fails.
        """
        parsed = self._parser.parse(data)
        return self._builder.to_worldmodel(parsed)

    def get_preview(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Get a summary preview of an OTBM map without full import.

        Args:
            file_path: Path to .otbm file.

        Returns:
            dict with preview info: version, dimensions, tile/spawn/city/waypoint counts.
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        data = path.read_bytes()
        return self.get_preview_from_bytes(data)

    def get_preview_from_bytes(self, data: bytes) -> Dict[str, Any]:
        """
        Get a summary preview of OTBM data without full import.

        Args:
            data: Raw .otbm bytes.

        Returns:
            dict with preview info.
        """
        try:
            parsed = self._parser.parse(data)
            root = parsed.get("root", {})

            preview = {
                "valid": True,
                "version": root.get("version", 0),
                "width": root.get("width", 0),
                "height": root.get("height", 0),
                "item_major": root.get("item_major", 3),
                "item_minor": root.get("item_minor", 57),
                "file_size": len(data),
            }

            # Count nodes
            decoded_root = self._node_decoder.decode_root(root)

            # Tile areas
            tile_areas = decoded_root.get("tile_areas", [])
            preview["tile_areas"] = len(tile_areas)

            # Estimate tiles
            tile_count = 0
            for area_node in tile_areas:
                try:
                    area_decoded = self._node_decoder.decode_tile_area(area_node)
                    tile_count += len(area_decoded.get("tiles", []))
                except Exception:
                    pass
            preview["tiles"] = tile_count

            # Spawns
            spawns_node = decoded_root.get("spawns")
            spawn_count = 0
            if spawns_node:
                try:
                    spawns_decoded = self._node_decoder.decode_spawns(spawns_node)
                    for area in spawns_decoded.get("spawn_areas", []):
                        spawn_count += len(area.get("monsters", []))
                except Exception:
                    pass
            preview["spawns"] = spawn_count

            # Towns
            towns_node = decoded_root.get("towns")
            town_count = 0
            if towns_node:
                try:
                    towns_decoded = self._node_decoder.decode_towns(towns_node)
                    town_count = len(towns_decoded.get("towns", []))
                except Exception:
                    pass
            preview["towns"] = town_count

            # Waypoints
            wp_node = decoded_root.get("waypoints")
            wp_count = 0
            if wp_node:
                try:
                    wp_decoded = self._node_decoder.decode_waypoints(wp_node)
                    wp_count = len(wp_decoded.get("waypoints", []))
                except Exception:
                    pass
            preview["waypoints"] = wp_count

            return preview

        except OtbmParseError as e:
            return {"valid": False, "error": str(e), "file_size": len(data)}

    # ------------------------------------------------------------------
    # Round trip: import then re-export
    # ------------------------------------------------------------------

    def round_trip(
        self, file_path: str | Path, output_path: Optional[str | Path] = None
    ) -> Dict[str, Any]:
        """
        Perform a full round trip: import OTBM -> WorldModel -> export OTBM.

        This verifies that the import/export pipeline is lossless for the
        structural data (tiles, spawns, towns, waypoints).

        Args:
            file_path: Source .otbm file to import.
            output_path: Optional path to write the re-exported .otbm file.

        Returns:
            dict with round trip results:
                - "import_success": bool
                - "export_success": bool
                - "import_stats": dict
                - "export_stats": dict
                - "original_size": int
                - "exported_size": int
                - "tiles_match": bool (count only)
                - "spawns_match": bool (count only)
        """
        from core.otbm.otbm_serializer import OtbmSerializer

        # Import
        source_data = Path(file_path).read_bytes()
        import_result = self.import_bytes(source_data)

        if not import_result.get("success"):
            return {
                "import_success": False,
                "error": import_result.get("error", "Import failed"),
            }

        world_model = import_result.get("world_model")

        # Export
        serializer = OtbmSerializer()
        try:
            exported_data = serializer.serialize(world_model)
            export_success = True
        except Exception as e:
            export_success = False
            exported_data = b""
            export_error = str(e)

        result = {
            "import_success": True,
            "export_success": export_success,
            "import_stats": import_result.get("stats", {}),
            "original_size": len(source_data),
            "exported_size": len(exported_data) if exported_data else 0,
            "tiles_match": (
                import_result.get("stats", {}).get("tiles", 0) ==
                self._count_tiles_in_bytes(exported_data)
            ) if exported_data else False,
            "spawns_match": (
                import_result.get("stats", {}).get("spawns", 0) ==
                self._count_spawns_in_bytes(exported_data)
            ) if exported_data else False,
        }

        if not export_success:
            result["export_error"] = export_error

        # Optionally write output
        if output_path and exported_data:
            Path(output_path).write_bytes(exported_data)
            result["output_path"] = str(output_path)

        return result

    @staticmethod
    def _count_tiles_in_bytes(data: bytes) -> int:
        """Quick count of TILE nodes in exported bytes."""
        if not data:
            return 0
        from .node_encoder import OTBM_NODE_TILE
        count = 0
        offset = 0
        while offset < len(data):
            # Search for TILE node marker
            idx = data.find(bytes([OTBM_NODE_TILE]), offset)
            if idx == -1:
                break
            count += 1
            offset = idx + 1
        return count

    @staticmethod
    def _count_spawns_in_bytes(data: bytes) -> int:
        """Quick count of MONSTER nodes in exported bytes."""
        if not data:
            return 0
        from .node_encoder import OTBM_NODE_MONSTER
        count = 0
        offset = 0
        while offset < len(data):
            idx = data.find(bytes([OTBM_NODE_MONSTER]), offset)
            if idx == -1:
                break
            count += 1
            offset = idx + 1
        return count
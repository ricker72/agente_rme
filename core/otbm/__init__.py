from __future__ import annotations

from .node_encoder import (
    NodeEncoder,
    OTBM_NODE_ROOT,
    OTBM_NODE_MAP_DATA,
    OTBM_NODE_TILE_AREA,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_TILE_SQUARE,
    OTBM_NODE_SPAWNS,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_MONSTER,
    OTBM_NODE_TOWNS,
    OTBM_NODE_TOWN,
    OTBM_NODE_HOUSETILE,
    OTBM_NODE_WAYPOINTS,
    OTBM_NODE_WAYPOINT,
    ATTR_DESCRIPTION,
    ATTR_EXT_HOUSE_FILE,
    ATTR_EXT_SPAWN_FILE,
    ATTR_TILE_FLAGS,
    ATTR_ITEM,
    ATTR_COUNT,
    ATTR_ACTION_ID,
    ATTR_UNIQUE_ID,
    ATTR_TEXT,
    ATTR_DESC,
    ATTR_EXT_FILE,
    ATTR_DURATION,
    ATTR_DECAYING_STATE,
    ATTR_WRITTEN_DATE,
    ATTR_WRITTEN_BY,
    ATTR_SLEEPERGUID,
    ATTR_SLEEPSTART,
    ATTR_CHARGES,
    ATTR_SUBTYPE,
    TILESTATE_NONE,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    TILESTATE_PVPZONE,
    TILESTATE_REFRESH,
    TILESTATE_TRASHED,
    DEFAULT_OTBM_VERSION,
    DEFAULT_ITEM_MAJOR_VERSION,
    DEFAULT_ITEM_MINOR_VERSION,
)
from .tile_encoder import (
    TileEncoder,
    GROUND_IDS,
    WALL_IDS,
    DECORATION_IDS,
)
from .item_encoder import ItemEncoder
from .spawn_encoder import SpawnEncoder
from .house_encoder import HouseEncoder
from .waypoint_encoder import WaypointEncoder
from .otbm_reader import OtbmReader
from .otbm_writer import OtbmWriter, WorldModelToOTBM
from .otbm_serializer import OtbmSerializer
from .otbm_deserializer import OtbmDeserializer
from .otbm_validator import OtbmValidator, OtbmValidationResult
from .byte_validator import (
    ByteValidator,
    validate_byte,
    validate_word,
    validate_dword,
)
from .otbm_templates import OtbmTemplateGenerator
from .otbm_exporter import OTBMExporter

# HITO 11: Importer pipeline
from .otbm_parser import OtbmParser, OtbmParseError, OTBM_MAGIC
from .node_decoder import NodeDecoder, NodeDecodeError
from .tile_decoder import TileDecoder
from .item_decoder import ItemDecoder
from .world_builder import WorldBuilder, WorldBuildError
from .otbm_importer import OTBMImporter

__all__ = [
    # Encoders
    "NodeEncoder",
    "TileEncoder",
    "ItemEncoder",
    "SpawnEncoder",
    "HouseEncoder",
    "WaypointEncoder",
    # Data maps
    "GROUND_IDS",
    "WALL_IDS",
    "DECORATION_IDS",
    # I/O
    "OtbmReader",
    "OtbmWriter",
    "WorldModelToOTBM",
    "OtbmSerializer",
    "OtbmDeserializer",
    "OtbmValidator",
    "OtbmValidationResult",
    "ByteValidator",
    "validate_byte",
    "validate_word",
    "validate_dword",
    "OtbmTemplateGenerator",
    # Exporter facade
    "OTBMExporter",
    # HITO 11: Importer pipeline
    "OtbmParser",
    "OtbmParseError",
    "OTBM_MAGIC",
    "NodeDecoder",
    "NodeDecodeError",
    "TileDecoder",
    "ItemDecoder",
    "WorldBuilder",
    "WorldBuildError",
    "OTBMImporter",
    # Node type constants
    "OTBM_NODE_ROOT",
    "OTBM_NODE_MAP_DATA",
    "OTBM_NODE_TILE_AREA",
    "OTBM_NODE_TILE",
    "OTBM_NODE_ITEM",
    "OTBM_NODE_TILE_SQUARE",
    "OTBM_NODE_SPAWNS",
    "OTBM_NODE_SPAWN_AREA",
    "OTBM_NODE_MONSTER",
    "OTBM_NODE_TOWNS",
    "OTBM_NODE_TOWN",
    "OTBM_NODE_HOUSETILE",
    "OTBM_NODE_WAYPOINTS",
    "OTBM_NODE_WAYPOINT",
    # Attribute constants
    "ATTR_DESCRIPTION",
    "ATTR_EXT_HOUSE_FILE",
    "ATTR_EXT_SPAWN_FILE",
    "ATTR_TILE_FLAGS",
    "ATTR_ITEM",
    "ATTR_COUNT",
    "ATTR_ACTION_ID",
    "ATTR_UNIQUE_ID",
    "ATTR_TEXT",
    "ATTR_DESC",
    "ATTR_EXT_FILE",
    "ATTR_DURATION",
    "ATTR_DECAYING_STATE",
    "ATTR_WRITTEN_DATE",
    "ATTR_WRITTEN_BY",
    "ATTR_SLEEPERGUID",
    "ATTR_SLEEPSTART",
    "ATTR_CHARGES",
    "ATTR_SUBTYPE",
    # Tile state constants
    "TILESTATE_NONE",
    "TILESTATE_PROTECTIONZONE",
    "TILESTATE_NOPVPZONE",
    "TILESTATE_NOLOGOUT",
    "TILESTATE_PVPZONE",
    "TILESTATE_REFRESH",
    "TILESTATE_TRASHED",
    # Defaults
    "DEFAULT_OTBM_VERSION",
    "DEFAULT_ITEM_MAJOR_VERSION",
    "DEFAULT_ITEM_MINOR_VERSION",
]

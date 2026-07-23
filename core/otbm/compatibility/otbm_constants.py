"""
OTBM Constants — Canonical node types from Canary Map Editor v4.0.

These constants define the exact node types used by Remere's Map Editor
as documented in iomap_otbm.h from the Canary source code.

MANDATORY OTBM NODE CONSTANTS (from Canary):
OTBM_ROOTV1       = 1
OTBM_MAP_DATA     = 2
OTBM_ITEM_DEF     = 3
OTBM_TILE_AREA    = 4
OTBM_TILE         = 5
OTBM_ITEM         = 6
OTBM_SPAWNS       = 9
OTBM_SPAWN_AREA   = 10
OTBM_MONSTER      = 11
OTBM_TOWNS        = 12
OTBM_TOWN         = 13
OTBM_HOUSETILE    = 14
OTBM_WAYPOINTS    = 15
OTBM_WAYPOINT     = 16
"""

# ============================================================
# OTBM Node Types — Canonical Canary/RME Format
# ============================================================
# These are the EXACT node type identifiers used in .otbm files
# by Remere's Map Editor (Canary v4.0)
# ============================================================

# Root and map header nodes
OTBM_ROOTV1 = 0x01
OTBM_MAP_DATA = 0x02
OTBM_ITEM_DEF = 0x03  # Not implemented in modern RME

# Tile structure nodes
OTBM_TILE_AREA = 0x04
OTBM_TILE = 0x05
OTBM_ITEM = 0x06
OTBM_TILE_SQUARE = 0x07  # Deprecated / unused in modern TFS
OTBM_TILE_REF = 0x08  # Deprecated / unused

# Spawn nodes
OTBM_SPAWNS = 0x09
OTBM_SPAWN_AREA = 0x0A
OTBM_MONSTER = 0x0B

# Town nodes
OTBM_TOWNS = 0x0C
OTBM_TOWN = 0x0D

# House nodes
OTBM_HOUSETILE = 0x0E

# Waypoint nodes
OTBM_WAYPOINTS = 0x0F
OTBM_WAYPOINT = 0x10

# Extended nodes (not commonly used in basic maps)
OTBM_SPAWN_NPC_AREA = 0x11
OTBM_SPAWNS_NPC = 0x12
OTBM_TILE_ZONE = 0x13

# ============================================================
# OTBM Attribute Types (used inside item nodes)
# ============================================================
OTBM_ATTR_DESCRIPTION = 0x01
OTBM_ATTR_EXT_FILE = 0x02
OTBM_ATTR_TILE_FLAGS = 0x03
OTBM_ATTR_ACTION_ID = 0x04
OTBM_ATTR_UNIQUE_ID = 0x05
OTBM_ATTR_TEXT = 0x06
OTBM_ATTR_DESC = 0x07
OTBM_ATTR_TELE_DEST = 0x08
OTBM_ATTR_ITEM = 0x09
OTBM_ATTR_DEPOT_ID = 0x0A
OTBM_ATTR_EXT_SPAWN_MONSTER_FILE = 0x0B
OTBM_ATTR_RUNE_CHARGES = 0x0C
OTBM_ATTR_EXT_HOUSE_FILE = 0x0D
OTBM_ATTR_HOUSEDOORID = 0x0E
OTBM_ATTR_COUNT = 0x0F
OTBM_ATTR_SUBTYPE = 0x13  # Alternative to COUNT for some items
OTBM_ATTR_DURATION = 0x10
OTBM_ATTR_DECAYING_STATE = 0x11
OTBM_ATTR_WRITTENDATE = 0x12
OTBM_ATTR_WRITTENBY = 0x13
OTBM_ATTR_SLEEPERGUID = 0x14
OTBM_ATTR_SLEEPSTART = 0x15
OTBM_ATTR_CHARGES = 0x16
OTBM_ATTR_EXT_SPAWN_NPC_FILE = 0x17
OTBM_ATTR_EXT_ZONE_FILE = 0x18
OTBM_ATTR_ATTRIBUTE_MAP = 0x80

# ============================================================
# Tile Flags (bitmask)
# ============================================================
TILESTATE_NONE = 0x0000
TILESTATE_PROTECTIONZONE = 0x0001
TILESTATE_NOPVPZONE = 0x0002
TILESTATE_NOLOGOUT = 0x0004
TILESTATE_PVPZONE = 0x0008
TILESTATE_REFRESH = 0x0010
TILESTATE_TRASHED = 0x0020

# ============================================================
# Map Header Constants
# ============================================================
OTBM_IDENTIFIER = b"\x00\x00\x00\x00"
OTBM_NAMED_IDENTIFIER = b"OTBM"
OTBM_ACCEPTED_IDENTIFIERS = (OTBM_IDENTIFIER, OTBM_NAMED_IDENTIFIER)
DEFAULT_OTBM_VERSION = 1  # Canary uses version 1
DEFAULT_ITEM_MAJOR_VERSION = 3
DEFAULT_ITEM_MINOR_VERSION = 57

# ============================================================
# Node Type Mapping — Agente RME → Canary/RME
# ============================================================
# This mapping shows the discrepancy between current Agente RME
# node constants and the canonical Canary/RME constants
# ============================================================

# Current Agente RME node constants (from node_encoder.py)
AGENTE_OTBM_NODE_ROOT = 0x00
AGENTE_OTBM_NODE_MAP_DATA = 0x01
AGENTE_OTBM_NODE_TILE_AREA = 0x02
AGENTE_OTBM_NODE_TILE = 0x03
AGENTE_OTBM_NODE_ITEM = 0x04
AGENTE_OTBM_NODE_TILE_SQUARE = 0x05
AGENTE_OTBM_NODE_SPAWNS = 0x06
AGENTE_OTBM_NODE_SPAWN_AREA = 0x07
AGENTE_OTBM_NODE_MONSTER = 0x08
AGENTE_OTBM_NODE_TOWNS = 0x09
AGENTE_OTBM_NODE_TOWN = 0x0A
AGENTE_OTBM_NODE_HOUSETILE = 0x0B
AGENTE_OTBM_NODE_WAYPOINTS = 0x0C
AGENTE_OTBM_NODE_WAYPOINT = 0x0D

# Mapping from Agente to Canary constants
AGENTE_TO_CANARY_NODE_MAP = {
    AGENTE_OTBM_NODE_ROOT: OTBM_ROOTV1,
    AGENTE_OTBM_NODE_MAP_DATA: OTBM_MAP_DATA,
    AGENTE_OTBM_NODE_TILE_AREA: OTBM_TILE_AREA,
    AGENTE_OTBM_NODE_TILE: OTBM_TILE,
    AGENTE_OTBM_NODE_ITEM: OTBM_ITEM,
    AGENTE_OTBM_NODE_SPAWNS: OTBM_SPAWNS,
    AGENTE_OTBM_NODE_SPAWN_AREA: OTBM_SPAWN_AREA,
    AGENTE_OTBM_NODE_MONSTER: OTBM_MONSTER,
    AGENTE_OTBM_NODE_TOWNS: OTBM_TOWNS,
    AGENTE_OTBM_NODE_TOWN: OTBM_TOWN,
    AGENTE_OTBM_NODE_HOUSETILE: OTBM_HOUSETILE,
    AGENTE_OTBM_NODE_WAYPOINTS: OTBM_WAYPOINTS,
    AGENTE_OTBM_NODE_WAYPOINT: OTBM_WAYPOINT,
}

# Mapping from Canary to Agente constants (for reverse compatibility)
CANARY_TO_AGENTE_NODE_MAP = {v: k for k, v in AGENTE_TO_CANARY_NODE_MAP.items()}

__all__ = [
    # Canonical Canary/RME node constants
    "OTBM_ROOTV1",
    "OTBM_MAP_DATA",
    "OTBM_ITEM_DEF",
    "OTBM_TILE_AREA",
    "OTBM_TILE",
    "OTBM_ITEM",
    "OTBM_TILE_SQUARE",
    "OTBM_TILE_REF",
    "OTBM_SPAWNS",
    "OTBM_SPAWN_AREA",
    "OTBM_MONSTER",
    "OTBM_TOWNS",
    "OTBM_TOWN",
    "OTBM_HOUSETILE",
    "OTBM_WAYPOINTS",
    "OTBM_WAYPOINT",
    "OTBM_SPAWN_NPC_AREA",
    "OTBM_SPAWNS_NPC",
    "OTBM_TILE_ZONE",
    # Attribute constants
    "OTBM_ATTR_DESCRIPTION",
    "OTBM_ATTR_EXT_FILE",
    "OTBM_ATTR_TILE_FLAGS",
    "OTBM_ATTR_ACTION_ID",
    "OTBM_ATTR_UNIQUE_ID",
    "OTBM_ATTR_TEXT",
    "OTBM_ATTR_DESC",
    "OTBM_ATTR_TELE_DEST",
    "OTBM_ATTR_ITEM",
    "OTBM_ATTR_DEPOT_ID",
    "OTBM_ATTR_EXT_SPAWN_MONSTER_FILE",
    "OTBM_ATTR_RUNE_CHARGES",
    "OTBM_ATTR_EXT_HOUSE_FILE",
    "OTBM_ATTR_HOUSEDOORID",
    "OTBM_ATTR_COUNT",
    "OTBM_ATTR_SUBTYPE",
    "OTBM_ATTR_DURATION",
    "OTBM_ATTR_DECAYING_STATE",
    "OTBM_ATTR_WRITTENDATE",
    "OTBM_ATTR_WRITTENBY",
    "OTBM_ATTR_SLEEPERGUID",
    "OTBM_ATTR_SLEEPSTART",
    "OTBM_ATTR_CHARGES",
    "OTBM_ATTR_EXT_SPAWN_NPC_FILE",
    "OTBM_ATTR_EXT_ZONE_FILE",
    "OTBM_ATTR_ATTRIBUTE_MAP",
    # Tile states
    "TILESTATE_NONE",
    "TILESTATE_PROTECTIONZONE",
    "TILESTATE_NOPVPZONE",
    "TILESTATE_NOLOGOUT",
    "TILESTATE_PVPZONE",
    "TILESTATE_REFRESH",
    "TILESTATE_TRASHED",
    # Header constants
    "OTBM_IDENTIFIER",
    "OTBM_NAMED_IDENTIFIER",
    "OTBM_ACCEPTED_IDENTIFIERS",
    "DEFAULT_OTBM_VERSION",
    "DEFAULT_ITEM_MAJOR_VERSION",
    "DEFAULT_ITEM_MINOR_VERSION",
    # Agente RME constants (for compatibility)
    "AGENTE_OTBM_NODE_ROOT",
    "AGENTE_OTBM_NODE_MAP_DATA",
    "AGENTE_OTBM_NODE_TILE_AREA",
    "AGENTE_OTBM_NODE_TILE",
    "AGENTE_OTBM_NODE_ITEM",
    "AGENTE_OTBM_NODE_TILE_SQUARE",
    "AGENTE_OTBM_NODE_SPAWNS",
    "AGENTE_OTBM_NODE_SPAWN_AREA",
    "AGENTE_OTBM_NODE_MONSTER",
    "AGENTE_OTBM_NODE_TOWNS",
    "AGENTE_OTBM_NODE_TOWN",
    "AGENTE_OTBM_NODE_HOUSETILE",
    "AGENTE_OTBM_NODE_WAYPOINTS",
    "AGENTE_OTBM_NODE_WAYPOINT",
    # Node mappings
    "AGENTE_TO_CANARY_NODE_MAP",
    "CANARY_TO_AGENTE_NODE_MAP",
]

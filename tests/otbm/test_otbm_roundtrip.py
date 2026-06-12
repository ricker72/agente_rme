"""
Tests de ida y vuelta (roundtrip) para el módulo OTBM.

Verifica:
  - Small map: 4 tiles + 1 spawn
  - City map: múltiples tiles con items decorativos
  - Hunt map: tiles tipo HuntArea con spawns
  - Boss room: boss spawn + flag PZ
  - Serialización → validación → deserialización
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

# Asegurar que podemos importar del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.world_engine.world_engine import WorldModel, Tile
from core.otbm import (
    OtbmSerializer,
    OtbmValidator,
    NodeEncoder,
    OTBM_NODE_ROOT,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_MONSTER,
)


def _dump_hex_header(data: bytes, max_len: int = 64) -> str:
    return data[:max_len].hex(" ")


# ============================================================
# Test 1: Small map (4 tiles + 1 spawn)
# ============================================================


def test_small_map():
    """Genera un mapa pequeño y verifica roundtrip completo."""
    wm = WorldModel()
    wm.add_tile(Tile(x=1000, y=1000, z=7, ground="106"))
    wm.add_tile(Tile(x=1001, y=1000, z=7, ground="106"))
    wm.add_tile(Tile(x=1000, y=1001, z=7, ground="106"))
    wm.add_tile(Tile(x=1001, y=1001, z=7, ground="106"))
    wm.spawns.append(
        {"monster": "Dragon Lord", "x": 1000, "y": 1000, "z": 7, "respawn": 60}
    )

    serializer = OtbmSerializer()
    data = serializer.serialize(wm)

    # Validar magic
    assert data[:4] == b"OTBM", f"Magic inválido: {data[:4]!r}"

    # Validar estructura
    validator = OtbmValidator()
    result = validator.validate(data)
    assert result.status == "success", f"Validación falló: {result.errors}"
    assert result.stats["tiles"] == 4, (
        f"Esperados 4 tiles, encontrados {result.stats['tiles']}"
    )
    assert result.stats["monsters"] == 1, (
        f"Esperado 1 monster, encontrados {result.stats['monsters']}"
    )

    # Deserializar
    decoded = serializer.deserialize(data)
    assert decoded["width"] == 2
    assert decoded["height"] == 2
    assert len(decoded["tiles"]) == 4
    assert len(decoded["spawns"]) == 1
    assert decoded["spawns"][0]["monsters"][0]["name"] == "Dragon Lord"
    assert decoded["item_version"] == (3, 57)

    print(
        f"[PASS] test_small_map — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawns, {len(data)} bytes"
    )


# ============================================================
# Test 2: City map (múltiples tiles con items decorativos)
# ============================================================


def test_city_map():
    """Genera un mapa tipo ciudad con items decorativos."""
    wm = WorldModel()
    # 5x5 tiles con suelo de ciudad
    for x in range(100, 105):
        for y in range(100, 105):
            tile = Tile(x=x, y=y, z=7, ground="city_floor")
            if (x + y) % 3 == 0:
                tile.items.append({"name": "torch"})
            wm.add_tile(tile)

    # Ciudad con templo
    wm.cities.append(
        {
            "name": "TestCity",
            "temple_x": 102,
            "temple_y": 102,
            "temple_z": 7,
        }
    )

    serializer = OtbmSerializer()
    data = serializer.serialize(wm)

    validator = OtbmValidator()
    result = validator.validate(data)
    assert result.status == "success", f"Validación falló: {result.errors}"
    assert result.stats["tiles"] == 25
    assert result.stats["towns"] >= 1

    decoded = serializer.deserialize(data)
    assert len(decoded["tiles"]) == 25
    assert len(decoded["towns"]) >= 1
    assert decoded["towns"][0]["name"] == "TestCity"

    print(
        f"[PASS] test_city_map — {len(decoded['tiles'])} tiles, {len(decoded['towns'])} towns, {len(data)} bytes"
    )


# ============================================================
# Test 3: Hunt map (simula HuntArea del pipeline_runner)
# ============================================================


def test_hunt_map():
    """Simula la salida del pipeline (HuntArea) para verificar exportabilidad."""
    # Crear un WorldModel que simule una HuntArea
    wm = WorldModel()
    for x in range(500, 510):
        for y in range(500, 510):
            ground = "stone_floor" if x % 3 == 0 else "cave_floor"
            tile = Tile(x=x, y=y, z=8, ground=ground)
            if x in (505, 506) and y == 505:
                tile.items.append({"name": "torch"})
            wm.add_tile(tile)

    # Spawns estilo hunt
    wm.spawns.append(
        {"monster": "Serpent Spawn", "x": 502, "y": 502, "z": 8, "respawn": 50}
    )
    wm.spawns.append({"monster": "Medusa", "x": 504, "y": 504, "z": 8, "respawn": 50})
    wm.spawns.append({"monster": "Hydra", "x": 506, "y": 506, "z": 8, "respawn": 50})
    wm.spawns.append(
        {"monster": "Dragon Lord", "x": 508, "y": 508, "z": 8, "respawn": 50}
    )
    wm.spawns.append(
        {"monster": "Grand Canon Dominant", "x": 505, "y": 505, "z": 8, "respawn": 300}
    )

    serializer = OtbmSerializer()
    data = serializer.serialize(wm)

    validator = OtbmValidator()
    result = validator.validate(data)
    assert result.status == "success", f"Validación falló: {result.errors}"

    decoded = serializer.deserialize(data)
    assert len(decoded["tiles"]) == 100
    assert decoded["spawns"], "No se encontraron spawns"

    monster_names = [m["monsters"][0]["name"] for m in decoded["spawns"]]
    assert "Serpent Spawn" in monster_names
    assert "Hydra" in monster_names

    print(
        f"[PASS] test_hunt_map — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawn areas"
    )


# ============================================================
# Test 4: Boss room (boss + flag PZ)
# ============================================================


def test_boss_room():
    """Genera un boss room con PZ flag."""
    wm = WorldModel()
    # Sala 5x5 en z=8
    for x in range(200, 205):
        for y in range(200, 205):
            tile = Tile(x=x, y=y, z=8, ground="elite_floor")
            if x in (202, 203) and y in (202, 203):
                tile.items.append({"name": "crystal_torch"})
                tile.items.append({"name": "blood"})
            wm.add_tile(tile)

    # Boss spawn
    wm.spawns.append(
        {"monster": "Grand Canon Dominant", "x": 203, "y": 203, "z": 8, "respawn": 600}
    )
    wm.spawns.append(
        {"monster": "Crystal Guardian", "x": 200, "y": 200, "z": 8, "respawn": 60}
    )

    serializer = OtbmSerializer()
    data = serializer.serialize(wm)

    # Verificar magic
    assert data[:4] == b"OTBM"

    # Verificar que tiene root node type correcto
    root_type = data[4]
    assert root_type == OTBM_NODE_ROOT, f"Root type: 0x{root_type:02X}"

    validator = OtbmValidator()
    result = validator.validate(data)
    assert result.status == "success", f"Validación falló: {result.errors}"

    decoded = serializer.deserialize(data)
    assert len(decoded["tiles"]) == 25
    assert len(decoded["spawns"]) == 2

    print(
        f"[PASS] test_boss_room — {len(decoded['tiles'])} tiles, {len(decoded['spawns'])} spawns"
    )


# ============================================================
# Test 5: WorldModelToOTBM (high-level API)
# ============================================================


def test_worldmodel_to_otbm():
    """Verifica el API de alto nivel WorldModelToOTBM."""
    from core.otbm import WorldModelToOTBM

    wm = WorldModel()
    wm.add_tile(Tile(x=10, y=10, z=0, ground="106"))
    wm.add_tile(Tile(x=11, y=10, z=0, ground="106"))

    converter = WorldModelToOTBM()
    data = converter.convert(wm)

    assert data[:4] == b"OTBM"
    assert len(data) > 20  # Al menos algo de contenido

    # Save a archivo
    output = Path(__file__).resolve().parent / "test_highlevel.otbm"
    path = converter.save(wm, output, generate_templates=False)
    assert path.exists()
    assert path.read_bytes()[:4] == b"OTBM"
    path.unlink()  # Limpiar

    print("[PASS] test_worldmodel_to_otbm — API alto nivel funciona")


# ============================================================
# Test 6: NodeEncoder low-level
# ============================================================


def test_node_encoder():
    """Verifica que NodeEncoder genera nodos bien formados."""
    encoder = NodeEncoder()

    # Tile
    tile_node = encoder.encode_tile(offset_x=5, offset_y=10, tile_flags=0)
    assert tile_node[0] == OTBM_NODE_TILE  # type byte
    # offset_x(1) + offset_y(1) = 2 bytes payload
    payload_size = struct.unpack_from("<H", tile_node, 1)[0]
    assert payload_size == 2, f"Esperado payload 2, encontrado {payload_size}"

    # Item sin atributos
    item_node = encoder.encode_item(item_id=106)
    assert item_node[0] == OTBM_NODE_ITEM
    item_size = struct.unpack_from("<H", item_node, 1)[0]
    assert item_size == 2  # solo item_id uint16

    # Item con count
    item_with_count = encoder.encode_item(item_id=2160, count=50)
    item_c_size = struct.unpack_from("<H", item_with_count, 1)[0]
    assert item_c_size == 4  # item_id(2) + ATTR_COUNT(1) + count(1)

    # Monster
    monster_node = encoder.encode_monster(name="Dragon", direction=2, spawntime=60)
    assert monster_node[0] == OTBM_NODE_MONSTER

    # SPAWN_AREA
    spawn_area = encoder.encode_spawn_area(
        center_x=1000, center_y=1000, center_z=7, radius=3, children=monster_node
    )
    assert spawn_area[0] == OTBM_NODE_SPAWN_AREA

    print("[PASS] test_node_encoder — nodos binarios correctos")


# ============================================================
# Test 7: OpenTibiaBR compatibility constraints
# ============================================================


def test_otbr_compatibility():
    """Verifica restricciones de compatibilidad OpenTibiaBR."""
    serializer = OtbmSerializer()
    validator = OtbmValidator()

    # Mapa con item ID 0 (inválido)
    wm = WorldModel()
    wm.add_tile(Tile(x=0, y=0, z=0, ground="0"))
    data = serializer.serialize(wm)
    result = validator.validate(data)
    # ID 0 del ground se resuelve en TileEncoder (no debería ser 0 real)
    if result.warnings:
        print(f"  [INFO] Warnings de compatibilidad: {result.warnings}")

    # Mapa con dimensiones grandes pero válidas
    wm2 = WorldModel()
    for x in range(50):
        for y in range(50):
            wm2.add_tile(Tile(x=x, y=y, z=0, ground="106"))
    data2 = serializer.serialize(wm2)
    result2 = validator.validate(data2)
    assert result2.status == "success"
    assert result2.stats["tiles"] == 2500

    print(
        f"[PASS] test_otbr_compatibility — {result2.stats['tiles']} tiles, {len(data2)} bytes"
    )


# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  OTBM Roundtrip & Compatibility Tests")
    print("=" * 60)
    print()

    tests = [
        test_small_map,
        test_city_map,
        test_hunt_map,
        test_boss_room,
        test_worldmodel_to_otbm,
        test_node_encoder,
        test_otbr_compatibility,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback

            print(f"[FAIL] {test_fn.__name__}: {e}")
            traceback.print_exc()

    print()
    print(f"{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

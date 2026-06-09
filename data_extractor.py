"""
data_extractor.py
Parses items.xml and builds an enriched item knowledge base for OpenTibiaBR RME.
Each item includes classification data such as category, theme, biome y usage.
"""
import json
import os
import re
from pathlib import Path
from typing import Optional

try:
    from lxml import etree as LET
    _LXML = True
except ImportError:
    import xml.etree.ElementTree as _StdET  # type: ignore
    _LXML = False

CACHE_FILE = "rme_knowledge_cache.json"

THEME_KEYWORDS = {
    "issavi": ["issavi", "sand", "dune", "ancient", "ruins"],
    "roshamuul": ["roshamuul", "corrupt", "dark", "hell", "shadow"],
    "yalahar": ["yalahar", "sea", "ocean", "ship", "coral"],
    "jungle": ["jungle", "tropical", "leaf", "vines", "swamp"],
    "ice": ["ice", "frozen", "snow", "glacier", "frost"],
}

BIOME_KEYWORDS = {
    "desert": ["sand", "dune", "dry", "stone", "sun"],
    "forest": ["tree", "leaf", "wood", "jungle", "vines"],
    "cave": ["cave", "rock", "underground", "dungeon", "stone"],
    "ruins": ["ruin", "ancient", "broken", "moss", "temple"],
    "ice": ["ice", "snow", "frozen", "glacier", "cold"],
    "swamp": ["swamp", "mud", "marsh", "water", "reeds"],
}

CATEGORY_KEYWORDS = {
    "terrain": ["floor", "ground", "sand", "grass", "stone", "pavement", "dirt", "tile"],
    "wall": ["wall", "pillar", "fence", "barrier", "rock face", "stone wall"],
    "door": ["door", "gate", "portal", "entrance", "exit", "arch"],
    "decoration": ["torch", "lamp", "statue", "banner", "vase", "plant", "column", "fountain"],
    "furniture": ["chair", "table", "bed", "throne", "bench", "altar"],
    "spawn": ["spawn", "hole", "nest", "lair", "teleport"],
    "liquid": ["water", "lava", "pool", "river", "sea", "ocean"],
}

USAGE_KEYWORDS = {
    "floor": ["floor", "ground", "pavement", "path"],
    "wall": ["wall", "pillar", "fence", "barrier"],
    "decoration": ["statue", "lamp", "banner", "fountain", "plant"],
    "spawn": ["spawn", "hole", "trap"],
    "door": ["door", "gate", "portal", "entrance"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _pick_metadata(value: str, keyword_map: dict[str, list[str]], default: str) -> str:
    lower = _normalize(value)
    for metadata, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in lower:
                return metadata
    return default


def _classify_item(item_id: str, name: str) -> dict:
    name_lower = _normalize(name)
    category = _pick_metadata(name_lower, CATEGORY_KEYWORDS, "general")
    theme = _pick_metadata(name_lower, THEME_KEYWORDS, "generic")
    biome = _pick_metadata(name_lower, BIOME_KEYWORDS, "generic")
    usage = _pick_metadata(name_lower, USAGE_KEYWORDS, category)
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "theme": theme,
        "biome": biome,
        "usage": usage,
    }


def _item_record(item_id: str, name: str) -> dict:
    record = _classify_item(item_id, name)
    record["display"] = f"{item_id} - {name}"
    return record


def _extract_lxml(items_xml_path: str) -> dict:
    data = {
        "items": [],
        "by_id": {},
        "by_category": {},
        "by_theme": {},
        "by_biome": {},
        "total": 0,
    }

    context = LET.iterparse(items_xml_path, events=("end",), tag="item", recover=True)
    for _event, elem in context:
        item_id = elem.get("id") or elem.get("fromid")
        name = elem.get("name") or ""
        if item_id:
            record = _item_record(item_id, name)
            data["items"].append(record)
            data["by_id"][item_id] = record
            data["by_category"].setdefault(record["category"], []).append(item_id)
            data["by_theme"].setdefault(record["theme"], []).append(item_id)
            data["by_biome"].setdefault(record["biome"], []).append(item_id)
            data["total"] += 1
        elem.clear()

    return data


def _extract_stdlib(items_xml_path: str) -> dict:
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(items_xml_path)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear items.xml: {e}")

    data = {
        "items": [],
        "by_id": {},
        "by_category": {},
        "by_theme": {},
        "by_biome": {},
        "total": 0,
    }

    items_elements = root.findall(".//item") or root.findall("item")
    for item in items_elements:
        item_id = item.get("id") or item.get("fromid")
        name = item.get("name") or ""
        if item_id:
            record = _item_record(item_id, name)
            data["items"].append(record)
            data["by_id"][item_id] = record
            data["by_category"].setdefault(record["category"], []).append(item_id)
            data["by_theme"].setdefault(record["theme"], []).append(item_id)
            data["by_biome"].setdefault(record["biome"], []).append(item_id)
            data["total"] += 1

    return data


def _score_item(item: dict, prompt_lower: str) -> int:
    score = 0
    if item["category"] in prompt_lower:
        score += 4
    if item["theme"] in prompt_lower:
        score += 3
    if item["biome"] in prompt_lower:
        score += 2
    if item["usage"] in prompt_lower:
        score += 2
    if item["name"].lower() in prompt_lower:
        score += 5
    return score


def extract_items(items_xml_path: str, force: bool = False) -> dict:
    if not force and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if cache.get("source") == items_xml_path:
                return cache["data"]
        except Exception:
            pass

    if _LXML:
        data = _extract_lxml(items_xml_path)
    else:
        data = _extract_stdlib(items_xml_path)

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"source": items_xml_path, "data": data}, f, ensure_ascii=False)
    except Exception:
        pass

    return data


def get_relevant_items(prompt: str, cache: dict, max_items: int = 60) -> list[dict]:
    prompt_lower = _normalize(prompt)
    scored = []
    for item in cache.get("items", []):
        score = _score_item(item, prompt_lower)
        if score > 0:
            scored.append((score, item))

    if not scored:
        scored = [(1, item) for item in cache.get("items", [])[:max_items]]

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _score, item in scored[:max_items]]


def build_rag_context(items: list[dict]) -> str:
    lines = ["=== Datos enriquecidos de items.xml ==="]
    for item in items[:40]:
        lines.append(
            f"{item['id']} | {item['name']} | category={item['category']} | theme={item['theme']} | biome={item['biome']} | usage={item['usage']}"
        )
    if not items:
        lines.append("No se ha identificado contexto relevante de items.")
    return "\n".join(lines)


def _parse_xml_file(path: str):
    if _LXML:
        parser = LET.XMLParser(recover=True)
        tree = LET.parse(str(path), parser)
        return tree.getroot()
    else:
        import xml.etree.ElementTree as ET
        return ET.parse(str(path)).getroot()


def _extract_monster_names_from_root(root, limit: int) -> list[str]:
    names = []
    tag = root.tag if isinstance(root.tag, str) else ""
    if tag.lower() == "monster":
        name = root.get("name") or root.findtext(".//name")
        if name:
            names.append(name)
        return names[:limit]

    for node in root.findall(".//monster"):
        name = node.get("name") or node.findtext(".//name")
        if name:
            names.append(name)
        if len(names) >= limit:
            break
    return names[:limit]


def _extract_npc_names_from_root(root, limit: int) -> list[str]:
    names = []
    tag = root.tag if isinstance(root.tag, str) else ""
    if tag.lower() == "npc":
        name = root.get("name") or root.findtext(".//name")
        if name:
            names.append(name)
        return names[:limit]

    for node in root.findall(".//npc"):
        name = node.get("name") or node.findtext(".//name")
        if name:
            names.append(name)
        if len(names) >= limit:
            break
    return names[:limit]


def load_monster_names(monsters_folder: str, limit: int = 50) -> list[str]:
    names = []
    folder = Path(monsters_folder)
    if folder.is_file():
        try:
            root = _parse_xml_file(folder)
            return _extract_monster_names_from_root(root, limit)
        except Exception:
            return []

    for f in sorted(folder.rglob("*.xml")):
        if len(names) >= limit:
            break
        try:
            root = _parse_xml_file(f)
            names.extend(_extract_monster_names_from_root(root, limit - len(names)))
        except Exception:
            continue
    return names[:limit]


def load_npc_names(npcs_folder: str, limit: int = 30) -> list[str]:
    names = []
    folder = Path(npcs_folder)
    if folder.is_file():
        try:
            root = _parse_xml_file(folder)
            return _extract_npc_names_from_root(root, limit)
        except Exception:
            return []

    for f in sorted(folder.rglob("*.xml")):
        if len(names) >= limit:
            break
        try:
            root = _parse_xml_file(f)
            names.extend(_extract_npc_names_from_root(root, limit - len(names)))
        except Exception:
            continue
    return names[:limit]

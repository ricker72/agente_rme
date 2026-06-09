"""
config_manager.py
Handles loading, saving, and validating the RME Agent configuration.
Uses lxml for fast, robust XML validation with stdlib ET as fallback.
"""
import json
import os
from pathlib import Path
from typing import Optional

# Prefer lxml for speed and richer error messages; fall back to stdlib
try:
    from lxml import etree as LET
    _LXML = True
except ImportError:
    import xml.etree.ElementTree as _StdET  # type: ignore
    _LXML = False

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "tibia_client_path": "",
    "items_xml_path": "",
    "monsters_folder": "",
    "npcs_folder": "",
    "mounts_folder": "",
    "configured": False,
    "last_model": "",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def is_configured(config: dict) -> bool:
    return bool(config.get("configured", False))


# ── Internal XML helpers ────────────────────────────────────────────────────

def _parse_xml(path: str):
    """Parse XML with lxml if available, else stdlib. Returns root element."""
    if _LXML:
        parser = LET.XMLParser(recover=True, encoding=None)
        tree = LET.parse(path, parser)
        return tree.getroot()
    else:
        import xml.etree.ElementTree as ET
        tree = ET.parse(path)
        return tree.getroot()


def _xml_parse_error(e) -> str:
    """Normalise error message across lxml / stdlib."""
    if _LXML:
        # lxml XMLSyntaxError carries line/col info
        return str(e)
    return str(e)


# ── Validation helpers ──────────────────────────────────────────────────────

class ValidationError(Exception):
    pass


def validate_tibia_path(path: str) -> tuple[bool, str]:
    """Accepts either a directory (client root) or direct path to appearances.dat / .otb"""
    if not path:
        return False, "La ruta del cliente Tibia está vacía."
    p = Path(path)
    if p.is_dir():
        candidates = list(p.rglob("appearances.dat")) + list(p.rglob("*.otb"))
        if not candidates:
            return False, f"No se encontró appearances.dat ni archivos .otb en: {path}"
        return True, f"Directorio válido ({len(candidates)} archivo(s) de datos encontrado(s))."
    elif p.is_file():
        if p.suffix.lower() in (".dat", ".otb", ".spr"):
            return True, f"Archivo válido: {p.name}"
        return False, f"El archivo '{p.name}' no parece ser un archivo de cliente Tibia."
    return False, f"La ruta no existe: {path}"


def validate_items_xml(path: str) -> tuple[bool, str]:
    if not path:
        return False, "La ruta de items.xml está vacía."
    p = Path(path)
    if not p.is_file():
        return False, f"No se encontró el archivo: {path}"
    if p.suffix.lower() != ".xml":
        return False, "El archivo no tiene extensión .xml"
    try:
        root = _parse_xml(str(p))
        if _LXML:
            items = root.findall(".//item[@id]")
            if not items:
                items = root.findall("item")
        else:
            import xml.etree.ElementTree as ET
            items = root.findall(".//item[@id]")
            if not items:
                items = root.findall("item")
        if len(items) == 0:
            return False, "El archivo XML no contiene ningún elemento <item id='...'>"
        named = [i for i in items if i.get("name")]
        backend = "lxml" if _LXML else "stdlib"
        return True, f"XML válido [{backend}]: {len(items)} items encontrados ({len(named)} con nombre)."
    except Exception as e:
        return False, f"Error al parsear XML: {_xml_parse_error(e)}"


def _xml_has_tag_with_name(root, tag: str) -> list:
    if _LXML:
        nodes = root.findall(f".//{tag}[@name]")
        if not nodes:
            nodes = root.findall(f".//{tag}")
    else:
        import xml.etree.ElementTree as ET
        nodes = root.findall(f".//{tag}[@name]")
        if not nodes:
            nodes = root.findall(f".//{tag}")
    return nodes


def _validate_xml_file(path: Path, tag: str) -> tuple[bool, str]:
    try:
        root = _parse_xml(str(path))
        nodes = _xml_has_tag_with_name(root, tag)
        if not nodes:
            return False, f"El archivo {path.name} no contiene ningún elemento <{tag} name='...'> ni <{tag}>"
        return True, f"Archivo válido: {len(nodes)} <{tag}> encontrados en {path.name}."
    except Exception as e:
        return False, f"Error al parsear {path.name}: {_xml_parse_error(e)}"


def validate_monsters_folder(path: str) -> tuple[bool, str]:
    if not path:
        return False, "La carpeta de monstruos está vacía."
    p = Path(path)
    if p.is_file():
        if p.suffix.lower() != ".xml":
            return False, "El archivo de monstruos no tiene extensión .xml"
        return _validate_xml_file(p, "monster")
    if not p.is_dir():
        return False, f"No es una carpeta válida: {path}"

    monster_xml = p / "monster.xml"
    if monster_xml.is_file():
        return _validate_xml_file(monster_xml, "monster")

    xml_files = list(p.rglob("*.xml"))
    monster_files = []
    for f in xml_files[:50]:
        try:
            root = _parse_xml(str(f))
            tag = root.tag if isinstance(root.tag, str) else root.tag.lower()
            if tag.lower() == "monster" and root.get("name"):
                monster_files.append(f)
        except Exception:
            continue
    if not monster_files:
        return False, "No se encontraron archivos XML con estructura <monster name='...'> ni un monster.xml válido."
    return True, f"Carpeta válida: {len(xml_files)} XML encontrados, {len(monster_files)} con estructura de monstruo."


def validate_npcs_folder(path: str) -> tuple[bool, str]:
    if not path:
        return False, "La carpeta de NPCs está vacía."
    p = Path(path)
    if p.is_file():
        if p.suffix.lower() != ".xml":
            return False, "El archivo de NPCs no tiene extensión .xml"
        return _validate_xml_file(p, "npc")
    if not p.is_dir():
        return False, f"No es una carpeta válida: {path}"

    npc_xml = p / "npc.xml"
    if npc_xml.is_file():
        return _validate_xml_file(npc_xml, "npc")

    xml_files = list(p.rglob("*.xml"))
    if not xml_files:
        return False, "No se encontraron archivos .xml en la carpeta de NPCs."
    return True, f"Carpeta válida: {len(xml_files)} archivo(s) XML encontrado(s)."


def validate_mounts_folder(path: str) -> tuple[bool, str]:
    """Mounts folder is optional."""
    if not path:
        return True, "Opcional — omitido."
    p = Path(path)
    if not p.is_dir():
        return False, f"No es una carpeta válida: {path}"
    xml_files = list(p.rglob("*.xml"))
    return True, f"Carpeta válida: {len(xml_files)} archivo(s) encontrado(s)."


def validate_all(config: dict) -> list[tuple[str, bool, str]]:
    """Returns list of (field_label, is_valid, message)"""
    results = []
    results.append(("Cliente Tibia",    *validate_tibia_path(config.get("tibia_client_path", ""))))
    results.append(("items.xml",        *validate_items_xml(config.get("items_xml_path", ""))))
    results.append(("Carpeta Monstruos",*validate_monsters_folder(config.get("monsters_folder", ""))))
    results.append(("Carpeta NPCs",     *validate_npcs_folder(config.get("npcs_folder", ""))))
    results.append(("Carpeta Monturas", *validate_mounts_folder(config.get("mounts_folder", ""))))
    return results

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple


def load_items(items_path: str) -> Tuple[dict, list[dict]]:
    items_catalog = {}
    documents = []
    path = Path(items_path)
    if not path.exists():
        return items_catalog, documents

    tree = ET.parse(path)
    root = tree.getroot()
    for item in root.findall("item"):
        item_id = item.get("id") or item.get("clientId") or ""
        name = item.get("name") or ""
        description = item.findtext("description") or ""
        items_catalog[item_id] = {
            "id": item_id,
            "name": name,
            "description": description,
        }
        documents.append({
            "title": f"Item {item_id}",
            "text": f"{name}: {description}".strip(),
            "metadata": {"type": "item", "id": item_id},
        })
    return items_catalog, documents

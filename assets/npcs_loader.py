import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple


def load_npc_names(npc_source: str) -> Tuple[List[str], List[dict]]:
    path = Path(npc_source)
    npc_names: List[str] = []
    documents: List[dict] = []

    if path.is_dir():
        for child in path.iterdir():
            if child.suffix.lower() == ".xml":
                names, docs = load_npc_names(str(child))
                npc_names.extend(names)
                documents.extend(docs)
        return npc_names, documents

    if not path.exists():
        return npc_names, documents

    tree = ET.parse(path)
    root = tree.getroot()
    for npc in root.findall("npc"):
        name = npc.get("name") or npc.findtext("name") or ""
        if name:
            npc_names.append(name)
            documents.append({
                "title": f"NPC {name}",
                "text": f"NPC {name} available in RME data.",
                "metadata": {"type": "npc", "name": name},
            })
    return npc_names, documents

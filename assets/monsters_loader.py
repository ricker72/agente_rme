import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple


def load_monster_names(monster_source: str) -> Tuple[List[str], List[dict]]:
    path = Path(monster_source)
    monster_names: List[str] = []
    documents: List[dict] = []

    if path.is_dir():
        for child in path.iterdir():
            if child.suffix.lower() == ".xml":
                names, docs = load_monster_names(str(child))
                monster_names.extend(names)
                documents.extend(docs)
        return monster_names, documents

    if not path.exists():
        return monster_names, documents

    tree = ET.parse(path)
    root = tree.getroot()
    for monster in root.findall("monster"):
        name = monster.get("name") or monster.findtext("name") or ""
        if name:
            monster_names.append(name)
            documents.append(
                {
                    "title": f"Monster {name}",
                    "text": f"Monster {name} found in RME data.",
                    "metadata": {"type": "monster", "name": name},
                }
            )
    return monster_names, documents

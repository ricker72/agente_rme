from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PackageResult:
    """Result of package building."""
    package_dir: str = ""
    files_created: List[str] = field(default_factory=list)
    total_size_kb: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_dir": self.package_dir,
            "files_created": self.files_created,
            "total_size_kb": round(self.total_size_kb, 1),
            "summary": self.summary,
        }


class PackageBuilder:
    """
    Builds a release package with all artifacts in a structured directory.

    Package structure:
        release/<name>/
            world.otbm
            lua/
                map.lua
            xml/
                monster.xml
                npc.xml
            docs/
                README.md
                CHANGELOG.md
                MAP_GUIDE.md
            preview/
                overview.png
            report/
                balance.json
                analysis.json
    """

    def __init__(self, output_root: str | Path = "release"):
        self.output_root = Path(output_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, name: str, otbm_bytes: Optional[bytes] = None,
              lua_scripts: Optional[Dict[str, str]] = None,
              xml_files: Optional[Dict[str, str]] = None,
              docs: Optional[Dict[str, str]] = None,
              preview_path: Optional[str] = None,
              reports: Optional[Dict[str, Any]] = None) -> PackageResult:
        """
        Build a complete release package.

        Args:
            name: Package name (directory name).
            otbm_bytes: Raw OTBM file bytes.
            lua_scripts: Dict of {filename: content} for lua/.
            xml_files: Dict of {filename: content} for xml/.
            docs: Dict of {filename: content} for docs/.
            preview_path: Path to preview image to copy.
            reports: Dict of {filename: data} for report/. Serialized as JSON.

        Returns:
            PackageResult with paths and size.
        """
        package_dir = self.output_root / name
        self._clean_dir(package_dir)
        created: List[str] = []

        # Create subdirectories
        lua_dir = package_dir / "lua"
        xml_dir = package_dir / "xml"
        docs_dir = package_dir / "docs"
        preview_dir = package_dir / "preview"
        report_dir = package_dir / "report"

        for d in [lua_dir, xml_dir, docs_dir, preview_dir, report_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 1. OTBM file
        if otbm_bytes:
            otbm_path = package_dir / f"{name}.otbm"
            otbm_path.write_bytes(otbm_bytes)
            created.append(str(otbm_path))

        # 2. Lua scripts
        if lua_scripts:
            for filename, content in lua_scripts.items():
                path = lua_dir / filename
                path.write_text(content, encoding="utf-8")
                created.append(str(path))

        # 3. XML files
        if xml_files:
            for filename, content in xml_files.items():
                path = xml_dir / filename
                path.write_text(content, encoding="utf-8")
                created.append(str(path))

        # 4. Documentation
        if docs:
            for filename, content in docs.items():
                path = docs_dir / filename
                path.write_text(content, encoding="utf-8")
                created.append(str(path))

        # 5. Preview
        if preview_path:
            src = Path(preview_path)
            if src.exists():
                dest = preview_dir / f"{name}.png"
                shutil.copy2(src, dest)
                created.append(str(dest))

        # 6. Reports
        if reports:
            for filename, data in reports.items():
                path = report_dir / filename
                if isinstance(data, str):
                    path.write_text(data, encoding="utf-8")
                else:
                    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                created.append(str(path))

        # Calculate total size
        total_size = sum(Path(f).stat().st_size for f in created if Path(f).exists())

        return PackageResult(
            package_dir=str(package_dir),
            files_created=created,
            total_size_kb=total_size / 1024,
            summary=f"Package '{name}' created at {package_dir} with {len(created)} files ({total_size / 1024:.1f} KB)",
        )

    def build_from_dict(self, name: str, package_data: Dict[str, Any]) -> PackageResult:
        """
        Build a package from a structured dict.

        Args:
            name: Package name.
            package_data: Dict with keys: otbm_bytes, lua, xml, docs, preview, reports.

        Returns:
            PackageResult.
        """
        return self.build(
            name=name,
            otbm_bytes=package_data.get("otbm_bytes"),
            lua_scripts=package_data.get("lua"),
            xml_files=package_data.get("xml"),
            docs=package_data.get("docs"),
            preview_path=package_data.get("preview"),
            reports=package_data.get("reports"),
        )

    def create_metadata(self, name: str, version: str = "1.0.0",
                        author: str = "RME AI",
                        description: str = "") -> str:
        """Create a package.json metadata file."""
        meta = {
            "name": name,
            "version": version,
            "author": author,
            "description": description or f"RME generated expansion: {name}",
            "generator": "RME AI World Generator",
            "format": "otbm_v4",
            "requirements": {
                "client": "12.x+",
                "server": "OTServ compatible",
            },
        }
        return json.dumps(meta, indent=2, ensure_ascii=False)

    def _clean_dir(self, path: Path) -> None:
        """Clean and recreate a directory."""
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
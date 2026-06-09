from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .package_builder import PackageBuilder, PackageResult
from .documentation_builder import DocumentationBuilder, DocumentationResult


@dataclass
class ReleaseResult:
    """Complete result of a release build."""
    name: str = ""
    version: str = ""
    package: PackageResult = field(default_factory=PackageResult)
    docs: DocumentationResult = field(default_factory=DocumentationResult)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "package": self.package.to_dict(),
            "docs": self.docs.to_dict(),
            "summary": self.summary,
        }


class ReleaseBuilder:
    """
    Complete release pipeline: builds package + documentation + metadata.

    Usage:
        builder = ReleaseBuilder()
        result = builder.build(
            name="issavi_expansion",
            otbm_bytes=bytes_data,
            map_data={"tiles": [...], "spawns": [...], "towns": [...]},
            version="2.0.0",
            author="RME AI",
        )
        print(result.summary)
    """

    def __init__(self, output_root: str | Path = "release"):
        self.output_root = Path(output_root)
        self.package_builder = PackageBuilder(output_root)
        self.doc_builder = DocumentationBuilder(output_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, name: str, otbm_bytes: Optional[bytes] = None,
              map_data: Optional[Dict[str, Any]] = None,
              version: str = "1.0.0", author: str = "RME AI",
              lua_scripts: Optional[Dict[str, str]] = None,
              xml_files: Optional[Dict[str, str]] = None,
              preview_path: Optional[str] = None,
              reports: Optional[Dict[str, Any]] = None,
              changelog_entries: Optional[List[str]] = None) -> ReleaseResult:
        """
        Full release: build package + generate docs + create metadata.

        Args:
            name: Release name (e.g., "issavi_expansion").
            otbm_bytes: Raw OTBM binary data.
            map_data: Dict with tiles, spawns, towns for doc generation.
            version: Version string.
            author: Author name.
            lua_scripts: Lua scripts for lua/ directory.
            xml_files: XML files for xml/ directory.
            preview_path: Path to preview image.
            reports: Additional reports for report/ directory.
            changelog_entries: Changelog entries.

        Returns:
            ReleaseResult with all paths and summaries.
        """
        map_data = map_data or {}

        # Step 1: Generate documentation
        docs_result = self.doc_builder.build_all(
            map_data=map_data,
            name=name,
            version=version,
            author=author,
            changelog_entries=changelog_entries,
        )

        # Step 2: Collect docs for the package
        doc_files: Dict[str, str] = {}
        for f in docs_result.files_created:
            fpath = Path(f)
            doc_files[fpath.name] = fpath.read_text(encoding="utf-8")

        # Step 3: Build the release package
        # Generate XML if map_data has spawns
        if map_data and xml_files is None:
            xml_files = self._generate_xml_from_map(map_data, name)

        # Build metadata report
        if reports is None:
            reports = {}
        reports["package.json"] = self.package_builder.create_metadata(
            name, version, author,
            description=f"RME generated expansion: {name} v{version}",
        )

        package_result = self.package_builder.build(
            name=name,
            otbm_bytes=otbm_bytes,
            lua_scripts=lua_scripts,
            xml_files=xml_files,
            docs=doc_files,
            preview_path=preview_path,
            reports=reports,
        )

        # Step 4: Build the final artifact list for summary
        total_files = len(package_result.files_created) + len(docs_result.files_created)
        summary = (
            f"Release '{name}' v{version}: "
            f"{package_result.total_size_kb:.1f} KB package, "
            f"{total_files} files total."
        )

        return ReleaseResult(
            name=name,
            version=version,
            package=package_result,
            docs=docs_result,
            summary=summary,
        )

    def build_minimal(self, name: str, otbm_bytes: bytes,
                      map_data: Optional[Dict[str, Any]] = None) -> ReleaseResult:
        """
        Quick minimal release with default settings.

        Args:
            name: Release name.
            otbm_bytes: Raw OTBM bytes.
            map_data: Optional map data for doc generation.

        Returns:
            ReleaseResult.
        """
        return self.build(
            name=name,
            otbm_bytes=otbm_bytes,
            map_data=map_data,
            version="1.0.0",
        )

    def build_from_world_model(self, name: str, world_model: Any,
                               version: str = "1.0.0") -> ReleaseResult:
        """
        Build release from a WorldModel object.

        Args:
            name: Release name.
            world_model: WorldModel with .serialize(), .spawns, .tiles, etc.
            version: Version string.

        Returns:
            ReleaseResult.
        """
        import io

        # Try to serialize
        otbm_bytes = None
        if hasattr(world_model, "serialize"):
            data = world_model.serialize()
            if isinstance(data, bytes):
                otbm_bytes = data
            elif isinstance(data, io.BytesIO):
                otbm_bytes = data.getvalue()
            else:
                try:
                    otbm_bytes = bytes(data)
                except (TypeError, ValueError):
                    pass
        elif hasattr(world_model, "to_otbm"):
            otbm_bytes = world_model.to_otbm()
        elif isinstance(world_model, bytes):
            otbm_bytes = world_model

        # Build map_data from world_model
        map_data: Dict[str, Any] = {
            "tiles": list(getattr(world_model, "tiles", {}).values())
                    if hasattr(world_model, "tiles") else [],
            "spawns": list(getattr(world_model, "spawns", []))
                     if hasattr(world_model, "spawns") else [],
            "towns": list(getattr(world_model, "towns", []))
                    if hasattr(world_model, "towns") else [],
        }

        return self.build(
            name=name,
            otbm_bytes=otbm_bytes,
            map_data=map_data,
            version=version,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_xml_from_map(self, map_data: Dict[str, Any],
                                name: str) -> Dict[str, str]:
        """Generate XML files from map data."""
        xml: Dict[str, str] = {}
        spawns = map_data.get("spawns", [])

        # Monster XML
        monsters: Dict[str, int] = {}
        for spawn in spawns:
            for m in spawn.get("monsters", []):
                mname = m.get("name", "")
                if mname:
                    monsters[mname] = monsters.get(mname, 0) + 1

        if monsters:
            monster_lines = []
            for mname in sorted(monsters.keys()):
                monster_lines.append(f'  <monster name="{mname}" respawn="60" />')
            xml["monster.xml"] = "<monsters>\n" + "\n".join(monster_lines) + "\n</monsters>\n"

        # NPC XML (minimal)
        towns = map_data.get("towns", [])
        if towns:
            npc_lines = []
            for town in towns:
                tname = town.get("name", "Unknown")
                tpos = town.get("position", (0, 0, 7))
                npc_lines.append(
                    f'  <npc name="Temple_{tname}" x="{tpos[0]}" y="{tpos[1]}" z="{tpos[2] if len(tpos) > 2 else 7}" />'
                )
            xml["npc.xml"] = "<npcs>\n" + "\n".join(npc_lines) + "\n</npcs>\n"

        # Zone XML
        tiles = map_data.get("tiles", [])
        if tiles:
            xs = [t.get("x", 0) for t in tiles]
            ys = [t.get("y", 0) for t in tiles]
            zs = [t.get("z", 7) for t in tiles]
            xml["zones.xml"] = (
                f'<zones>\n  <zone id="1" name="{name}">\n'
                f'    <area x1="{min(xs)}" y1="{min(ys)}" '
                f'x2="{max(xs)}" y2="{max(ys)}" z="{min(zs)}" />\n'
                f'  </zone>\n</zones>\n'
            )

        return xml

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Remove all release packages."""
        import shutil
        if self.output_root.exists():
            shutil.rmtree(self.output_root)
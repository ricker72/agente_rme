"""PROJECT-01B NECRO new project wizard and project materialization."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from ui.live_preview.app_paths import get_user_projects_root, validate_user_project_path


INITIAL_MODULES = [
    "Temple",
    "Depot",
    "Main Square",
    "Residential District",
    "Basic Roads",
    "Asset Browser",
    "Layer Manager",
    "Project Explorer",
    "Properties Inspector",
    "Engineering Console",
]

FUTURE_MODULES = [
    "NPC Generator",
    "Spawn Generator",
    "Quest Generator",
    "AI Copilot",
]


@dataclass(frozen=True)
class NecroProjectConfig:
    project_name: str = "Necro"
    town_name: str = "Necro"
    temple_x: int = 1000
    temple_y: int = 1000
    temple_z: int = 7
    world_theme: str = "Venore Architecture"
    world_size: str = "4096x4096"
    ground_layer: int = 7
    starting_floor: int = 7
    enabled_modules: List[str] = field(default_factory=lambda: list(INITIAL_MODULES))
    future_modules: List[str] = field(default_factory=lambda: list(FUTURE_MODULES))
    certification: str = "NONE"

    @property
    def project_code(self) -> str:
        return self.project_name.upper()

    @property
    def temple(self) -> Dict[str, int]:
        return {"x": self.temple_x, "y": self.temple_y, "z": self.temple_z}


def default_necro_config() -> NecroProjectConfig:
    return NecroProjectConfig()


class NecroProjectCreator:
    """Creates the PROJECT-01 NECRO skeleton without loading runtime providers."""

    def __init__(self, workspace_root: str | Path | None = None, *, projects_root: str | Path | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve() if workspace_root is not None else None
        self.projects_root = (
            validate_user_project_path(projects_root)
            if projects_root is not None
            else get_user_projects_root(self.workspace_root)
        )

    def create_project(self, config: NecroProjectConfig | None = None) -> Dict[str, object]:
        config = config or default_necro_config()
        project_root = validate_user_project_path(self.projects_root / config.project_code)
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        project_id = f"PROJECT-01-{config.project_code}-{uuid.uuid4().hex[:12].upper()}"

        for directory in ["world", "exports", "reports", "backups", "autosave"]:
            (project_root / directory).mkdir(parents=True, exist_ok=True)

        project_json = {
            "project_id": project_id,
            "project_code": config.project_code,
            "project_name": config.project_name,
            "town_name": config.town_name,
            "temple": config.temple,
            "world_theme": config.world_theme,
            "world_size": config.world_size,
            "ground_layer": config.ground_layer,
            "starting_floor": config.starting_floor,
            "enabled_modules": list(config.enabled_modules),
            "future_modules": {name: False for name in config.future_modules},
            "scope": "OpenTibia-only",
            "certification": config.certification,
            "created_at": created_at,
            "project_path": str(project_root),
        }
        self._write_json(project_root / "project.json", project_json)

        metadata = {
            "project_id": project_id,
            "name": "PROJECT-01 NECRO",
            "display_name": config.project_name,
            "town": config.town_name,
            "version": "PROJECT-01B",
            "opentibia_compatible": True,
            "rme_version": "RME AI Studio",
            "tfs_compatible": True,
            "canary_compatible": True,
            "otservbr_compatible": True,
            "otclient_compatible": True,
            "assets_policy": "official OpenTibia/RME assets only",
            "generated_at": created_at,
            "certification": config.certification,
            "project_path": str(project_root),
        }
        self._write_json(project_root / "metadata.json", metadata)
        self._write_json(project_root / "project_metadata.json", metadata)

        manifest = {
            "project": config.project_name,
            "town": config.town_name,
            "temple": config.temple,
            "world_size": config.world_size,
            "world_theme": config.world_theme,
            "active_floor": config.starting_floor,
            "paths": {
                "world": "world/",
                "exports": "exports/",
                "reports": "reports/",
                "backups": "backups/",
                "autosave": "autosave/",
            },
            "otbm": {
                "loaded": False,
                "export_path": str(project_root / "exports" / "necro.otbm"),
                "status": "PENDING EXPORT",
            },
        }
        self._write_json(project_root / "world_manifest.json", manifest)

        state = {
            "project_id": project_id,
            "camera": {"x": config.temple_x, "y": config.temple_y, "z": config.temple_z},
            "selected_tile": config.temple,
            "current_floor": config.starting_floor,
            "tiles": [
                {
                    "x": config.temple_x,
                    "y": config.temple_y,
                    "z": config.temple_z,
                    "ground_id": 0,
                    "items": [],
                    "metadata": {"zone": "Temple", "town": config.town_name},
                }
            ],
        }
        self._write_json(project_root / "project_state.json", state)
        self._write_json(project_root / "world" / "necro_map_state.json", state)

        session = {
            "project_id": project_id,
            "safe_mode": True,
            "provider_loaded": False,
            "preview_initialized": False,
            "last_opened": created_at,
            "workspace": "Mapping Workspace",
            "message": "New world initialized. Ready for editing.",
            "project_path": str(project_root),
        }
        self._write_json(project_root / "session.json", session)

        self._write_markdown(
            project_root / "ENGINEERING_PASSPORT.md",
            [
                "# PROJECT-01 NECRO Engineering Passport",
                "",
                "- Status: IMPLEMENTATION COMPLETE",
                f"- Certification: {config.certification}",
                "- Scope: OpenTibia-only project initialization",
                "- Runtime loading: not triggered by wizard",
                "- Initial workspace: Mapping Workspace",
            ],
        )
        self._write_markdown(
            project_root / "TRACEABILITY.md",
            [
                "# PROJECT-01 NECRO Traceability",
                "",
                "- PROJECT-01B creates the NECRO project skeleton.",
                "- MAP-01 consumes project state for guided mapping.",
                "- MAP-02 consumes exports/necro.otbm as the export target.",
                "- BUILD-01 packages the workflow in the Windows executable.",
            ],
        )

        self._update_recent_projects(project_root, config, project_id, created_at)
        return {
            "project_root": project_root,
            "projects_root": self.projects_root,
            "project_id": project_id,
            "config": asdict(config),
            "message": "New world initialized. Ready for editing.",
        }

    def _update_recent_projects(
        self, project_root: Path, config: NecroProjectConfig, project_id: str, timestamp: str
    ) -> None:
        self.projects_root.mkdir(parents=True, exist_ok=True)
        path = self.projects_root / "recent_projects.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                projects = list(data.get("projects", []))
            elif isinstance(data, list):
                projects = list(data)
            else:
                projects = []
        else:
            projects = []
        entry = {
            "project_id": project_id,
            "project_name": config.project_name,
            "town_name": config.town_name,
            "path": str(project_root),
            "last_opened": timestamp,
            "temple": config.temple,
        }
        projects = [
            candidate
            for candidate in projects
            if candidate.get("path") != str(project_root)
            and not (
                candidate.get("project_name") == config.project_name
                and candidate.get("town_name", config.town_name) == config.town_name
            )
        ]
        projects.insert(0, entry)
        self._write_json(path, {"projects": projects[:10]})

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _write_markdown(path: Path, lines: List[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class NecroNewProjectWizard(QWizard):
    """Qt wizard with deterministic PROJECT-01B defaults."""

    def __init__(self, workspace_root: str | Path, parent=None) -> None:
        super().__init__(parent)
        self.projects_root = validate_user_project_path(workspace_root)
        self.setWindowTitle("PROJECT-01B NECRO New Project Wizard")
        self.setObjectName("PROJECT01BNecroNewProjectWizard")
        self.config_page = self._build_config_page()
        self.modules_page = self._build_modules_page()
        self.addPage(self.config_page)
        self.addPage(self.modules_page)

    def _build_config_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("PROJECT-01 NECRO")
        layout = QFormLayout(page)
        self.project_name = QLineEdit("Necro")
        self.town_name = QLineEdit("Necro")
        self.temple = QLineEdit("1000,1000,7")
        self.world_theme = QLineEdit("Venore Architecture")
        self.world_size = QComboBox()
        self.world_size.addItems(["2048x2048", "4096x4096", "8192x8192"])
        self.world_size.setCurrentText("4096x4096")
        self.ground_layer = QLineEdit("7")
        self.starting_floor = QLineEdit("7")
        for label, widget in [
            ("Project Name", self.project_name),
            ("Town Name", self.town_name),
            ("Temple", self.temple),
            ("World Theme", self.world_theme),
            ("World Size", self.world_size),
            ("Ground Layer", self.ground_layer),
            ("Starting Floor", self.starting_floor),
        ]:
            layout.addRow(label, widget)
        return page

    def _build_modules_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Initial Modules")
        layout = QVBoxLayout(page)
        self.module_checks: Dict[str, QCheckBox] = {}
        for name in INITIAL_MODULES:
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            self.module_checks[name] = checkbox
            layout.addWidget(checkbox)
        for name in FUTURE_MODULES:
            checkbox = QCheckBox(name)
            checkbox.setChecked(False)
            checkbox.setEnabled(False)
            self.module_checks[name] = checkbox
            layout.addWidget(checkbox)
        return page

    def config(self) -> NecroProjectConfig:
        temple = [int(part.strip()) for part in self.temple.text().split(",")]
        enabled = [name for name in INITIAL_MODULES if self.module_checks[name].isChecked()]
        return NecroProjectConfig(
            project_name=self.project_name.text().strip() or "Necro",
            town_name=self.town_name.text().strip() or "Necro",
            temple_x=temple[0],
            temple_y=temple[1],
            temple_z=temple[2],
            world_theme=self.world_theme.text().strip() or "Venore Architecture",
            world_size=self.world_size.currentText(),
            ground_layer=int(self.ground_layer.text()),
            starting_floor=int(self.starting_floor.text()),
            enabled_modules=enabled,
            future_modules=list(FUTURE_MODULES),
        )

    def create_project(self) -> Dict[str, object]:
        return NecroProjectCreator(projects_root=self.projects_root).create_project(self.config())

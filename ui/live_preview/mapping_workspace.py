"""
MAP-01A: NECRO Project Bootstrap
Core mapping workspace for OpenTibia NECRO project
"""

import json
import os
import uuid
from datetime import datetime
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .mapping_engine import OpenTibiaMappingEngine, TileCoord
from .map_brushes import (
    BrushDefinition,
    BrushShape,
    BrushType,
    GroundBrushEngine,
    MappingEngineCoreAdapter,
    MaterialDefinition,
    WorkspaceServices,
    extend_valid_item_ids,
    is_valid_item,
)
from .minimap_widget import MinimapWidget
from .viewport_factory import create_rme_viewport
from .editor_status_bar import EditorStatus
from .rme_palette import RMEPaletteWidget


@dataclass
class Tile:
    """Represents a single OpenTibia tile"""

    x: int
    y: int
    z: int
    ground_id: int = 0
    items: List[int] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Region:
    """Represents a map region"""

    name: str
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class Spawn:
    """Represents a monster spawn point"""

    x: int
    y: int
    z: int
    monster_id: int
    radius: int = 1
    metadata: Dict = field(default_factory=dict)


@dataclass
class Waypoint:
    """Represents a navigation waypoint"""

    name: str
    x: int
    y: int
    z: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class NECROProject:
    """Main NECRO project structure"""

    project_id: str
    name: str = "PROJECT-01 NECRO"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    tiles: Dict[Tuple[int, int, int], Tile] = field(default_factory=dict)
    regions: List[Region] = field(default_factory=list)
    spawns: List[Spawn] = field(default_factory=list)
    waypoints: List[Waypoint] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class MappingWorkspace:
    """Core mapping workspace for NECRO project"""

    def __init__(self):
        self.project = None
        self.project_path = None
        self.is_modified = False

    def create_necro_project(self, project_path: str) -> NECROProject:
        """Create a new NECRO project"""
        os.makedirs(project_path, exist_ok=True)

        # Create project structure
        project = NECROProject(
            project_id=str(uuid.uuid4()),
            metadata={
                "version": "1.0.0",
                "opentibia_compatible": True,
                "rme_version": "MAP-01",
            },
        )

        # Initialize with empty world
        self._initialize_empty_world(project)

        self.project = project
        self.project_path = project_path
        self.is_modified = True

        # Save project metadata
        self._save_project_metadata()

        return project

    def _initialize_empty_world(self, project: NECROProject):
        """Initialize empty OpenTibia world"""
        # Create a small starter area (100x100 tiles)
        for x in range(100):
            for y in range(100):
                tile = Tile(x=x, y=y, z=7, ground_id=0)  # Default ground
                project.tiles[(x, y, 7)] = tile

    def _save_project_metadata(self):
        """Save project metadata to disk"""
        if not self.project_path or not self.project:
            return

        metadata_path = os.path.join(self.project_path, "project_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "project_id": self.project.project_id,
                    "name": self.project.name,
                    "created_at": self.project.created_at,
                    "last_modified": self.project.last_modified,
                    "metadata": self.project.metadata,
                },
                f,
                indent=2,
            )

    def _save_world_manifest(self):
        """Save the starter world manifest used by the NECRO validation loop."""
        if not self.project_path or not self.project:
            return

        manifest_path = os.path.join(self.project_path, "world_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "project_id": self.project.project_id,
                    "world_name": "NECRO",
                    "format": "MAP-01_EDITOR_STATE",
                    "otbm_export": "PENDING_REAL_EXPORTER",
                    "state_path": "project_state.json",
                },
                f,
                indent=2,
            )

    def _save_project_state(self):
        """Persist editable map state without claiming OTBM serialization."""
        if not self.project_path or not self.project:
            return

        state_path = os.path.join(self.project_path, "project_state.json")
        payload = {
            "tiles": [asdict(tile) for tile in self.project.tiles.values()],
            "regions": [asdict(region) for region in self.project.regions],
            "spawns": [asdict(spawn) for spawn in self.project.spawns],
            "waypoints": [asdict(waypoint) for waypoint in self.project.waypoints],
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _load_project_state(self, project: NECROProject, project_path: str):
        """Load saved editable map state, falling back to a starter world."""
        state_path = os.path.join(project_path, "project_state.json")
        if not os.path.exists(state_path):
            self._initialize_empty_world(project)
            return

        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        for tile_data in state.get("tiles", []):
            tile = Tile(
                x=int(tile_data["x"]),
                y=int(tile_data["y"]),
                z=int(tile_data.get("z", 7)),
                ground_id=int(tile_data.get("ground_id", 0)),
                items=[int(item) for item in tile_data.get("items", [])],
                metadata=dict(tile_data.get("metadata", {})),
            )
            project.tiles[(tile.x, tile.y, tile.z)] = tile

        project.regions = [Region(**region) for region in state.get("regions", [])]
        project.spawns = [Spawn(**spawn) for spawn in state.get("spawns", [])]
        project.waypoints = [
            Waypoint(**waypoint) for waypoint in state.get("waypoints", [])
        ]

    def load_necro_project(self, project_path: str) -> NECROProject:
        """Load existing NECRO project"""
        metadata_path = os.path.join(project_path, "project_metadata.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"NECRO project not found at {project_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Reconstruct project (simplified for now)
        project = NECROProject(
            project_id=metadata["project_id"],
            name=metadata["name"],
            created_at=metadata["created_at"],
            last_modified=metadata["last_modified"],
            metadata=metadata["metadata"],
        )

        self._load_project_state(project, project_path)

        self.project = project
        self.project_path = project_path
        self.is_modified = False

        return project

    def save_project(self):
        """Save current project state"""
        if not self.project or not self.project_path:
            return False

        self.project.last_modified = datetime.now().isoformat()
        self._save_project_metadata()
        self._save_world_manifest()
        self._save_project_state()
        self.is_modified = False
        return True

    def get_tile(self, x: int, y: int, z: int) -> Optional[Tile]:
        """Get tile at coordinates"""
        return self.project.tiles.get((x, y, z))

    def _get_or_create_tile(self, x: int, y: int, z: int) -> Tile:
        if not self.project:
            raise RuntimeError("No NECRO project loaded")
        key = (x, y, z)
        if key not in self.project.tiles:
            self.project.tiles[key] = Tile(x=x, y=y, z=z, ground_id=0)
        return self.project.tiles[key]

    def set_ground_id(self, x: int, y: int, z: int, ground_id: int):
        """Set ground ID for tile"""
        tile = self._get_or_create_tile(x, y, z)
        tile.ground_id = ground_id
        self.is_modified = True

    def add_item(self, x: int, y: int, z: int, item_id: int):
        """Add item to tile"""
        if not is_valid_item(item_id):
            raise ValueError(
                f"Item id {item_id} is not in the MAP-01 OpenTibia allowlist"
            )
        tile = self._get_or_create_tile(x, y, z)
        if item_id not in tile.items:
            tile.items.append(item_id)
        self.is_modified = True

    def remove_item(self, x: int, y: int, z: int, item_id: int):
        """Remove item from tile"""
        tile = self.get_tile(x, y, z)
        if tile and item_id in tile.items:
            tile.items.remove(item_id)
            self.is_modified = True


class OpenTibiaMappingWorkspacePage(QMainWindow):
    """Qt MAP-01 workspace bound to the NECRO-guided mapping engine."""

    def __init__(self, workspace_root: Optional[str] = None):
        super().__init__()
        self.workspace_root = workspace_root
        self.mapping_engine = OpenTibiaMappingEngine(workspace_root or ".")
        self.ground_brush_engine = GroundBrushEngine()
        self.workspace_services = WorkspaceServices(
            MappingEngineCoreAdapter(self.mapping_engine)
        )
        self.active_tool = "select"
        self.profile_states = {}
        self.asset_registry = None
        self.selected_asset = None
        self.asset_load_error = ""
        self.reference_profile = {}
        self.reference_load_error = ""
        self.pending_mapper_plan = None
        self.pending_mapper_report = {}
        self.active_brush_family = "Terrain"
        self.editor_status = EditorStatus()
        self.professional_palette_categories = [
            "Terrain Palette",
            "Doodad Palette",
            "Item Palette",
            "House Palette",
            "Waypoint Palette",
            "Zone Palette",
            "Monster Palette",
            "Npc Palette",
            "RAW Palette",
        ]

        self.viewport = create_rme_viewport()
        self.viewport.setObjectName("UX03OTBMViewport")
        self.viewport.setMinimumSize(900, 540)
        self.start_panel = QLabel(
            "New NECRO  |  Open Project  |  Open world.otbm reference read-only"
        )
        self.start_panel.setObjectName("MEP01EditorStartPanel")
        self.start_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coordinate_jump = QLineEdit()
        self.coordinate_jump.setPlaceholderText("x,y,z")
        self.coordinate_jump.returnPressed.connect(self.jump_to_coordinate)
        self.brush_radius = QComboBox()
        self.brush_radius.setObjectName("MEP01BrushSize")
        self.brush_radius.addItems(["1", "2", "3", "5", "7", "9", "12"])
        self.brush_shape = QComboBox()
        self.brush_shape.setObjectName("MERGE07ABrushShape")
        self.brush_shape.addItems(["Square", "Circle"])
        self.brush_family_selector = QComboBox()
        self.brush_family_selector.setObjectName("MEP01BrushFamily")
        self.brush_family_selector.addItems(
            [
                "Terrain",
                "Mountain",
                "Wall",
                "Border",
                "Nature",
                "Decoration",
                "Raw",
                "Quest",
                "House",
            ]
        )
        self.brush_family_selector.currentTextChanged.connect(
            self._set_active_brush_family
        )
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Coordinate"))
        controls.addWidget(self.coordinate_jump)
        controls.addWidget(QLabel("Brush"))
        controls.addWidget(self.brush_family_selector)
        controls.addWidget(QLabel("Size"))
        controls.addWidget(self.brush_radius)
        controls.addWidget(QLabel("Shape"))
        controls.addWidget(self.brush_shape)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.start_panel)
        layout.addWidget(self.viewport)

        central = QWidget()
        central.setLayout(layout)
        central.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setCentralWidget(central)

        self._build_toolbar()
        self._build_editor_menu()
        self._load_asset_registry()
        self._load_reference_world_profile()
        self._build_ux03_docks()
        self._load_recent_necro_project_if_available()
        self.viewport.tileSelected.connect(self._handle_tile_selected)
        self.viewport.tileHovered.connect(self._handle_tile_hovered)
        self.viewport.selectionCommitted.connect(self._handle_selection_committed)
        QTimer.singleShot(0, self._apply_mapping_mode_defaults)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Mapping")
        toolbar.setObjectName("MEP01MappingToolbar")
        self.addToolBar(toolbar)
        for text, handler in [
            ("New", lambda: self._log("New NECRO requested.")),
            ("Open", lambda: self._log("Open Project requested.")),
            ("Save", lambda: self._log("Save requested.")),
            ("Undo", self.undo),
            ("Redo", self.redo),
            ("Cut", lambda: self._log("Cut requested.")),
            ("Copy", self.copy_selection),
            ("Paste", self.paste_clipboard),
            ("Rotate", self.rotate_clipboard),
            ("Mirror", self.mirror_clipboard),
            ("Expand", self.expand_selection),
            ("Bookmark", self.add_bookmark),
            ("Repair", self.repair_visual_zones),
            ("Brush", self._activate_brush),
            ("Erase", lambda: self._set_tool("erase")),
            ("Select", lambda: self._set_tool("select")),
            ("Floor", lambda: self._log(f"Floor {self.viewport.floor}")),
            ("Zoom", lambda: self._log(f"Zoom {int(self.viewport.zoom * 100)}%")),
            ("Export Status", self.refresh_export_status),
        ]:
            action = QAction(text, self)
            action.setObjectName(f"MEP01Toolbar_{text.replace(' ', '_')}")
            action.triggered.connect(handler)
            toolbar.addAction(action)
        self.profile_selector = QComboBox()
        self.profile_selector.addItems(
            [
                "Mapping",
                "AI Review",
                "Validation",
                "Export",
                "Performance",
                "Architecture",
            ]
        )
        self.profile_selector.currentTextChanged.connect(self.apply_workspace_profile)
        self.active_tool_label = QLabel("Tool: Select")
        toolbar.addWidget(self.profile_selector)
        toolbar.addWidget(self.active_tool_label)

    def _build_editor_menu(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.setObjectName("MEP01EditorMenu")
        for title in [
            "File",
            "Edit",
            "Map",
            "Select",
            "View",
            "Window",
            "Floor",
            "Scripts",
            "AI",
            "Help",
        ]:
            menu = menu_bar.addMenu(title)
            menu.setObjectName(f"MEP01EditorMenu_{title}")
        view_menu = menu_bar.findChild(
            type(menu_bar.addMenu("_tmp")), "MEP01EditorMenu_View"
        )
        menu_bar.removeAction(menu_bar.actions()[-1])
        if view_menu is not None:
            engineering = QAction("Engineering Dashboard", self)
            engineering.setObjectName("MEP01ViewEngineeringDashboardAction")
            engineering.triggered.connect(
                lambda: self.apply_workspace_profile("AI Review")
            )
            view_menu.addAction(engineering)

    def _activate_brush(self) -> None:
        self.active_tool = "brush"
        self.active_tool_label.setText("Tool: Brush")
        self.current_brush_label.setText(f"brush: {self.active_brush_family}")
        self.statusBar().showMessage(self._status_text())

    def _apply_mapping_mode_defaults(self) -> None:
        self.asset_dock.show()
        self.inspector_dock.show()
        for dock in [
            self.project_dock,
            self.brush_dock,
            self.minimap_dock,
            self.layer_dock,
            self.ai_dock,
            self.status_dock,
            self.bottom_dock,
        ]:
            dock.hide()
        self._log("Brush tool active")

    def _set_tool(self, tool: str) -> None:
        self.active_tool = tool
        self.active_tool_label.setText(f"Tool: {tool.title()}")
        self.current_brush_label.setText(
            f"brush: {self.active_brush_family if tool == 'brush' else tool}"
        )
        self.statusBar().showMessage(self._status_text())
        self._log(f"{tool.title()} tool active")

    def _set_active_brush_family(self, family: str) -> None:
        self.active_brush_family = family
        if self.active_tool == "brush":
            self.active_tool_label.setText(f"Tool: {family} Brush")
        self.current_brush_label.setText(f"brush: {family}")
        self.statusBar().showMessage(self._status_text())
        self._log(f"Brush family active: {family}")

    def _build_ux03_docks(self) -> None:
        self.coordinate_label = QLabel(
            "World: No OTBM loaded | Floor: 7 | X: -- | Y: -- | Z: --"
        )
        self.project_path_label = QLabel("--")
        self.selection_type = QLabel("None")
        self.selection_coordinates = QLabel("--")
        self.asset_id_label = QLabel("--")
        self.asset_client_id_label = QLabel("--")
        self.asset_name_label = QLabel("--")
        self.asset_category_label = QLabel("--")
        self.asset_brush_label = QLabel("--")
        self.asset_source_label = QLabel("--")
        self.layer_toggles = {}

        self.project_dock = self._dock("Project Explorer", self._project_tree())
        self.asset_dock = self._dock("Palette", self._asset_tabs())
        self.asset_dock.setObjectName("MEP01PaletteDock")
        self.brush_dock = self._dock("Brush Browser", self._brush_tabs())
        self.minimap = MinimapWidget()
        self.minimap.setObjectName("MEP01WorldMinimap")
        self.minimap.navigationRequested.connect(self._handle_minimap_navigation)
        self.minimap_dock = self._dock("World Minimap", self.minimap)
        self.layer_dock = self._dock("Layer Manager", self._layer_panel())
        self.inspector_dock = self._dock(
            "Properties Inspector", self._properties_tabs()
        )
        self.inspector_dock.setObjectName("PMX02R1PropertiesDock")
        self.ai_dock = self._dock("AI Engineering", self._ai_engineering_panel())
        self.status_dock = self._dock("Engineering Status", QLabel("Safe Mode active"))
        self.bottom_dock = self._dock("Operations Center", self._operations_tabs())

        for dock in [
            self.project_dock,
            self.asset_dock,
            self.brush_dock,
            self.minimap_dock,
            self.layer_dock,
            self.inspector_dock,
            self.ai_dock,
            self.status_dock,
            self.bottom_dock,
        ]:
            dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable
                | QDockWidget.DockWidgetFeature.DockWidgetFloatable
                | QDockWidget.DockWidgetFeature.DockWidgetClosable
            )

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.asset_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.brush_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.minimap_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.layer_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.status_dock)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)
        self.asset_dock.setMinimumWidth(280)
        self.asset_dock.setMaximumWidth(320)
        self.inspector_dock.setMinimumWidth(220)
        self.inspector_dock.setMaximumWidth(320)
        self.resizeDocks(
            [self.asset_dock, self.inspector_dock],
            [290, 260],
            Qt.Orientation.Horizontal,
        )
        self.resizeDocks([self.bottom_dock], [150], Qt.Orientation.Vertical)
        self.project_dock.hide()
        self.brush_dock.hide()
        self.minimap_dock.hide()
        self.layer_dock.hide()
        self.ai_dock.hide()
        self.status_dock.hide()
        self.bottom_dock.hide()
        self.viewport_dominance_ratio = 0.82
        self.status_project_label = QLabel("Project: NECRO")
        self.status_town_label = QLabel("Town: Necro")
        self.status_x_label = QLabel("x: 1000")
        self.status_y_label = QLabel("y: 1000")
        self.status_z_label = QLabel("z: 7")
        self.zoom_label = QLabel("zoom: 100%")
        self.selected_item_label = QLabel("item: none")
        self.current_brush_label = QLabel("brush: Terrain")
        self.safe_mode_label = QLabel("Safe Mode")
        for label in [
            self.status_project_label,
            self.status_town_label,
            self.status_x_label,
            self.status_y_label,
            self.status_z_label,
            self.zoom_label,
            self.selected_item_label,
            self.current_brush_label,
            self.safe_mode_label,
        ]:
            self.statusBar().addPermanentWidget(label)
        self.statusBar().showMessage(self._status_text())
        self.apply_workspace_profile("Mapping")

    def _dock(self, title: str, widget: QWidget) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        return dock

    def _properties_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("PMX02R1PropertiesTabs")
        tabs.addTab(self._inspector_panel(), "Selection")
        tabs.addTab(
            self._property_list("Brush", ["Family", "Size", "Shape", "Selected Brush"]),
            "Brush",
        )
        tabs.addTab(
            self._property_list("Tile", ["Ground", "Items", "Flags", "House", "Spawn"]),
            "Tile",
        )
        tabs.addTab(self._layer_panel(), "Layer")
        tabs.addTab(
            self._property_list(
                "AI Suggestions",
                [
                    "Proposal-only mode",
                    "Improve selected area",
                    "Generate original extension",
                    "Review before apply",
                ],
            ),
            "AI Suggestions",
        )
        tabs.addTab(
            self._property_list(
                "Context",
                [
                    "Current selection",
                    "Reference world profile",
                    "Asset registry",
                    "Necro constraints",
                ],
            ),
            "Context",
        )
        tabs.addTab(
            self._property_list(
                "Inspector", ["ClientID", "SpriteID", "Source", "Flags"]
            ),
            "Inspector",
        )
        return tabs

    def _property_list(self, object_name: str, values: list[str]) -> QListWidget:
        items = QListWidget()
        items.setObjectName(f"PMX02R1{object_name.replace(' ', '')}")
        items.addItems(values)
        return items

    def _project_tree(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setObjectName("UX03ProjectExplorer")
        tree.setHeaderLabels(["OpenTibia Project", "State"])
        root = QTreeWidgetItem(["Current World", "NECRO"])
        necro = QTreeWidgetItem(["NECRO", "OpenTibia Project"])
        entries = [
            ("world.otbm", "Reference/target world"),
            ("exports", "Writable"),
            ("reports", "Writable"),
            ("scripts", "Project tools"),
            ("layers", "Ground/Borders/Nature/Items"),
            ("bookmarks", "Navigation"),
            ("towns", "Necro"),
            ("houses", "Editable"),
            ("waypoints", "Editable"),
            ("quests", "Original layouts"),
            ("spawns", "Editable"),
        ]
        for name, state in entries:
            necro.addChild(QTreeWidgetItem([name, state]))
        root.addChild(necro)
        tree.addTopLevelItem(root)
        root.setExpanded(True)
        necro.setExpanded(True)
        return tree

    def _asset_tabs(self) -> QTabWidget:
        palette = RMEPaletteWidget(
            self.asset_registry,
            on_asset_selected=self._asset_selected,
            on_tool_selected=self._palette_tool_selected,
            on_brush_size_changed=lambda value: self.brush_radius.setCurrentText(str(value)),
            on_brush_shape_changed=self.brush_shape.setCurrentText,
            on_doodad_thickness_changed=lambda value: self._log(f"Doodad thickness: {value}"),
        )
        self.asset_lists = palette.asset_lists
        self.asset_search = palette.asset_search
        self.asset_search_results = palette.asset_search_results
        return palette

    def _brush_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("UX03BrushBrowser")
        if self.asset_registry is None:
            brushes = QListWidget()
            brushes.setObjectName("UX03OfficialBrushList")
            brushes.addItem(
                f"OpenTibia assets could not be loaded. {self.asset_load_error}"
            )
            tabs.addTab(brushes, "Official Brushes")
        else:
            brush_groups = {
                "Terrain Brush": ("ground", "terrain", "grass", "earth", "sand"),
                "Mountain Brush": ("mountain", "rock"),
                "Wall Brush": ("wall",),
                "Border Brush": ("border",),
                "Nature Brush": ("tree", "nature", "bush", "grass"),
                "Decoration Brush": ("deco", "decoration", "furniture"),
                "Raw Brush": ("raw", "item"),
                "Quest Brush": ("quest", "chest", "key", "scroll"),
                "House Brush": ("house", "door", "bed"),
            }
            for tab_name, tokens in brush_groups.items():
                brushes = QListWidget()
                brushes.setObjectName(f"MEP01{tab_name.replace(' ', '')}")
                count = 0
                for brush in self.asset_registry.brushes:
                    if brush.item_id is None:
                        continue
                    brush_asset = self.asset_registry.asset(int(brush.item_id))
                    if (
                        brush_asset is None
                        or brush_asset.render_status != "SPRITE_BACKED"
                    ):
                        continue
                    haystack = (
                        f"{brush.name} {brush.category} {brush.brush_type}".lower()
                    )
                    if any(token in haystack for token in tokens):
                        item = QListWidgetItem(
                            f"{brush.name} | item {brush.item_id} | {brush.category} | {brush.source_file}"
                        )
                        item.setData(Qt.ItemDataRole.UserRole, brush.item_id)
                        brushes.addItem(item)
                        count += 1
                if count == 0:
                    for asset in self._assets_for_professional_category(
                        tab_name.replace(" Brush", "")
                    )[:50]:
                        item = QListWidgetItem(
                            f"{asset.name} | item {asset.asset_id} | sprite {asset.client_id or asset.asset_id} | {asset.category}"
                        )
                        item.setData(Qt.ItemDataRole.UserRole, asset.asset_id)
                        brushes.addItem(item)
                brushes.itemClicked.connect(self._asset_selected)
                tabs.addTab(brushes, tab_name)
        return tabs

    def _simple_tabs(
        self, object_name: str, sections: dict[str, list[str]]
    ) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName(object_name)
        for title, values in sections.items():
            items = QListWidget()
            items.addItems(values)
            tabs.addTab(items, title)
        return tabs

    def _operations_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("UX03OperationsTabs")
        tabs.addTab(self.console_output, "Console")
        for title, values in {
            "Runtime": ["Packaged validation available"],
            "Logs": ["Startup log: dist/RME AI Studio/logs/RME_AI_Studio_startup.log"],
            "Problems": ["No active proposal problems"],
            "Build": ["BUILD-01 script integrated"],
            "Performance": ["Viewport dominant layout active"],
        }.items():
            items = QListWidget()
            items.addItems(values)
            tabs.addTab(items, title)
        return tabs

    def _ai_engineering_panel(self) -> QTabWidget:
        from core.opentibia.ai_engineering import PROMPT_LIBRARY

        tabs = QTabWidget()
        tabs.setObjectName("UX03AIEngineeringPanel")

        builder = QWidget()
        builder_layout = QVBoxLayout(builder)
        self.ai_prompt_input = QPlainTextEdit()
        self.ai_prompt_input.setObjectName("UX03PromptBuilderInput")
        self.ai_prompt_input.setPlaceholderText(
            "Describe an original OpenTibia change to propose."
        )
        self.ai_template_selector = QComboBox()
        self.ai_template_selector.setObjectName("UX03PromptTemplateSelector")
        self.ai_template_selector.addItems(list(PROMPT_LIBRARY.keys()))
        self.ai_provider_selector = QComboBox()
        self.ai_provider_selector.setObjectName("UX03ProviderSelector")
        self.ai_provider_selector.addItems(
            ["Manual Review", "OpenAI", "Local Provider"]
        )
        self.ai_build_prompt_button = QPushButton("Build Enriched Prompt")
        self.ai_build_prompt_button.clicked.connect(self.build_enriched_prompt)
        self.ai_enriched_prompt = QPlainTextEdit()
        self.ai_enriched_prompt.setObjectName("UX03EnrichedPromptPreview")
        self.ai_enriched_prompt.setReadOnly(True)
        builder_layout.addWidget(self.ai_template_selector)
        builder_layout.addWidget(self.ai_provider_selector)
        builder_layout.addWidget(self.ai_prompt_input)
        builder_layout.addWidget(self.ai_build_prompt_button)
        builder_layout.addWidget(self.ai_enriched_prompt)
        tabs.addTab(builder, "Prompt Builder")

        engineering_prompt = QPlainTextEdit()
        engineering_prompt.setObjectName("PMX02R1EngineeringPrompt")
        engineering_prompt.setReadOnly(True)
        engineering_prompt.setPlainText(
            "AI proposes original OpenTibia changes from context. The editor renders; the human approves."
        )
        tabs.addTab(engineering_prompt, "Engineering Prompt")

        library = QListWidget()
        library.setObjectName("UX03PromptLibrary")
        for name, text in PROMPT_LIBRARY.items():
            library.addItem(f"{name}: {text}")
        tabs.addTab(library, "Prompt Library")

        context = QListWidget()
        context.setObjectName("UX03ContextBuilder")
        context.addItem("Current project")
        context.addItem("Current town")
        context.addItem("Current coordinates")
        context.addItem("Blueprint")
        context.addItem("Asset Registry")
        context.addItem("Current selection")
        context.addItem("Reference World knowledge")
        context.addItem("Engineering constraints")
        tabs.addTab(context, "AI Context")

        reference = QListWidget()
        reference.setObjectName("MEP01ReferenceWorldKnowledge")
        if self.reference_profile:
            reference.addItem(f"Source: {self.reference_profile.get('source_path')}")
            reference.addItem(
                f"Sampled tiles: {self.reference_profile.get('sampled_tile_count')}"
            )
            reference.addItem(
                f"Sampled items: {self.reference_profile.get('sampled_item_count')}"
            )
            for domain in self.reference_profile.get("learning_domains", [])[:16]:
                reference.addItem(f"Pattern domain: {domain}")
            reference.addItem(str(self.reference_profile.get("copy_policy")))
        else:
            reference.addItem(
                f"Reference World unavailable: {self.reference_load_error}"
            )
        tabs.addTab(reference, "Reference World Knowledge")
        tabs.addTab(
            self._ai_generator_list(
                "Reference Context",
                [
                    "projects/world/world.otbm read-only",
                    "Pattern extraction only",
                    "Never copy coordinates",
                    "Never clone areas",
                ],
            ),
            "Reference Context",
        )

        registry = QListWidget()
        registry.setObjectName("MEP01AIAssetRegistry")
        if self.asset_registry is not None:
            health = self.asset_registry.health_report()
            registry.addItem(f"Assets: {health.get('asset_count')}")
            registry.addItem(f"Categories: {health.get('category_count')}")
            registry.addItem(f"Brushes: {health.get('brush_count')}")
            registry.addItem(f"Tilesets: {health.get('tileset_count')}")
        else:
            registry.addItem(f"Asset Registry unavailable: {self.asset_load_error}")
        tabs.addTab(registry, "Asset Registry")

        blueprint = QListWidget()
        blueprint.setObjectName("MEP01Blueprint")
        blueprint.addItems(
            [
                "Town: Necro",
                "Temple: 1000 1000 7",
                "Architecture: Venore-inspired, original layout",
                "Districts: Temple, Depot, Shops, Residential, Roads, Nature",
                "Hunts: Oramond-inspired and Krailos-inspired, never copied",
            ]
        )
        tabs.addTab(blueprint, "Blueprint")
        tabs.addTab(
            self._ai_generator_list(
                "Blueprint Generator",
                ["Town blueprint", "Road graph", "District plan", "Original layout"],
            ),
            "Blueprint Generator",
        )
        for title, values in {
            "Zone Generator": [
                "Protection zones",
                "No-PVP zones",
                "Quest zones",
                "Hunt zones",
            ],
            "Architecture Generator": [
                "Venore style",
                "Depot structure",
                "House blocks",
                "Bridge transitions",
            ],
            "NPC Generator": [
                "Shop placement",
                "Temple services",
                "Travel NPCs",
                "Dialogue anchors",
            ],
            "Quest Generator": [
                "Quest anchors",
                "Reward rooms",
                "Progression gates",
                "Original chains",
            ],
            "Dungeon Generator": [
                "Hunt loops",
                "Spawn rhythm",
                "Exit safety",
                "Level range constraints",
            ],
            "Terrain Generator": [
                "Ground transitions",
                "Borders",
                "Nature density",
                "Mountain composition",
            ],
            "Improvement Suggestions": [
                "Clean borders",
                "Improve navigation",
                "Balance density",
                "Review style",
            ],
            "Natural Language Commands": [
                "Generate a hunt inspired by Issavi for levels 300-350.",
                "Create a new depot inspired by Thais.",
                "Expand this city toward the north.",
            ],
        }.items():
            tabs.addTab(self._ai_generator_list(title, values), title)

        history = QListWidget()
        history.setObjectName("MEP01GenerationHistory")
        history.addItem("No AI generation applied")
        history.addItem("AI proposals require human approval before workspace mutation")
        tabs.addTab(history, "Generation History")

        proposal = QPlainTextEdit()
        proposal.setObjectName("MEP01ProposalPreview")
        proposal.setReadOnly(True)
        proposal.setPlainText(
            "Proposal preview will contain original OpenTibia changes after prompt enrichment."
        )
        tabs.addTab(proposal, "Proposal Preview")

        critic = QListWidget()
        critic.setObjectName("MEP01CriticResult")
        critic.addItem("Critic result: pending proposal")
        critic.addItem(
            "Checks: OpenTibia compatibility, no copied layouts, asset IDs, OTBM constraints"
        )
        tabs.addTab(critic, "Critic Result")

        validation = QListWidget()
        validation.setObjectName("UX03EngineeringValidation")
        validation.addItem("Critic status: pending proposal")
        validation.addItem("Human approval required before apply")
        validation.addItem("Copy policy: learn patterns, never copy maps")
        tabs.addTab(validation, "Engineering Validation")
        validation_compat = QListWidget()
        validation_compat.setObjectName("UX03EngineeringValidationCompat")
        validation_compat.addItem("Critic status: pending proposal")
        validation_compat.addItem("Human approval required before apply")
        validation_compat.addItem("Copy policy: learn patterns, never copy maps")
        tabs.addTab(validation_compat, "Validation")
        approval = QListWidget()
        approval.setObjectName("UX03ApprovalQueue")
        approval.addItem("No approval pending")
        approval.addItem("Human approval required before applying AI proposals")
        tabs.addTab(approval, "Approval Queue")
        human = QListWidget()
        human.setObjectName("MEP01HumanApproval")
        human.addItem("Pending proposal")
        human.addItem("Review, approve, or reject before any generated map operation")
        tabs.addTab(human, "Human Approval")
        tabs.addTab(
            self._ai_generator_list(
                "Apply / Reject",
                [
                    "Apply disabled until approval",
                    "Reject proposal",
                    "Return to prompt",
                    "Record history",
                ],
            ),
            "Apply / Reject",
        )
        return tabs

    def _ai_generator_list(self, object_name: str, values: list[str]) -> QListWidget:
        items = QListWidget()
        items.setObjectName(f"PMX02R1{object_name.replace(' ', '').replace('/', '')}")
        items.addItems(values)
        return items

    def _layer_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        for layer in [
            "Ground",
            "Borders",
            "Nature",
            "Buildings",
            "Items",
            "Creatures",
            "Waypoints",
            "Spawns",
            "Zones",
            "Metadata",
        ]:
            toggle = QCheckBox(layer)
            toggle.setChecked(True)
            toggle.toggled.connect(
                lambda checked, name=layer: self._layer_changed(name, checked)
            )
            self.layer_toggles[layer] = toggle
            layout.addWidget(toggle)
        return panel

    def _inspector_panel(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        form.addRow("Selection", self.selection_type)
        form.addRow("Coordinates", self.selection_coordinates)
        form.addRow("Viewport", self.coordinate_label)
        form.addRow("Project Path", self.project_path_label)
        form.addRow("Item ID", self.asset_id_label)
        form.addRow("Client ID", self.asset_client_id_label)
        form.addRow("Name", self.asset_name_label)
        form.addRow("Category", self.asset_category_label)
        form.addRow("Brush", self.asset_brush_label)
        form.addRow("Source", self.asset_source_label)
        return panel

    def _load_asset_registry(self) -> None:
        try:
            from core.opentibia.assets.asset_registry import AssetRegistry

            self.asset_registry = AssetRegistry(self.workspace_root).load()
            extend_valid_item_ids(
                asset.asset_id
                for asset in self.asset_registry.assets.values()
                if asset.render_status == "SPRITE_BACKED"
            )
            self._log(
                f"Official OpenTibia assets loaded: assets={self.asset_registry.health.asset_count} "
                f"sprite_backed={self.asset_registry.health.sprite_backed_asset_count} "
                f"categories={self.asset_registry.health.category_count} brushes={self.asset_registry.health.brush_count}"
            )
        except Exception as exc:
            self.asset_registry = None
            self.asset_load_error = f"{type(exc).__name__}: {exc}"
            self._log(f"OpenTibia assets could not be loaded. {self.asset_load_error}")

    def _load_reference_world_profile(self) -> None:
        try:
            from core.opentibia.reference_learning import ReferenceWorldAnalyzer

            self.reference_profile = (
                ReferenceWorldAnalyzer(max_nodes=12000).analyze().to_dict()
            )
            self._log(
                "Reference world learning profile loaded: "
                f"sampled_tiles={self.reference_profile.get('sampled_tile_count')} "
                f"truncated={self.reference_profile.get('parse_truncated')}"
            )
        except Exception as exc:
            self.reference_profile = {}
            self.reference_load_error = f"{type(exc).__name__}: {exc}"
            self._log(
                f"Reference world learning profile unavailable. {self.reference_load_error}"
            )

    def build_enriched_prompt(self) -> str:
        from core.opentibia.ai_engineering import PromptBuilder, context_from_workspace

        raw_prompt = (
            self.ai_prompt_input.toPlainText()
            or "Create an original OpenTibia proposal for the current workspace."
        )
        selected_asset = (
            f"{self.selected_asset.name} ({self.selected_asset.asset_id})"
            if self.selected_asset is not None
            else "None"
        )
        try:
            self.pending_mapper_plan, self.pending_mapper_report = (
                self.mapping_engine.create_mapper_proposal(raw_prompt)
            )
            planner_audit = self.mapping_engine.workspace_core.planner.audit()
            planner_summary = (
                f"{self.pending_mapper_report.get('status')} proposal, "
                f"database={planner_audit['database_available']}, "
                f"memory={planner_audit['visual_memory_available']}, "
                f"regions={len(self.pending_mapper_plan.regions)}, "
                f"routes={len(self.pending_mapper_plan.routes)}"
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self.pending_mapper_plan = None
            self.pending_mapper_report = {
                "status": "BLOCKED",
                "error": f"{type(exc).__name__}: {exc}",
            }
            planner_summary = self.pending_mapper_report["error"]
        context = context_from_workspace(
            project=getattr(self, "project_name", "Necro"),
            town=getattr(self, "town_name", "Necro"),
            coordinates=self.selection_coordinates.text(),
            selected_asset=selected_asset,
            selection=self.selection_type.text(),
            asset_health=(
                self.asset_registry.health_report()
                if self.asset_registry is not None
                else {}
            ),
            reference_profile=self.reference_profile,
            planner_summary=planner_summary,
        )
        prompt = PromptBuilder().build(
            raw_prompt, context, self.ai_template_selector.currentText()
        )
        self.ai_enriched_prompt.setPlainText(prompt)
        self._log("Built enriched AI engineering prompt with cached Mapper proposal.")
        return prompt

    def _assets_for_professional_category(self, category: str):
        if self.asset_registry is None:
            return []
        direct = {
            "Terrain": "Grounds",
            "Grounds": "Grounds",
            "Nature": "Nature",
            "Mountains": "Mountains",
            "Walls": "Walls",
            "Borders": "Borders",
            "Water": "Water",
            "Raw": "Raw Items",
            "Raw Items": "Raw Items",
            "Decoration": "Decoration",
            "House": "Houses",
        }
        if category in direct:
            assets = self.asset_registry.sprite_backed_assets_by_category(
                direct[category]
            )
        else:
            assets = []
        search_tokens = {
            "Construction": ("construction", "brick", "stone", "wood"),
            "Quest": ("chest", "key", "scroll", "reward"),
            "Magic": ("magic", "rune", "spell", "crystal"),
            "Cave": ("cave", "rock", "stalagmite", "mushroom"),
            "Doodads": ("statue", "banner", "torch", "sign"),
        }
        for token in search_tokens.get(category, ()):
            assets.extend(
                asset
                for asset in self.asset_registry.search(token)
                if asset.render_status == "SPRITE_BACKED"
            )
        unique = {}
        for asset in assets:
            if asset.render_status != "SPRITE_BACKED":
                continue
            unique[asset.asset_id] = asset
        return sorted(unique.values(), key=lambda item: (item.name, item.asset_id))

    def _populate_asset_list(self, category: str, query: str) -> None:
        items = self.asset_lists[category]
        items.clear()
        if query:
            assets = [
                asset
                for asset in self._assets_for_professional_category(category)
                if query.lower() in asset.name.lower() or query in str(asset.asset_id)
            ]
        else:
            assets = self._assets_for_professional_category(category)
        for asset in assets[:1000]:
            sprite_id = (
                asset.client_id if asset.client_id is not None else asset.asset_id
            )
            item = QListWidgetItem(
                f"{asset.name} | ID {asset.asset_id} | Sprite {sprite_id} | Brush {asset.brush} | {asset.category}"
            )
            item.setData(Qt.ItemDataRole.UserRole, asset.asset_id)
            items.addItem(item)

    def _filter_asset_lists(self, text: str) -> None:
        if self.asset_registry is None:
            return
        for category in self.asset_lists:
            self._populate_asset_list(category, text)
        self.asset_search_results.clear()
        if text:
            for asset in self.asset_registry.search(text)[:500]:
                if asset.render_status != "SPRITE_BACKED":
                    continue
                item = QListWidgetItem(
                    f"{asset.name} | ID {asset.asset_id} | {asset.category} | {asset.source_file}"
                )
                item.setData(Qt.ItemDataRole.UserRole, asset.asset_id)
                self.asset_search_results.addItem(item)

    def _asset_selected(self, item: QListWidgetItem) -> None:
        if self.asset_registry is None:
            return
        asset_id = item.data(Qt.ItemDataRole.UserRole)
        if asset_id is None:
            return
        asset = self.asset_registry.asset(int(asset_id))
        if asset is None:
            return
        if asset.render_status != "SPRITE_BACKED":
            self._log(
                f"Rejected asset {asset.asset_id}: no real client sprite backing."
            )
            return
        self.selected_asset = asset
        self.asset_id_label.setText(str(asset.asset_id))
        self.asset_client_id_label.setText(
            str(asset.client_id) if asset.client_id is not None else "--"
        )
        self.asset_name_label.setText(asset.name)
        self.asset_category_label.setText(asset.category)
        self.asset_brush_label.setText(asset.brush)
        self.asset_source_label.setText(asset.source_file)
        self.selection_type.setText("Asset")
        self.selection_coordinates.setText(f"Selected item {asset.asset_id}")
        self.selected_item_label.setText(f"item: {asset.asset_id}")
        self.viewport.set_selected_asset_reference(asset)
        self._activate_brush()
        self.statusBar().showMessage(self._status_text())
        self._log(f"Selected asset {asset.asset_id}: {asset.name}")

    def _palette_tool_selected(self, tool: str) -> None:
        family = {
            "optional-border": "Border",
            "door-normal": "Wall", "door-locked": "Wall",
            "door-magic": "Wall", "door-quest": "Wall",
            "door-hatch": "Wall", "window-normal": "Wall",
        }.get(tool)
        if family is not None:
            self.brush_family_selector.setCurrentText(family)
        if tool == "erase":
            self._set_tool("erase")
        else:
            self._set_tool("brush")
        self._log(f"RME palette tool selected: {tool}")

    def _layer_changed(self, layer: str, checked: bool) -> None:
        state = "visible" if checked else "hidden"
        self.coordinate_label.setText(
            f"Layer {layer}: {state} | Floor: {self.viewport.floor}"
        )

    def apply_workspace_profile(self, profile: str) -> None:
        mapping_visible = {
            self.asset_dock,
            self.inspector_dock,
        }
        ai_visible = {
            self.project_dock,
            self.ai_dock,
            self.status_dock,
            self.bottom_dock,
        }
        visible = ai_visible if profile == "AI Review" else mapping_visible
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(dock in visible)

    def _handle_tile_selected(self, x: int, y: int, z: int) -> None:
        coord = TileCoord(x, y, z)
        self.selection_type.setText("Tile")
        self.selection_coordinates.setText(f"{x}, {y}, {z}")
        self.coordinate_label.setText(
            f"World: No OTBM loaded | Floor: {z} | X: {x} | Y: {y} | Z: {z}"
        )
        self._set_status_coordinates(x, y, z)
        if self.active_tool == "brush":
            self._paint_at(coord)
        elif self.active_tool == "erase":
            self.mapping_engine.erase([coord])
            self._log(f"Erased tile {coord.x},{coord.y},{coord.z}")
            self._refresh_viewport()
        else:
            self.mapping_engine.select_single(coord)
            self._refresh_viewport()

    def _handle_tile_hovered(self, x: int, y: int, z: int) -> None:
        self.coordinate_label.setText(
            f"World: NECRO | Floor: {z} | Hover X: {x} | Y: {y} | Z: {z}"
        )
        self._set_status_coordinates(x, y, z)
        if self.active_tool == "brush" and self._active_is_ground_brush():
            brush = self._safe_ground_brush_definition()
            if brush is None:
                self.viewport.set_preview_tiles(set())
                return
            action = self.ground_brush_engine.preview(
                brush,
                (x, y, z),
                size=int(self.brush_radius.currentText()),
                shape=self._selected_brush_shape(),
            )
            self.viewport.set_preview_tiles(
                {(m.x, m.y, m.z) for m in action.mutations}
            )
            self.statusBar().showMessage(
                "Ground Brush | "
                f"material:{brush.material.name} | "
                f"size:{self.brush_radius.currentText()} | "
                f"shape:{self._selected_brush_shape().value} | "
                f"preview:{len(action.mutations)} | valid | autoborder pending"
            )
        else:
            self.viewport.set_preview_tiles(set())

    def _handle_selection_committed(
        self, x1: int, y1: int, x2: int, y2: int, z: int
    ) -> None:
        from .map_selection import SelectionSessionMode

        selection_mode = (
            SelectionSessionMode.INTERNAL
            if self.active_tool in {"brush", "erase"}
            else SelectionSessionMode.EXTERNAL
        )
        self.mapping_engine.select_rectangle(
            TileCoord(x1, y1, z),
            TileCoord(x2, y2, z),
            mode=selection_mode,
        )
        self.selection_type.setText("Rectangle")
        self.selection_coordinates.setText(f"{x1},{y1},{z} -> {x2},{y2},{z}")
        self._set_status_coordinates(x1, y1, z)
        if self.active_tool == "brush":
            if self._active_is_ground_brush():
                brush = self._safe_ground_brush_definition()
                if brush is None:
                    self._refresh_viewport()
                    return
                self.ground_brush_engine.commit_coords(
                    self.workspace_services,
                    brush,
                    (selected.key() for selected in self.mapping_engine.selection_coords()),
                )
                self._log(
                    f"Ground-painted selection {len(self.mapping_engine.selection)} tiles"
                )
            else:
                brush, role = self._brush_role()
                self.mapping_engine.paint(
                    self.mapping_engine.selection_coords(), brush=brush, role=role
                )
                self._log(
                    f"Painted selection {len(self.mapping_engine.selection)} tiles"
                )
        elif self.active_tool == "erase":
            selected_count = len(self.mapping_engine.selection)
            self.mapping_engine.erase(
                self.mapping_engine.selection_coords(),
                name="Erase selected tiles",
            )
            self._log(f"Erased selection {selected_count} tiles")
        self._refresh_viewport()

    def _brush_role(self) -> tuple[str, str]:
        family = self.active_brush_family.lower()
        mapping = {
            "terrain": ("terrain", "ground"),
            "mountain": ("mountain", "mountain"),
            "wall": ("wall", "wall"),
            "border": ("border", "border"),
            "nature": ("nature", "nature"),
            "decoration": ("decoration", "decoration"),
            "raw": ("raw", "item"),
            "quest": ("quest", "quest"),
            "house": ("house", "house"),
        }
        return mapping.get(family, ("terrain", "ground"))

    def _paint_at(self, coord: TileCoord) -> None:
        radius = int(self.brush_radius.currentText())
        if self._active_is_ground_brush():
            brush = self._safe_ground_brush_definition()
            if brush is None:
                return
            committed = self.ground_brush_engine.commit(
                self.workspace_services,
                brush,
                coord.key(),
                size=radius,
                shape=self._selected_brush_shape(),
            )
            if committed:
                dirty_chunks = (
                    len(self.workspace_services.last_result.affected_chunks)
                    if self.workspace_services.last_result is not None
                    else 0
                )
                self.statusBar().showMessage(
                    "Ground Brush | "
                    f"material:{brush.material.name} | "
                    f"size:{radius} | "
                    f"shape:{self._selected_brush_shape().value} | "
                    "valid | autoborder pending | "
                    f"dirty chunks:{dirty_chunks}"
                )
                self._log(
                    f"Painted tile {coord.x},{coord.y},{coord.z} | Ground-painted {brush.name}"
                )
            else:
                self.statusBar().showMessage(
                    "Ground Brush | "
                    f"material:{brush.material.name} | "
                    f"size:{radius} | "
                    f"shape:{self._selected_brush_shape().value} | invalid"
                )
                self._log(
                    f"Ground brush rejected at {coord.x},{coord.y},{coord.z}"
                )
        elif self.selected_asset is not None and self._selected_official_brush_type():
            brush_name = str(getattr(self.selected_asset, "brush", "")).strip()
            footprint = self.ground_brush_engine.footprint(
                coord.key(),
                size=radius,
                shape=self._selected_brush_shape(),
            )
            brush_type = self._selected_official_brush_type()
            try:
                result = self.mapping_engine.apply_official_brush(
                    brush_name,
                    footprint,
                    align="auto",
                    doors=(footprint if "door" in self.selected_asset.name.lower() else ()),
                    semantic_role=(
                        "roof"
                        if "roof" in brush_name.lower()
                        else brush_type.replace(" ", "_")
                    ),
                )
            except (KeyError, TypeError, ValueError) as exc:
                self._log(
                    f"Official brush rejected: {type(exc).__name__}: {exc}"
                )
                self.statusBar().showMessage("Official brush rejected; map unchanged")
                return
            family = result.postprocess.get("family", {})
            self._log(
                f"Applied official {brush_type} brush {brush_name} at "
                f"{coord.x},{coord.y},{coord.z} | {family}"
            )
        elif self.selected_asset is not None:
            if radius <= 1:
                self.mapping_engine.place_item(coord, self.selected_asset.asset_id)
            else:
                self.mapping_engine.place_items(
                    (
                        TileCoord(x, y, coord.z)
                        for x in range(coord.x - radius + 1, coord.x + radius)
                        for y in range(coord.y - radius + 1, coord.y + radius)
                    ),
                    self.selected_asset.asset_id,
                )
            self._log(
                f"Painted {self.selected_asset.name} ({self.selected_asset.asset_id}) at {coord.x},{coord.y},{coord.z}"
            )
        elif radius <= 1:
            brush, role = self._brush_role()
            self.mapping_engine.paint([coord], brush=brush, role=role)
            self._log(f"Painted tile {coord.x},{coord.y},{coord.z}")
        else:
            brush, role = self._brush_role()
            self.mapping_engine.paint_radius(coord, radius - 1, brush=brush, role=role)
            self._log(f"Painted tile {coord.x},{coord.y},{coord.z}")
        self._refresh_viewport()

    def _selected_brush_shape(self) -> BrushShape:
        if self.brush_shape.currentText().lower() == "circle":
            return BrushShape.CIRCLE
        return BrushShape.SQUARE

    def _active_is_ground_brush(self) -> bool:
        if self.selected_asset is not None:
            official_type = self._selected_official_brush_type()
            if official_type:
                return official_type == "ground"
            return str(getattr(self.selected_asset, "category", "")).lower() in {
                "grounds",
                "terrain",
            }
        return self.active_brush_family.lower() == "terrain"

    def _selected_official_brush_type(self) -> str:
        if self.selected_asset is None or self.asset_registry is None:
            return ""
        brush_name = str(getattr(self.selected_asset, "brush", "")).strip().lower()
        brush = getattr(self.asset_registry, "brush_materials", {}).get(brush_name)
        if brush is None:
            return ""
        source = str(getattr(brush, "source_file", "")).replace("\\", "/").lower()
        if "/materials/brushs/" not in source:
            return ""
        return str(getattr(brush, "brush_type", "")).lower()

    def _ground_brush_definition(self) -> BrushDefinition:
        if self.selected_asset is not None:
            asset_id = int(self.selected_asset.asset_id)
            name = str(self.selected_asset.name)
            tileset = str(getattr(self.selected_asset, "tileset", ""))
            source = str(getattr(self.selected_asset, "source_file", "BrushDatabase"))
        else:
            default_asset = None
            if self.asset_registry is not None:
                brush_materials = getattr(self.asset_registry, "brush_materials", {})
                default_brush = brush_materials.get("grass")
                default_item_id = getattr(default_brush, "item_id", None)
                asset_lookup = getattr(self.asset_registry, "asset", None)
                if default_item_id is not None and callable(asset_lookup):
                    candidate = asset_lookup(int(default_item_id))
                    if getattr(candidate, "render_status", None) == "SPRITE_BACKED":
                        default_asset = candidate
            if default_asset is None:
                raise RuntimeError(
                    "Terrain brush unavailable: no official SPRITE_BACKED ground loaded"
                )
            asset_id = int(default_asset.asset_id)
            name = str(default_asset.name)
            tileset = str(getattr(default_asset, "tileset", "Grounds"))
            source = str(getattr(default_asset, "source_file", "BrushDatabase"))
        material = MaterialDefinition(
            material_id=f"ground:{asset_id}",
            name=name,
            ground_item_id=asset_id,
            tileset=tileset,
            source=source,
        )
        return BrushDefinition(
            brush_id=f"ground:{asset_id}",
            name=name,
            brush_type=BrushType.GROUND,
            material=material,
            source=source,
            metadata={
                "workspace_core_material": "materials"
                in source.replace("\\", "/").lower()
                and "/brushs/" in source.replace("\\", "/").lower()
            },
        )

    def _safe_ground_brush_definition(self) -> BrushDefinition | None:
        try:
            return self._ground_brush_definition()
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._log(f"Ground brush unavailable. {type(exc).__name__}: {exc}")
            self.statusBar().showMessage("Ground Brush unavailable: official assets not loaded")
            return None

    def undo(self) -> None:
        transaction = self.mapping_engine.undo()
        if transaction:
            self._log(f"Undo {transaction.name}")
        self._refresh_viewport()

    def redo(self) -> None:
        transaction = self.mapping_engine.redo()
        if transaction:
            self._log(f"Redo {transaction.name}")
        self._refresh_viewport()

    def copy_selection(self) -> None:
        copied = self.mapping_engine.copy_selection()
        self._log(f"Copied {copied} tiles")

    def paste_clipboard(self) -> None:
        self.mapping_engine.paste(self.mapping_engine.cursor)
        self._log("Pasted clipboard")
        self._refresh_viewport()

    def rotate_clipboard(self) -> None:
        count = self.mapping_engine.rotate_clipboard_clockwise()
        self._log(f"Rotated {count} clipboard tiles")

    def mirror_clipboard(self) -> None:
        count = self.mapping_engine.mirror_clipboard_horizontal()
        self._log(f"Mirrored {count} clipboard tiles")

    def expand_selection(self) -> None:
        self.mapping_engine.expand_selection()
        self._refresh_viewport()

    def add_bookmark(self) -> None:
        name = f"Bookmark {len(self.mapping_engine.bookmarks) + 1}"
        self.mapping_engine.add_bookmark(name, self.mapping_engine.cursor)
        self._log(f"Added Bookmark {name}")

    def repair_visual_zones(self) -> None:
        report = self.mapping_engine.repair_visual_zones_with_rme_core(
            root=str(self.workspace_root or ".")
        )
        ui_bridge = report.get("ui_bridge", {}) if isinstance(report, dict) else {}
        self._log(
            "RME visual repair: "
            f"status={report.get('status')} "
            f"find_replace={report.get('find_replace_repairs')} "
            f"copybuffer={report.get('copybuffer_repairs')} "
            f"bitmap={report.get('bitmap_to_map_repairs')} "
            f"tiles={ui_bridge.get('after_tiles')}"
        )
        self._refresh_viewport()

    def refresh_export_status(self) -> None:
        from .map02_necro_export import NecroMap02Exporter

        project_root = None
        if hasattr(self, "project_context") and isinstance(self.project_context, dict):
            project_root = self.project_context.get("project_root")
        exporter = NecroMap02Exporter(
            self.workspace_root or ".", project_root=project_root
        )
        model = exporter.build_export_model()
        precheck = exporter.precheck(model)
        status = "Export Ready" if precheck.ready else "Export Blocked"
        export_path = exporter.export_root / "necro.otbm"
        self.export_status = {
            "status": status,
            "tile_count": model.tile_count,
            "item_count": model.item_count,
            "warning_count": len(precheck.warnings),
            "error_count": len(precheck.errors),
            "export_path": str(export_path),
        }
        self._log(
            f"{status}: tiles={model.tile_count} items={model.item_count} "
            f"errors={len(precheck.errors)} warnings={len(precheck.warnings)} path={export_path}"
        )

    def jump_to_coordinate(self) -> None:
        parts = [part.strip() for part in self.coordinate_jump.text().split(",")]
        if len(parts) not in {2, 3}:
            self._log("Invalid coordinate")
            return
        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2]) if len(parts) == 3 else 7
        self.mapping_engine.jump_to(x, y, z)
        self.viewport.set_floor(z)
        tile_size = max(1, int(24 * self.viewport.zoom))
        self.viewport.pan = QPoint(
            max(self.viewport.width(), 800) // 2 - x * tile_size,
            max(self.viewport.height(), 480) // 2 - y * tile_size,
        )
        self._log(f"Jumped to coordinate {x},{y},{z}")
        self._refresh_viewport()

    def _handle_minimap_navigation(self, x: int, y: int) -> None:
        self.mapping_engine.jump_to(x, y, self.viewport.floor)
        self.coordinate_jump.setText(f"{x},{y},{self.viewport.floor}")
        self._log(f"Minimap navigation requested {x},{y},{self.viewport.floor}")
        self._refresh_viewport()

    def _refresh_viewport(self) -> None:
        dirty = set(self.mapping_engine.consume_dirty_positions())
        if hasattr(self.viewport, "set_dirty_tiles"):
            self.viewport.set_dirty_tiles(dirty)
        if dirty and hasattr(self.viewport, "update_tiles"):
            self.viewport.update_tiles(
                self.mapping_engine.tiles_for_positions(dirty),
                {position for position in dirty if position not in self.mapping_engine.tiles},
            )
        elif not getattr(self.viewport, "tiles", []):
            tiles = self.mapping_engine.tiles_for_viewport()
            self.viewport.set_tiles(tiles)
        self.viewport.set_selected_tiles(set(self.mapping_engine.selection))
        if hasattr(self, "minimap"):
            self.minimap.set_tiles(self.mapping_engine.tiles_for_viewport())
        if hasattr(self, "zoom_label"):
            self.zoom_label.setText(f"zoom: {int(self.viewport.zoom * 100)}%")
            self.statusBar().showMessage(self._status_text())

    def _status_text(self) -> str:
        self.editor_status.project = self.status_project_label.text().replace(
            "Project: ", ""
        )
        self.editor_status.town = self.status_town_label.text().replace("Town: ", "")
        self.editor_status.x = int(self.status_x_label.text().replace("x: ", ""))
        self.editor_status.y = int(self.status_y_label.text().replace("y: ", ""))
        self.editor_status.z = int(self.status_z_label.text().replace("z: ", ""))
        self.editor_status.zoom = int(
            self.zoom_label.text().replace("zoom: ", "").replace("%", "")
        )
        self.editor_status.item = (
            self.selected_item_label.text()
            .replace("item: ", "")
            .replace("selected item: ", "")
        )
        self.editor_status.brush = self.current_brush_label.text().replace(
            "brush: ", ""
        )
        self.editor_status.fps = float(getattr(self.viewport, "viewport_fps", 0.0))
        self.editor_status.visible_tiles = int(
            getattr(self.viewport, "visible_tile_count", 0)
        )
        self.editor_status.visible_chunks = int(
            getattr(self.viewport, "visible_chunk_count", 0)
        )
        if self.selected_asset is not None:
            self.editor_status.client_id = str(
                self.selected_asset.client_id or self.selected_asset.asset_id
            )
            self.editor_status.sprite_id = str(
                self.selected_asset.client_id or self.selected_asset.asset_id
            )
        else:
            self.editor_status.client_id = "none"
            self.editor_status.sprite_id = "none"
        return self.editor_status.text()

    def _set_status_coordinates(self, x: int, y: int, z: int) -> None:
        self.status_x_label.setText(f"x: {x}")
        self.status_y_label.setText(f"y: {y}")
        self.status_z_label.setText(f"z: {z}")
        self.statusBar().showMessage(self._status_text())

    def _load_recent_necro_project_if_available(self) -> None:
        from .app_paths import get_user_projects_root

        projects_root = get_user_projects_root(self.workspace_root)
        recent_path = projects_root / "recent_projects.json"
        if not recent_path.exists():
            return
        try:
            payload = json.loads(recent_path.read_text(encoding="utf-8"))
            projects = payload.get("projects", [])
            if not projects:
                return
            project = projects[0]
            self.load_necro_project_context(
                {
                    "project_root": project.get("path"),
                    "config": {
                        "project_name": project.get("project_name", "Necro"),
                        "town_name": project.get("town_name", "Necro"),
                        "temple": project.get("temple", {"x": 1000, "y": 1000, "z": 7}),
                        "map_width": 4096,
                        "map_height": 4096,
                    },
                }
            )
        except Exception as exc:
            self._log(f"Recent NECRO project unavailable. {type(exc).__name__}: {exc}")

    def load_necro_project_context(self, project_info: Dict[str, object]) -> None:
        config = project_info.get("config", {})
        if not isinstance(config, dict):
            config = {}
        temple = config.get("temple") or {
            "x": config.get("temple_x", 1000),
            "y": config.get("temple_y", 1000),
            "z": config.get("temple_z", 7),
        }
        if not isinstance(temple, dict):
            temple = {"x": 1000, "y": 1000, "z": 7}
        x = int(temple.get("x", 1000))
        y = int(temple.get("y", 1000))
        z = int(temple.get("z", 7))
        project_name = str(config.get("project_name", "Necro"))
        town_name = str(config.get("town_name", "Necro"))
        self.project_name = project_name
        self.town_name = town_name

        self.project_context = project_info
        self.status_project_label.setText(f"Project: {project_name.upper()}")
        self.status_town_label.setText(f"Town: {town_name}")
        self.mapping_engine.jump_to(x, y, z)
        self.viewport.floor = z
        width = max(self.viewport.width(), 800)
        height = max(self.viewport.height(), 480)
        tile_size = max(1, int(24 * self.viewport.zoom))
        self.viewport.pan = QPoint(
            width // 2 - x * tile_size, height // 2 - y * tile_size
        )
        self.selection_type.setText("Temple")
        self.selection_coordinates.setText(f"{x}, {y}, {z}")
        self.coordinate_jump.setText(f"{x},{y},{z}")
        self.start_panel.hide()
        self._set_status_coordinates(x, y, z)
        self.coordinate_label.setText(
            f"Project: {project_name} | Town: {town_name} | Temple: {x},{y},{z} | Floor {z}"
        )
        project_root = project_info.get("project_root")
        if project_root:
            self.project_path_label.setText(str(project_root))
        self._log("New world initialized. Ready for editing.")
        if project_root:
            self._log(f"Project path: {project_root}")
        self._refresh_viewport()

    def _log(self, message: str) -> None:
        self.console_output.append(message)

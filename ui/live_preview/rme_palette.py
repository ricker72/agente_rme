"""Qt widgets for an RME-like OpenTibia palette."""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.rendering.appearance_loader import AppearanceLoader
from core.rendering.sprite_cache import SpriteCache
from core.rendering.sprite_materializer import SpriteMaterializer
from core.rendering.sprite_resolver import SpriteResolver
from .rme_palette_model import (
    ITEM_MATERIALS,
    PALETTE_GROUPS,
    TERRAIN_MATERIALS,
    PaletteCard,
)

LEGACY_CATEGORY_TABS = (
    "Terrain",
    "Borders",
    "Raw",
    "Raw Items",
    "Construction",
    "House",
    "Quest",
    "Magic",
    "Cave",
    "Doodads",
)

_RENDER_SERVICES: tuple[AppearanceLoader, SpriteResolver, SpriteCache] | None = None


def _render_services() -> tuple[AppearanceLoader, SpriteResolver, SpriteCache]:
    """Load immutable appearance metadata once per UI process."""
    global _RENDER_SERVICES
    if _RENDER_SERVICES is None:
        loader = AppearanceLoader().load()
        pixel_sources = (
            loader.report.companion_pixel_sources if loader.report is not None else ()
        )
        _RENDER_SERVICES = (
            loader,
            SpriteResolver(loader),
            SpriteCache(SpriteMaterializer(pixel_sources)),
        )
    return _RENDER_SERVICES


def _asset_cards(
    asset_registry: object | None, category: str, *, limit: int | None = 240
) -> list[PaletteCard]:
    if asset_registry is None:
        return []
    assets_by_category = getattr(asset_registry, "sprite_backed_assets_by_category", None)
    if not callable(assets_by_category):
        assets_by_category = getattr(asset_registry, "assets_by_category", None)
    search = getattr(asset_registry, "search", None)
    assets = []
    if callable(assets_by_category):
        lookup = {
            "Terrain Palette": "Grounds",
            "Grounds": "Grounds",
            "Terrain": "Grounds",
            "Nature": "Nature",
            "Mountains": "Mountains",
            "Walls": "Walls",
            "Water": "Water",
            "Borders": "Borders",
            "Tiny Borders": "Borders",
            "Large Borders": "Borders",
            "House": "Houses",
            "House Palette": "Houses",
            "RAW Palette": "Raw Items",
            "Raw": "Raw Items",
            "Raw Items": "Raw Items",
            "Item Palette": "Raw Items",
            "Quest": "Raw Items",
            "Magic": "Raw Items",
            "Doodad Palette": "Decoration",
            "Doodads": "Decoration",
        }.get(category, category)
        assets.extend(assets_by_category(lookup))
    if not assets and callable(search):
        for token in category.replace("-", " ").replace("/", " ").split():
            assets.extend(
                asset
                for asset in search(token)
                if getattr(asset, "render_status", None) == "SPRITE_BACKED"
            )
    unique = {}
    for asset in assets:
        if getattr(asset, "render_status", None) != "SPRITE_BACKED":
            continue
        unique[getattr(asset, "asset_id", id(asset))] = asset
    source_assets = list(unique.values())
    if limit is not None:
        source_assets = source_assets[:limit]
    cards = [
        PaletteCard(
            item_id=int(getattr(asset, "asset_id")),
            client_id=getattr(asset, "client_id", None),
            category=str(getattr(asset, "category", category)),
            tileset=str(getattr(asset, "tileset", "Materials")),
            source=str(getattr(asset, "source_file", "official OpenTibia assets")),
            name=str(getattr(asset, "name", f"item {getattr(asset, 'asset_id')}")),
            sprite_status=str(getattr(asset, "render_status", "SPRITE_BACKED")),
        )
        for asset in source_assets
        if getattr(asset, "asset_id", None) is not None
    ]
    return cards


class RMEPaletteWidget(QTabWidget):
    """Palette with RME workflow hierarchy and appearance-backed sprite grids."""

    def __init__(
        self,
        asset_registry: object | None,
        *,
        on_asset_selected: Callable[[QListWidgetItem], None] | None = None,
        on_tool_selected: Callable[[str], None] | None = None,
        on_brush_size_changed: Callable[[int], None] | None = None,
        on_brush_shape_changed: Callable[[str], None] | None = None,
        on_doodad_thickness_changed: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("PMX01ARMEPalette")
        self.asset_registry = asset_registry
        self.on_asset_selected = on_asset_selected
        self.on_tool_selected = on_tool_selected
        self.on_brush_size_changed = on_brush_size_changed
        self.on_brush_shape_changed = on_brush_shape_changed
        self.on_doodad_thickness_changed = on_doodad_thickness_changed
        self.asset_lists: dict[str, QListWidget] = {}
        self.asset_search_results = QListWidget()
        self.asset_search_results.setObjectName("UX03AssetSearchResults")
        self.palette_selector = QComboBox()
        self.palette_selector.setObjectName("RMEPaletteTypeChoice")
        self.tileset_selector = QComboBox()
        self.tileset_selector.setObjectName("RMETilesetChoice")
        self.visible_asset_grid = QListWidget()
        self.visible_asset_grid.setObjectName("RMEVisibleTilesetSprites")
        self.previous_page_button = QPushButton("<-")
        self.next_page_button = QPushButton("->")
        self.page_label = QLabel("1 /1")
        self._page_index = 0
        self._page_size = 60
        self._active_cards: list[PaletteCard] = []
        (
            self.appearance_loader,
            self.sprite_resolver,
            self.sprite_cache,
        ) = _render_services()
        self._thumbnail_cache: OrderedDict[tuple[int, str], tuple[QPixmap, str]] = (
            OrderedDict()
        )
        self._thumbnail_cache_limit = 512
        self._build()

    def _build(self) -> None:
        self.tabBar().hide()

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.palette_selector.addItems(PALETTE_GROUPS)
        self.palette_selector.currentTextChanged.connect(self._palette_changed)
        layout.addWidget(self.palette_selector)
        layout.addWidget(QLabel("Tileset"))
        self.tileset_selector.currentTextChanged.connect(self._tileset_changed)
        layout.addWidget(self.tileset_selector)

        self._configure_icon_grid(self.visible_asset_grid, QSize(44, 44), QSize(40, 40))
        if self.on_asset_selected is not None:
            self.visible_asset_grid.itemClicked.connect(self.on_asset_selected)
        layout.addWidget(self.visible_asset_grid, 1)

        page_row = QHBoxLayout()
        for button in (self.previous_page_button, self.next_page_button):
            button.setFixedSize(55, 25)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previous_page_button.clicked.connect(self._previous_page)
        self.next_page_button.clicked.connect(self._next_page)
        page_row.addWidget(self.previous_page_button)
        page_row.addStretch(1)
        page_row.addWidget(self.page_label)
        page_row.addStretch(1)
        page_row.addWidget(self.next_page_button)
        layout.addLayout(page_row)

        self.tools_panel = self._build_tools_panel()
        self.doodad_thickness_panel = self._build_doodad_thickness_panel()
        self.brush_size_panel = self._build_brush_size_panel()
        layout.addWidget(self.tools_panel)
        layout.addWidget(self.doodad_thickness_panel)
        layout.addWidget(self.brush_size_panel)

        search_panel = QWidget()
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.asset_search = QLineEdit()
        self.asset_search.setObjectName("UX03AssetSearch")
        self.asset_search.setPlaceholderText("Search official OpenTibia assets")
        self.asset_search.textChanged.connect(self.filter_assets)
        if self.on_asset_selected is not None:
            self.asset_search_results.itemClicked.connect(self.on_asset_selected)
        search_layout.addWidget(self.asset_search)
        search_layout.addWidget(self.asset_search_results)
        layout.addWidget(search_panel)

        self.compat_categories = self._build_terrain_palette()
        self.compat_categories.hide()
        layout.addWidget(self.compat_categories)
        self.compat_item_categories = self._build_item_palette()
        self.compat_item_categories.hide()
        layout.addWidget(self.compat_item_categories)

        self.addTab(panel, PALETTE_GROUPS[0])
        for palette_name in PALETTE_GROUPS[1:]:
            self.addTab(QWidget(), palette_name)

        fallback = QGroupBox("Sprite rendering status")
        fallback.setObjectName("PMX01ASpriteFallbackCard")
        fallback.hide()
        layout.addWidget(fallback)
        self._palette_changed(self.palette_selector.currentText())

    def _palette_categories(self, palette_name: str) -> tuple[str, ...]:
        if palette_name == "Terrain Palette":
            return (*TERRAIN_MATERIALS, *LEGACY_CATEGORY_TABS)
        if palette_name == "Doodad Palette":
            return ("Decoration", "Doodads", "Nature")
        if palette_name == "Item Palette":
            return (*ITEM_MATERIALS, "Raw Items")
        if palette_name == "House Palette":
            return ("House", "Houses", "Construction")
        if palette_name == "RAW Palette":
            return ("Raw", "Raw Items")
        return (palette_name,)

    def _palette_changed(self, palette_name: str) -> None:
        cards: dict[int, PaletteCard] = {}
        for category in self._palette_categories(palette_name):
            for card in _asset_cards(self.asset_registry, category, limit=None):
                if card.sprite_status == "SPRITE_BACKED":
                    cards.setdefault(card.item_id, card)
        self._active_cards = list(cards.values())

        tilesets = sorted({card.tileset for card in self._active_cards if card.tileset})
        self.tileset_selector.blockSignals(True)
        self.tileset_selector.clear()
        self.tileset_selector.addItems(tilesets or ["Materials"])
        preferred = self.tileset_selector.findText("Grounds - Ornamented")
        if preferred >= 0:
            self.tileset_selector.setCurrentIndex(preferred)
        self.tileset_selector.blockSignals(False)
        self._page_index = 0
        self._refresh_visible_grid()
        self.tools_panel.setVisible(palette_name == "Terrain Palette")
        self.doodad_thickness_panel.setVisible(palette_name == "Doodad Palette")
        self.brush_size_panel.setVisible(
            palette_name in {
                "Terrain Palette", "Doodad Palette", "Item Palette",
                "House Palette", "RAW Palette",
            }
        )

    def _tileset_changed(self, _tileset_name: str) -> None:
        self._page_index = 0
        self._refresh_visible_grid()

    def _cards_for_current_tileset(self) -> list[PaletteCard]:
        tileset_name = self.tileset_selector.currentText()
        return [card for card in self._active_cards if card.tileset == tileset_name]

    def _refresh_visible_grid(self) -> None:
        self.visible_asset_grid.clear()
        cards = self._cards_for_current_tileset()
        total_pages = max(1, (len(cards) + self._page_size - 1) // self._page_size)
        self._page_index = max(0, min(self._page_index, total_pages - 1))
        start = self._page_index * self._page_size
        for card in cards[start : start + self._page_size]:
            self._add_card_item(self.visible_asset_grid, card)
        self.page_label.setText(f"{self._page_index + 1} /{total_pages}")
        self.previous_page_button.setEnabled(self._page_index > 0)
        self.next_page_button.setEnabled(self._page_index < total_pages - 1)

    def _previous_page(self) -> None:
        if self._page_index > 0:
            self._page_index -= 1
            self._refresh_visible_grid()

    def _next_page(self) -> None:
        total = len(self._cards_for_current_tileset())
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._page_index < total_pages - 1:
            self._page_index += 1
            self._refresh_visible_grid()

    def _build_tools_panel(self) -> QWidget:
        panel = QGroupBox("Tools")
        grid = QGridLayout(panel)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(2)
        tools = (
            ("Optional Border", "optional-border"), ("Erase", "erase"),
            ("PZ", "pz"), ("No-PvP", "no-pvp"),
            ("Logout", "logout"), ("PvP", "pvp"),
            ("Normal Door", "door-normal"), ("Locked Door", "door-locked"),
            ("Magic Door", "door-magic"), ("Quest Door", "door-quest"),
            ("Hatch Window", "door-hatch"), ("Window", "window-normal"),
        )
        self.tool_buttons: dict[str, QPushButton] = {}
        for index, (label, tool_id) in enumerate(tools):
            button = QPushButton(label)
            button.setFixedSize(45, 45)
            button.setCheckable(True)
            button.setToolTip(label)
            button.clicked.connect(lambda _checked=False, value=tool_id: self._select_tool(value))
            grid.addWidget(button, index // 6, index % 6)
            self.tool_buttons[tool_id] = button
        return panel

    def _select_tool(self, tool_id: str) -> None:
        for current_id, button in self.tool_buttons.items():
            button.setChecked(current_id == tool_id)
        if self.on_tool_selected is not None:
            self.on_tool_selected(tool_id)

    def _build_doodad_thickness_panel(self) -> QWidget:
        panel = QGroupBox("Brush Thickness")
        layout = QVBoxLayout(panel)
        self.doodad_thickness = QSlider(Qt.Orientation.Horizontal)
        self.doodad_thickness.setRange(1, 10)
        self.doodad_thickness.setValue(5)
        self.doodad_thickness.valueChanged.connect(self._doodad_thickness_changed)
        layout.addWidget(self.doodad_thickness)
        return panel

    def _doodad_thickness_changed(self, value: int) -> None:
        if self.on_doodad_thickness_changed is not None:
            self.on_doodad_thickness_changed(value)

    def _build_brush_size_panel(self) -> QWidget:
        panel = QGroupBox("Brush Size")
        layout = QGridLayout(panel)
        self.brush_shape_buttons: dict[str, QPushButton] = {}
        for column, shape in enumerate(("Square", "Circle")):
            button = QPushButton(shape)
            button.setCheckable(True)
            button.setChecked(shape == "Square")
            button.clicked.connect(lambda _checked=False, value=shape: self._select_shape(value))
            layout.addWidget(button, 0, column)
            self.brush_shape_buttons[shape] = button
        self.brush_size_buttons: dict[int, QPushButton] = {}
        for column, size in enumerate((1, 2, 3, 5, 7, 9, 12)):
            button = QPushButton(str(size))
            button.setFixedSize(32, 30)
            button.setCheckable(True)
            button.setChecked(size == 1)
            button.clicked.connect(lambda _checked=False, value=size: self._select_size(value))
            layout.addWidget(button, 1, column)
            self.brush_size_buttons[size] = button
        return panel

    def _select_shape(self, shape: str) -> None:
        for value, button in self.brush_shape_buttons.items():
            button.setChecked(value == shape)
        if self.on_brush_shape_changed is not None:
            self.on_brush_shape_changed(shape)

    def _select_size(self, size: int) -> None:
        for value, button in self.brush_size_buttons.items():
            button.setChecked(value == size)
        if self.on_brush_size_changed is not None:
            self.on_brush_size_changed(size)

    def _build_terrain_palette(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("UX03AssetCategories")
        for material in (*TERRAIN_MATERIALS, *LEGACY_CATEGORY_TABS):
            tabs.addTab(
                self._visual_grid(
                    material, _asset_cards(self.asset_registry, material)
                ),
                material,
            )
        return tabs

    def _build_item_palette(self) -> QTabWidget:
        tabs = QTabWidget()
        for material in ITEM_MATERIALS:
            tabs.addTab(
                self._visual_grid(
                    material, _asset_cards(self.asset_registry, material)
                ),
                material,
            )
        tabs.addTab(
            self._visual_grid(
                "Raw Items", _asset_cards(self.asset_registry, "Raw Items")
            ),
            "Raw Items",
        )
        return tabs

    def _visual_grid(self, category: str, cards: Iterable[PaletteCard]) -> QListWidget:
        grid = QListWidget()
        grid.setObjectName(
            f"UX03AssetList_{category.replace(' ', '_').replace('/', '_')}"
        )
        self._configure_icon_grid(grid, QSize(44, 44), QSize(40, 40))
        if self.on_asset_selected is not None:
            grid.itemClicked.connect(self.on_asset_selected)
        self.asset_lists[category] = grid
        card_list = list(cards)
        for index, card in enumerate(card_list):
            if card.sprite_status != "SPRITE_BACKED":
                continue
            # Render one proof sprite per hidden compatibility category. Keep
            # the remaining searchable metadata without decoding thousands of
            # images during application startup.
            self._add_card_item(grid, card, render_thumbnail=index == 0)
        return grid

    def _configure_icon_grid(
        self, grid: QListWidget, grid_size: QSize, icon_size: QSize
    ) -> None:
        grid.setViewMode(QListView.ViewMode.IconMode)
        grid.setResizeMode(QListView.ResizeMode.Adjust)
        grid.setMovement(QListView.Movement.Static)
        grid.setUniformItemSizes(True)
        grid.setWrapping(True)
        grid.setSpacing(2)
        grid.setIconSize(icon_size)
        grid.setGridSize(grid_size)
        grid.setWordWrap(False)
        grid.setBatchSize(120)

    def _add_card_item(
        self,
        grid: QListWidget,
        card: PaletteCard,
        *,
        render_thumbnail: bool = True,
    ) -> None:
        item = QListWidgetItem("")
        item.setData(Qt.ItemDataRole.UserRole, card.item_id)
        status = "SPRITE_BACKED:DEFERRED"
        if render_thumbnail:
            try:
                pixmap, status = self._thumbnail(card)
            except (OSError, ValueError, RuntimeError) as exc:
                # One malformed sprite must not make the complete editor fail.
                item.setData(
                    Qt.ItemDataRole.AccessibleDescriptionRole,
                    f"SPRITE_DECODE_ERROR:{type(exc).__name__}",
                )
                return
            item.setIcon(QIcon(pixmap))
        item.setData(
            Qt.ItemDataRole.ToolTipRole,
            f"{card.name} | ID {card.item_id} | ClientID {card.client_id or card.item_id} | "
            f"Sprite {status} | Brush {card.category} | Category {card.category} | "
            f"Tileset {card.tileset} | Source {card.source}",
        )
        item.setData(Qt.ItemDataRole.StatusTipRole, status)
        item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, status)
        grid.addItem(item)

    def _thumbnail(self, card: PaletteCard):
        cache_key = (card.client_id or card.item_id, card.category)
        if cache_key in self._thumbnail_cache:
            cached = self._thumbnail_cache.pop(cache_key)
            self._thumbnail_cache[cache_key] = cached
            return cached
        resolved = self.sprite_resolver.resolve(
            item_id=card.item_id,
            client_id=card.client_id,
            name=card.name,
            category=card.category,
            source=card.source,
        )
        pixmap, material = self.sprite_cache.thumbnail(resolved, size=42)
        status = (
            f"{resolved.status}:{material.status}:"
            f"{resolved.primary_sprite_id if resolved.primary_sprite_id is not None else 'UNRESOLVED'}"
        )
        self._thumbnail_cache[cache_key] = (pixmap, status)
        while len(self._thumbnail_cache) > self._thumbnail_cache_limit:
            self._thumbnail_cache.popitem(last=False)
        return pixmap, status

    def filter_assets(self, text: str) -> None:
        self.asset_search_results.clear()
        if not text or self.asset_registry is None:
            return
        search = getattr(self.asset_registry, "search", None)
        if not callable(search):
            return
        for asset in search(text)[:200]:
            if getattr(asset, "render_status", None) != "SPRITE_BACKED":
                continue
            item = QListWidgetItem(
                f"{getattr(asset, 'name', 'item')} | ID {getattr(asset, 'asset_id', '--')} | "
                f"{getattr(asset, 'category', '--')} | {getattr(asset, 'source_file', '--')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, getattr(asset, "asset_id", None))
            self.asset_search_results.addItem(item)

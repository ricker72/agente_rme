"""
HITO 9 REAL — Preview Generator V1

Orquestador principal del sistema de preview.

Responsable de:
    WorldModel → PNG (preview.png, preview_minimap.png)
    WorldModel → JSON (preview.json)

API:
    generator = PreviewGenerator()
    generator.generate(world, output_png="preview.png")

Pipeline:
    WorldModel
    ↓
    WorldValidator
    ↓
    PreviewGenerator
    ↓
    preview.png  +  preview_minimap.png  +  preview.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .palette import (
    GROUND,
    WALL,
    SPAWN,
    BOSS,
    DECORATION,
    TEMPLE,
)
from .preview_renderer import (
    render_layer,
    compute_bounds,
    add_structure_overlay,
)
from .minimap_renderer import save_minimap
from .preview_report import generate_report

try:
    from PIL import Image, ImageDraw, ImageFont

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class PreviewGenerator:
    """
    Genera preview.png + preview_minimap.png + preview.json
    a partir de un WorldModel.

    Uso:
        from core.preview import PreviewGenerator

        generator = PreviewGenerator()
        generator.generate(
            world,
            output_png="output/preview.png"
        )
        # Genera:
        #   output/preview.png
        #   output/preview_minimap.png
        #   output/preview.json

    También se puede usar paso a paso:
        png = generator.generate_png(world, "output/preview.png")
        mini = generator.generate_minimap(world, "output/preview_minimap.png")
        report = generator.generate_report(world)
        with open("output/preview.json", "w") as f:
            json.dump(report, f, indent=2)
    """

    def __init__(self, tile_size: int = 10, minimap_scale: str = "8x"):
        """
        Args:
            tile_size: Tamaño de cada tile en píxeles para preview.png.
            minimap_scale: Escala del minimapa ('4x', '8x', '16x').
        """
        self.tile_size = tile_size
        self.minimap_scale = minimap_scale

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def generate(
        self,
        world_model: Any,
        output_png: str = "output/preview.png",
        output_minimap: Optional[str] = "output/preview_minimap.png",
        output_json: Optional[str] = "output/preview.json",
        z: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Genera todos los outputs de preview: PNG, minimap, JSON.

        Args:
            world_model: Instancia de WorldModel.
            output_png: Ruta para preview.png.
            output_minimap: Ruta para minimapa (None para saltar).
            output_json: Ruta para preview.json (None para saltar).
            z: Capa Z a renderizar. None = automático.

        Returns:
            Dict con rutas de archivos generados.
        """
        result = {}

        # PNG
        png_path = self.generate_png(world_model, output_png, z=z)
        if png_path:
            result["png"] = png_path

        # Minimap
        if output_minimap:
            mini_path = self.generate_minimap(world_model, output_minimap, z=z)
            if mini_path:
                result["minimap"] = mini_path

        # Report JSON
        if output_json:
            json_path = self.generate_report_file(world_model, output_json)
            if json_path:
                result["json"] = json_path

        # Mostrar resumen en consola
        if result:
            report = generate_report(world_model)
            print(f"  [PREVIEW] {report['summary']}")
            for key, path in result.items():
                size = Path(path).stat().st_size if Path(path).exists() else 0
                print(f"    -> {key}: {path} ({size} bytes)")

        return result

    # ------------------------------------------------------------------
    # PNG preview completo
    # ------------------------------------------------------------------

    def generate_png(
        self,
        world_model: Any,
        output_path: str = "output/preview.png",
        z: Optional[int] = None,
    ) -> Optional[str]:
        """
        Genera preview.png con tiles coloreados + overlays de estructuras.

        Args:
            world_model: Instancia de WorldModel.
            output_path: Ruta de salida.
            z: Capa Z. None = automático.

        Returns:
            Ruta del archivo, o None si falló.
        """
        if not HAS_PIL:
            return self._fallback_ascii(world_model, output_path)

        tiles = getattr(world_model, "tiles", {})
        structures = getattr(world_model, "structures", [])

        bounds = compute_bounds(tiles)
        if bounds is None:
            return None

        if z is None:
            z = bounds["min_z"]

        # Renderizar capa
        img = render_layer(tiles, z=z, tile_size=self.tile_size, padding=1)
        if img is None:
            return None

        # Overlay de estructuras
        img = add_structure_overlay(
            img,
            structures,
            bounds,
            z=z,
            tile_size=self.tile_size,
            padding=1,
        )

        # Leyenda
        img = self._add_legend(img, world_model, z)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path

    # ------------------------------------------------------------------
    # Minimap
    # ------------------------------------------------------------------

    def generate_minimap(
        self,
        world_model: Any,
        output_path: str = "output/preview_minimap.png",
        z: Optional[int] = None,
    ) -> Optional[str]:
        """
        Genera preview_minimap.png a escala reducida.

        Args:
            world_model: Instancia de WorldModel.
            output_path: Ruta de salida.
            z: Capa Z.

        Returns:
            Ruta del archivo, o None si falló.
        """
        tiles = getattr(world_model, "tiles", {})
        structures = getattr(world_model, "structures", [])

        if z is None:
            bounds = compute_bounds(tiles)
            if bounds is None:
                return None
            z = bounds["min_z"]

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        return save_minimap(
            tiles,
            structures,
            output_path=output_path,
            z=z,
            scale=self.minimap_scale,
        )

    # ------------------------------------------------------------------
    # Report JSON
    # ------------------------------------------------------------------

    def generate_report(self, world_model: Any) -> Dict[str, Any]:
        """
        Genera el reporte de estadísticas del mapa.

        Args:
            world_model: Instancia de WorldModel.

        Returns:
            Dict con estadísticas.
        """
        return generate_report(world_model)

    def generate_report_file(
        self,
        world_model: Any,
        output_path: str = "output/preview.json",
    ) -> Optional[str]:
        """
        Genera preview.json con estadísticas.

        Args:
            world_model: Instancia de WorldModel.
            output_path: Ruta de salida.

        Returns:
            Ruta del archivo, o None si falló.
        """
        report = generate_report(world_model)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_path

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _add_legend(
        self,
        img: "Image.Image",
        world_model: Any,
        z: int,
    ) -> "Image.Image":
        """Añade una leyenda de colores en la parte inferior de la imagen."""
        draw = ImageDraw.Draw(img)

        # Región para leyenda
        legend_h = 70
        new_img = Image.new(
            "RGB",
            (img.width, img.height + legend_h),
            (10, 10, 10),
        )
        new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)

        font = None
        try:
            font = ImageFont.load_default()
        except Exception:
            pass

        # Título
        regions = getattr(world_model, "regions", [])
        title = regions[0].theme if regions else "World"
        draw.text(
            (10, img.height + 4),
            f"Tema: {title} | Z={z}",
            fill=(200, 200, 200),
            font=font,
        )

        # Items de leyenda
        legend_items = [
            (GROUND, "Ground"),
            (WALL, "Wall"),
            (SPAWN, "Spawn"),
            (BOSS, "Boss"),
            (DECORATION, "Deco"),
            (TEMPLE, "Structure"),
        ]
        for i, (color, name) in enumerate(legend_items):
            lx = 10 + i * 110
            ly = img.height + 24
            draw.rectangle([lx, ly, lx + 12, ly + 12], fill=color)
            draw.text((lx + 16, ly), name, fill=(180, 180, 180), font=font)

        return new_img

    def _fallback_ascii(self, world_model: Any, output_path: str) -> Optional[str]:
        """Fallo a ASCII si PIL no está disponible.

        Genera un archivo .txt con el preview ASCII en lugar de PNG.
        """
        from .preview_renderer import compute_bounds

        tiles = getattr(world_model, "tiles", {})
        bounds = compute_bounds(tiles)
        if bounds is None:
            return None

        lines = [f"Preview: {bounds.get('tile_count', 0)} tiles"]
        lines.append(
            f"Bounds: ({bounds['min_x']},{bounds['min_y']})~({bounds['max_x']},{bounds['max_y']})"
        )
        lines.append(f"Z: {bounds['min_z']}–{bounds['max_z']}")

        ascii_path = output_path.replace(".png", ".txt")
        Path(ascii_path).parent.mkdir(parents=True, exist_ok=True)
        with open(ascii_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  [WARN] PIL no instalado. ASCII guardado en: {ascii_path}")
        return None

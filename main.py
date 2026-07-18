"""
main.py
Agente IA de Diseño de Mapas para Remere's Map Editor
GUI built with customtkinter — dark industrial aesthetic.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk

import config_manager as cm
from assets.items_loader import load_items
from assets.monsters_loader import load_monster_names
from assets.npcs_loader import load_npc_names
from core.maintenance import cleanup_expired_artifacts
from core.studio import AIMapStudio

# ── Theme ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT = "#E8A020"  # amber/gold
ACCENT_DIM = "#9C6B10"
BG_DARK = "#0D0D0F"
BG_MID = "#16181C"
BG_CARD = "#1C1F26"
BG_INPUT = "#12141A"
TEXT_MAIN = "#E8E6DF"
TEXT_DIM = "#6B7280"
TEXT_GREEN = "#4ADE80"
TEXT_RED = "#F87171"
FONT_TITLE = ("Consolas", 22, "bold")
FONT_LABEL = ("Consolas", 11)
FONT_SMALL = ("Consolas", 9)
FONT_CODE = ("Consolas", 10)
FONT_BTN = ("Consolas", 11, "bold")
ICON_PATH = Path(__file__).resolve().parent / "recursos" / "favicon.ico"


def _apply_window_icon(window: tk.Tk | tk.Toplevel) -> None:
    try:
        if ICON_PATH.is_file():
            window.iconbitmap(str(ICON_PATH))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  SETUP WIZARD WINDOW
# ═══════════════════════════════════════════════════════════════════════════


class SetupWizard(ctk.CTkToplevel):
    """First-run configuration wizard. Blocks main window until complete."""

    def __init__(self, parent, config: dict, on_complete):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.on_complete = on_complete

        self.title("RME Agent — Asistente de Configuración")
        self.geometry("780x680")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        _apply_window_icon(self)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚙  CONFIGURACIÓN INICIAL",
            font=FONT_TITLE,
            text_color=ACCENT,
        ).place(x=24, y=16)
        ctk.CTkLabel(
            header,
            text="Configura las rutas de datos antes de generar mapas.",
            font=FONT_SMALL,
            text_color=TEXT_DIM,
        ).place(x=26, y=50)

        # Scrollable body
        body = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self.field_vars = {}
        self.status_labels = {}

        fields = [
            (
                "tibia_client_path",
                "1. Ruta del Cliente Tibia / appearances.dat",
                "archivo o carpeta",
                False,
            ),
            (
                "items_xml_path",
                "2. Archivo items.xml (servidor Canary / TFS)",
                "archivo .xml",
                False,
            ),
            (
                "monsters_folder",
                "3. Carpeta de Monstruos  (data/monster/)",
                "carpeta",
                False,
            ),
            ("npcs_folder", "4. Carpeta de NPCs  (data/npc/)", "carpeta", False),
            (
                "mounts_folder",
                "5. Carpeta de Monturas  (data/mounts/) — OPCIONAL",
                "carpeta",
                True,
            ),
        ]

        for key, label_text, hint, optional in fields:
            self._add_field_row(body, key, label_text, hint, optional)

        # Status box
        self.status_box = ctk.CTkTextbox(
            body,
            height=110,
            fg_color=BG_INPUT,
            text_color=TEXT_DIM,
            font=FONT_SMALL,
            corner_radius=6,
            wrap="word",
        )
        self.status_box.pack(fill="x", padx=20, pady=(8, 12))
        self.status_box.insert("end", "Estado: esperando validación...\n")
        self.status_box.configure(state="disabled")

        # Footer buttons
        footer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="VALIDAR Y GUARDAR",
            font=FONT_BTN,
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color="#000000",
            width=200,
            height=38,
            command=self._validate_and_save,
        ).place(x=24, y=11)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            font=FONT_BTN,
            fg_color="transparent",
            hover_color=BG_MID,
            text_color=TEXT_DIM,
            border_color=TEXT_DIM,
            border_width=1,
            width=110,
            height=38,
            command=self._on_close,
        ).place(x=238, y=11)

    def _add_field_row(self, parent, key, label_text, hint, optional):
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=8)
        frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(
            frame, text=label_text, font=FONT_LABEL, text_color=TEXT_MAIN, anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 2))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 8))

        var = ctk.StringVar()
        self.field_vars[key] = var

        entry = ctk.CTkEntry(
            row,
            textvariable=var,
            fg_color=BG_INPUT,
            border_color="#2A2D35",
            text_color=TEXT_MAIN,
            font=FONT_SMALL,
            placeholder_text=hint,
            height=34,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Browse button
        def _browse(k=key, optional=optional):
            if "folder" in k or k == "tibia_client_path":
                # First try folder, then file for tibia path
                if k == "tibia_client_path":
                    path = filedialog.askopenfilename(
                        title="Selecciona appearances.dat o archivo de cliente",
                        filetypes=[
                            ("Archivos de datos", "*.dat *.otb *.spr"),
                            ("Todos", "*.*"),
                        ],
                    )
                    if not path:
                        path = filedialog.askdirectory(
                            title="O selecciona la carpeta del cliente Tibia"
                        )
                else:
                    path = filedialog.askdirectory(
                        title=f"Selecciona carpeta para: {k}"
                    )
            else:
                path = filedialog.askopenfilename(
                    title="Selecciona items.xml",
                    filetypes=[("XML", "*.xml"), ("Todos", "*.*")],
                )
            if path:
                self.field_vars[k].set(path)

        ctk.CTkButton(
            row,
            text="Examinar...",
            font=FONT_SMALL,
            fg_color=BG_MID,
            hover_color="#2A2D35",
            text_color=TEXT_DIM,
            width=90,
            height=34,
            command=_browse,
        ).pack(side="right")

        # Status label
        status = ctk.CTkLabel(
            frame, text="", font=FONT_SMALL, text_color=TEXT_DIM, anchor="w"
        )
        status.pack(fill="x", padx=14, pady=(0, 6))
        self.status_labels[key] = status

    def _populate_fields(self):
        for key in self.field_vars:
            self.field_vars[key].set(self.config.get(key, ""))

    def _validate_and_save(self):
        # Update config from fields
        for key, var in self.field_vars.items():
            self.config[key] = var.get().strip()

        results = cm.validate_all(self.config)
        all_ok = True
        log_lines = []

        key_order = list(self.field_vars.keys())
        for i, (label, ok, msg) in enumerate(results):
            key = key_order[i]
            sl = self.status_labels[key]
            if ok:
                sl.configure(text=f"✓ {msg}", text_color=TEXT_GREEN)
                log_lines.append(f"[OK]  {label}: {msg}")
            else:
                sl.configure(text=f"✗ {msg}", text_color=TEXT_RED)
                log_lines.append(f"[ERR] {label}: {msg}")
                all_ok = False

        self._set_status("\n".join(log_lines))

        if all_ok:
            self.config["configured"] = True
            cm.save_config(self.config)
            self._set_status(
                "\n".join(log_lines) + "\n\n✓ Configuración guardada exitosamente."
            )
            self.after(
                800, lambda: (self.grab_release(), self.destroy(), self.on_complete())
            )
        else:
            self._set_status(
                "\n".join(log_lines) + "\n\n✗ Corrige los errores antes de continuar."
            )

    def _set_status(self, text: str):
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.insert("end", text)
        self.status_box.configure(state="disabled")

    def _on_close(self):
        if not self.config.get("configured"):
            if messagebox.askyesno(
                "Salir",
                "La configuración no está completa.\n¿Deseas cerrar la aplicación?",
                parent=self,
            ):
                self.parent.destroy()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════════════


class RMEAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RME Map AI Agent  v1.0")
        self.geometry("1100x820")
        self.minsize(900, 700)
        self.configure(fg_color=BG_DARK)
        _apply_window_icon(self)

        self.config = cm.load_config()
        self._cache: Optional[dict] = None
        self._monster_names: list[str] = []
        self._npc_names: list[str] = []
        self._generating = False
        self._last_script = ""
        self._studio: Optional[AIMapStudio] = None

        self._build_ui()

        # Check if we need setup wizard
        if not cm.is_configured(self.config):
            self.after(200, self._open_setup_wizard)
        else:
            self.after(300, self._load_data_async)

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=58)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkLabel(
            topbar,
            text="▣  RME MAP AI AGENT",
            font=("Consolas", 17, "bold"),
            text_color=ACCENT,
        ).place(x=20, y=14)

        ctk.CTkLabel(
            topbar,
            text="Generador de Scripts Lua para Remere's Map Editor",
            font=FONT_SMALL,
            text_color=TEXT_DIM,
        ).place(x=22, y=36)

        # Settings button
        ctk.CTkButton(
            topbar,
            text="⚙ Reconfigurar",
            font=FONT_SMALL,
            fg_color="transparent",
            hover_color=BG_MID,
            text_color=TEXT_DIM,
            border_color="#2A2D35",
            border_width=1,
            width=130,
            height=30,
            command=self._open_setup_wizard,
        ).place(relx=1.0, x=-155, y=14)

        # Main layout: left panel + right code panel
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        left = ctk.CTkFrame(main, fg_color="transparent", width=420)
        left.pack(side="left", fill="y", padx=0)
        left.pack_propagate(False)

        right = ctk.CTkFrame(main, fg_color=BG_MID, corner_radius=0)
        right.pack(side="right", fill="both", expand=True)

        self._build_left_panel(left)
        self._build_right_panel(right)

        # Status bar
        self.statusbar = ctk.CTkLabel(
            self,
            text="● Listo",
            font=FONT_SMALL,
            text_color=TEXT_DIM,
            fg_color=BG_CARD,
            anchor="w",
        )
        self.statusbar.pack(fill="x", side="bottom", ipady=4, padx=10)

    def _build_left_panel(self, parent):
        # Model selector card
        card1 = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        card1.pack(fill="x", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            card1, text="MODELO OLLAMA", font=FONT_SMALL, text_color=ACCENT
        ).pack(anchor="w", padx=14, pady=(10, 2))

        model_row = ctk.CTkFrame(card1, fg_color="transparent")
        model_row.pack(fill="x", padx=14, pady=(0, 10))

        self.model_var = ctk.StringVar(value="Cargando...")
        self.model_menu = ctk.CTkOptionMenu(
            model_row,
            variable=self.model_var,
            values=["Cargando..."],
            fg_color=BG_INPUT,
            button_color=BG_MID,
            button_hover_color="#2A2D35",
            dropdown_fg_color=BG_CARD,
            text_color=TEXT_MAIN,
            font=FONT_SMALL,
            dynamic_resizing=False,
            width=240,
        )
        self.model_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            model_row,
            text="↺",
            font=("Consolas", 14),
            fg_color=BG_MID,
            hover_color="#2A2D35",
            text_color=TEXT_DIM,
            width=34,
            height=34,
            command=self._refresh_models,
        ).pack(side="right")

        self.ollama_status = ctk.CTkLabel(
            card1, text="", font=FONT_SMALL, text_color=TEXT_DIM, anchor="w"
        )
        self.ollama_status.pack(fill="x", padx=14, pady=(0, 8))

        # Prompt card
        card2 = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        card2.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(
            card2, text="DESCRIPCIÓN DEL MAPA", font=FONT_SMALL, text_color=ACCENT
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.prompt_box = ctk.CTkTextbox(
            card2,
            height=130,
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            font=FONT_CODE,
            corner_radius=6,
            wrap="word",
            border_color="#2A2D35",
            border_width=1,
        )
        self.prompt_box.pack(fill="x", padx=14, pady=(0, 10))
        self.prompt_box.insert(
            "end",
            "Crea una mazmorra subterránea de 30x30 para nivel 100.\n"
            "Incluye dragones, cofres con tesoro, paredes de piedra,\n"
            "antorchas decorativas y una puerta de entrada bloqueada.",
        )

        # Examples
        ctk.CTkLabel(
            card2, text="Ejemplos rápidos:", font=FONT_SMALL, text_color=TEXT_DIM
        ).pack(anchor="w", padx=14)
        examples_frame = ctk.CTkFrame(card2, fg_color="transparent")
        examples_frame.pack(fill="x", padx=14, pady=(4, 10))

        examples = [
            (
                "🐉 Mazmorra",
                "Crea una mazmorra de 20x20 con dragones, paredes de piedra y cofres de tesoro.",
            ),
            (
                "🌲 Bosque",
                "Genera un área boscosa de 40x40 con árboles, caminos de tierra y decoraciones naturales.",
            ),
            (
                "🏰 Castillo",
                "Diseña el interior de un castillo con sala del trono, paredes de ladrillo y puertas.",
            ),
            (
                "🌊 Puerto",
                "Crea un área portuaria con muelles de madera, agua y decoraciones marinas.",
            ),
        ]
        for label, prompt in examples:
            ctk.CTkButton(
                examples_frame,
                text=label,
                font=FONT_SMALL,
                fg_color=BG_MID,
                hover_color="#2A2D35",
                text_color=TEXT_DIM,
                width=82,
                height=28,
                command=lambda p=prompt: self._set_prompt(p),
            ).pack(side="left", padx=(0, 4))

        # RAG info card
        self.rag_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        self.rag_card.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(
            self.rag_card, text="DATOS CARGADOS", font=FONT_SMALL, text_color=ACCENT
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.rag_info = ctk.CTkLabel(
            self.rag_card,
            text="Cargando datos...",
            font=FONT_SMALL,
            text_color=TEXT_DIM,
            anchor="w",
            wraplength=360,
            justify="left",
        )
        self.rag_info.pack(fill="x", padx=14, pady=(0, 10))

        # Generate button
        self.gen_btn = ctk.CTkButton(
            parent,
            text="▶  GENERAR SCRIPT LUA",
            font=("Consolas", 13, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color="#000000",
            height=48,
            corner_radius=8,
            command=self._generate,
            state="disabled",
        )
        self.gen_btn.pack(fill="x", padx=14, pady=(10, 4))

        self.progress = ctk.CTkProgressBar(
            parent,
            fg_color=BG_CARD,
            progress_color=ACCENT,
            height=4,
            corner_radius=2,
        )
        self.progress.pack(fill="x", padx=14, pady=(0, 4))
        self.progress.set(0)

    def _build_right_panel(self, parent):
        # Header
        hdr = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=0, height=42)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="SCRIPT LUA GENERADO", font=FONT_SMALL, text_color=ACCENT
        ).place(x=14, y=12)

        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.place(relx=1.0, x=-10, y=6, anchor="ne")

        ctk.CTkButton(
            btn_row,
            text="💾 Guardar .lua",
            font=FONT_SMALL,
            fg_color=BG_MID,
            hover_color="#2A2D35",
            text_color=TEXT_DIM,
            border_color="#2A2D35",
            border_width=1,
            width=120,
            height=30,
            command=self._save_script,
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            btn_row,
            text="🗑 Limpiar",
            font=FONT_SMALL,
            fg_color=BG_MID,
            hover_color="#2A2D35",
            text_color=TEXT_DIM,
            border_color="#2A2D35",
            border_width=1,
            width=80,
            height=30,
            command=self._clear_output,
        ).pack(side="right")

        # Code output
        self.output_box = ctk.CTkTextbox(
            parent,
            fg_color=BG_INPUT,
            text_color="#A8D8A8",  # soft green for Lua
            font=FONT_CODE,
            corner_radius=0,
            wrap="none",
        )
        self.output_box.pack(fill="both", expand=True)

        self._show_placeholder()

    # ── Data Loading ───────────────────────────────────────────────────────

    def _load_data_async(self):
        self._set_status("Cargando datos de items.xml...")
        threading.Thread(target=self._load_data_worker, daemon=True).start()

    def _load_data_worker(self):
        try:
            xml_path = self.config.get("items_xml_path", "")
            item_docs = []
            if xml_path and os.path.exists(xml_path):
                self._cache, item_docs = load_items(xml_path)
                total_items = len(self._cache)
                self.after(
                    0,
                    lambda: self.rag_info.configure(
                        text=(
                            f"✓ {total_items:,} items analizados\n"
                            f"✓ {total_items:,} entradas indexadas\n"
                            f"✓ RAG base construida para generación de mapas"
                        ),
                        text_color=TEXT_GREEN,
                    ),
                )
            else:
                item_docs = []
                self.after(
                    0,
                    lambda: self.rag_info.configure(
                        text="⚠ items.xml no configurado. Reconfigura la app.",
                        text_color=TEXT_RED,
                    ),
                )

            monster_docs = []
            monsters_folder = self.config.get("monsters_folder", "")
            if monsters_folder and os.path.exists(monsters_folder):
                self._monster_names, monster_docs = load_monster_names(monsters_folder)

            npc_docs = []
            npcs_folder = self.config.get("npcs_folder", "")
            if npcs_folder and os.path.exists(npcs_folder):
                self._npc_names, npc_docs = load_npc_names(npcs_folder)

            self._studio = AIMapStudio(self.config, item_docs, monster_docs, npc_docs)
            self.after(0, self._enable_generate_btn)
            self.after(
                0,
                lambda: self._set_status(
                    f"✓ Datos cargados — {len(self._monster_names)} monstruos, {len(self._npc_names)} NPCs"
                ),
            )
        except Exception as e:
            error_msg = str(e)
            self.after(
                0,
                lambda msg=error_msg: self.rag_info.configure(
                    text=f"✗ Error al cargar datos:\n{msg}", text_color=TEXT_RED
                ),
            )
            self.after(0, lambda msg=error_msg: self._set_status(f"Error: {msg}"))

        self.after(0, self._refresh_models)

    def _enable_generate_btn(self):
        self.gen_btn.configure(state="normal")

    # ── Model Management ───────────────────────────────────────────────────

    def _refresh_models(self):
        if self._studio is None:
            self.ollama_status.configure(
                text="⚠ Cargando RME Studio...", text_color=TEXT_RED
            )
            self.model_menu.configure(values=["Cargando..."])
            return

        models = self._studio.available_models()
        if models:
            self.ollama_status.configure(
                text="● Ollama disponible", text_color=TEXT_GREEN
            )
            self.model_menu.configure(values=models)
            saved = self.config.get("last_model", "")
            if saved in models:
                self.model_var.set(saved)
            else:
                self.model_var.set(models[0])
        else:
            self.ollama_status.configure(
                text="✗ Ollama no disponible", text_color=TEXT_RED
            )
            self.model_menu.configure(values=["Ollama no disponible"])
            self.model_var.set("Ollama no disponible")

    # ── Generation ─────────────────────────────────────────────────────────

    def _generate(self):
        if self._generating:
            return

        prompt = self.prompt_box.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning(
                "Prompt vacío", "Escribe una descripción del mapa.", parent=self
            )
            return

        model = self.model_var.get()
        if not model or "no disponible" in model.lower() or "cargando" in model.lower():
            messagebox.showerror(
                "Modelo no disponible",
                "Selecciona un modelo de Ollama válido.",
                parent=self,
            )
            return

        if self._studio is None:
            messagebox.showwarning(
                "Datos no cargados",
                "Los datos del estudio AI aún no están listos.",
                parent=self,
            )
            return

        self._generating = True
        self.gen_btn.configure(state="disabled", text="⏳ Generando...")
        self.progress.set(0)
        self._start_progress_animation()

        # Clear output
        self.output_box.delete("1.0", "end")
        self.output_box.configure(text_color="#A8D8A8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_box.insert(
            "end",
            f"-- Generado por AI OpenTibia Map Studio  [{timestamp}]\n"
            f"-- Modelo: {model}\n"
            f"-- Descripción: {prompt[:80]}...\n\n",
        )

        # Save model preference
        self.config["last_model"] = model
        cm.save_config(self.config)

        # Stream in background thread
        threading.Thread(
            target=self._studio.generate_script,
            args=(
                prompt,
                model,
                self._monster_names,
                self._npc_names,
                self._on_chunk,
                self._on_done,
                self._on_error,
            ),
            daemon=True,
        ).start()

    def _on_chunk(self, text: str):
        self.after(0, lambda: self._append_output(text))

    def _on_done(self, full_text: str):
        self._last_script = self.output_box.get("1.0", "end")
        self.after(0, self._generation_done)

    def _on_error(self, msg: str):
        self.after(0, lambda: self._generation_error(msg))

    def _append_output(self, text: str):
        self.output_box.insert("end", text)
        self.output_box.see("end")

    def _generation_done(self):
        self._generating = False
        self.progress.set(1)
        self.gen_btn.configure(state="normal", text="▶  GENERAR SCRIPT LUA")
        self._set_status(
            "✓ Script generado exitosamente. Usa 'Guardar .lua' para exportarlo."
        )
        self.after(2000, lambda: self.progress.set(0))

    def _generation_error(self, msg: str):
        self._generating = False
        self.progress.set(0)
        self.gen_btn.configure(state="normal", text="▶  GENERAR SCRIPT LUA")
        self.output_box.configure(text_color=TEXT_RED)
        self.output_box.insert("end", f"\n\n-- ERROR: {msg}")
        self._set_status(f"✗ Error: {msg}")

    def _start_progress_animation(self):
        if self._generating:
            current = self.progress.get()
            new_val = (current + 0.008) % 0.95
            self.progress.set(new_val)
            self.after(80, self._start_progress_animation)

    # ── UI Helpers ─────────────────────────────────────────────────────────

    def _set_prompt(self, text: str):
        self.prompt_box.delete("1.0", "end")
        self.prompt_box.insert("end", text)

    def _show_placeholder(self):
        self.output_box.delete("1.0", "end")
        self.output_box.configure(text_color=TEXT_DIM)
        placeholder = (
            "-- El script Lua generado aparecerá aquí.\n"
            "-- Configura los archivos de datos y escribe una descripción\n"
            "-- de tu mapa para comenzar.\n\n"
            "-- Ejemplo de lo que se generará:\n"
            "--\n"
            "-- function createDungeon()\n"
            "--   local startX, startY, startZ = 1000, 1000, 7\n"
            "--   for x = 0, 29 do\n"
            "--     for y = 0, 29 do\n"
            "--       local pos = Position(startX + x, startY + y, startZ)\n"
            "--       Map.setTile(pos, 103)  -- stone floor\n"
            "--     end\n"
            "--   end\n"
            "-- end\n"
            "--\n"
            "-- createDungeon()\n"
        )
        self.output_box.insert("end", placeholder)

    def _clear_output(self):
        self._last_script = ""
        self._show_placeholder()
        self._set_status("Salida limpiada.")

    def _save_script(self):
        content = self.output_box.get("1.0", "end").strip()
        if not content or content.startswith("-- El script Lua generado aparecerá"):
            messagebox.showwarning(
                "Sin contenido", "No hay script para guardar.", parent=self
            )
            return

        default_name = f"rme_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.lua"
        path = filedialog.asksaveasfilename(
            defaultextension=".lua",
            filetypes=[("Lua Scripts", "*.lua"), ("Todos", "*.*")],
            initialfile=default_name,
            title="Guardar Script Lua",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._set_status(f"✓ Script guardado en: {path}")
            messagebox.showinfo("Guardado", f"Script guardado:\n{path}", parent=self)

    def _set_status(self, msg: str):
        self.statusbar.configure(text=f"  {msg}")

    def _open_setup_wizard(self):
        wizard = SetupWizard(self, self.config, on_complete=self._on_setup_complete)
        wizard.focus()

    def _on_setup_complete(self):
        self.config = cm.load_config()
        self._set_status("Configuración actualizada. Recargando datos...")
        self.rag_info.configure(text="Recargando...", text_color=TEXT_DIM)
        self.gen_btn.configure(state="disabled")
        self._cache = None
        self._monster_names = []
        self._npc_names = []
        self.after(300, self._load_data_async)


# ═══════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cleanup_expired_artifacts()
    app = RMEAgentApp()

    def _retention_tick() -> None:
        cleanup_expired_artifacts()
        app.after(60 * 60 * 1000, _retention_tick)

    app.after(60 * 60 * 1000, _retention_tick)
    app.mainloop()

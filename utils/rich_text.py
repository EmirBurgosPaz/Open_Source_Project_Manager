"""
utils/rich_text.py — Editor de texto enriquecido reutilizable (RichTextEditor)
y funciones de (de)serialización a JSON, pensado para usarse con NotaRepository.

Formato de almacenamiento (JSON-safe):
    {"runs": [{"texto": "...", "tags": ["bold", "italic", "color_ff8800", ...]}, ...]}

Sigue el mismo estilo que utils/ui_helpers.py: usa C (config.py), tema oscuro,
y expone una clase con estado propio igual que Tooltip / KeybindsHelp.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, font as tkfont
from config import C

# Tags de formato soportados y su configuración visual base.
_TAG_CONFIG = {
    "bold":      {"weight": "bold"},
    "italic":    {"slant": "italic"},
    "underline": {"underline": True},
    "strike":    {"overstrike": True},
    "h1":        {"size": 18, "weight": "bold"},
    "h2":        {"size": 14, "weight": "bold"},
}


# ── Serialización ──────────────────────────────────────────────────────────

def serializar_texto(text_widget: tk.Text) -> dict:
    """Convierte el contenido del Text widget (con tags) a un dict serializable en JSON."""
    runs = []
    activos = set()
    dump = text_widget.dump("1.0", "end-1c", tag=True, text=True)
    for clave, valor, _indice in dump:
        if clave == "tagon":
            if valor in _TAG_CONFIG or valor.startswith("color_"):
                activos.add(valor)
        elif clave == "tagoff":
            activos.discard(valor)
        elif clave == "text" and valor:
            runs.append({"texto": valor, "tags": sorted(activos)})
    return {"runs": runs}


def deserializar_texto(text_widget: tk.Text, data: dict):
    """Reconstruye el contenido de un Text widget a partir del dict serializado."""
    text_widget.delete("1.0", "end")
    for run in (data or {}).get("runs", []):
        inicio = text_widget.index("end-1c")
        text_widget.insert("end", run.get("texto", ""))
        fin = text_widget.index("end-1c")
        for tag in run.get("tags", []):
            if tag.startswith("color_"):
                color = "#" + tag.split("_", 1)[1]
                text_widget.tag_configure(tag, foreground=color)
            text_widget.tag_add(tag, inicio, fin)


# ── Widget editor ────────────────────────────────────────────────────────

class RichTextEditor(tk.Frame):
    """
    Editor de texto enriquecido con barra de herramientas (negrita, cursiva,
    subrayado, tachado, títulos, color). Pensado para integrarse dentro de
    ui/notas_dialog.py, con el tema oscuro del resto de la app.

    Uso:
        editor = RichTextEditor(parent, altura=16)
        editor.pack(fill="both", expand=True)
        editor.set_contenido(nota.contenido)
        ...
        nota.contenido = editor.get_contenido()
    """

    def __init__(self, parent, altura: int = 18, **kwargs):
        super().__init__(parent, bg=C["dlg_bg"], **kwargs)
        self._base_font = tkfont.Font(family="Helvetica", size=11)
        self._construir_toolbar()
        self._construir_texto(altura)
        self._configurar_tags()
        self._bindear_atajos()

    # ── Construcción de UI ──────────────────────────────────────────
    def _construir_toolbar(self):
        barra = tk.Frame(self, bg=C["dlg_bg"])
        barra.pack(fill="x", pady=(0, 6))

        botones = [
            ("N", "bold", "Negrita (Ctrl+B)"),
            ("I", "italic", "Cursiva (Ctrl+I)"),
            ("S", "underline", "Subrayado (Ctrl+U)"),
            ("Tch", "strike", "Tachado"),
            ("H1", "h1", "Título 1"),
            ("H2", "h2", "Título 2"),
        ]
        self._botones = {}
        for texto, tag, _tip in botones:
            btn = tk.Label(
                barra, text=texto, bg=C["border"], fg=C["text"],
                font=("Helvetica", 10, "bold"), width=3, cursor="hand2",
                relief="flat", padx=4, pady=2,
            )
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda e, t=tag: self._alternar_tag(t))
            self._botones[tag] = btn

        color_btn = tk.Label(
            barra, text="Color", bg=C["border"], fg=C["text"],
            font=("Helvetica", 10), cursor="hand2", relief="flat", padx=8, pady=2,
        )
        color_btn.pack(side="left", padx=(4, 0))
        color_btn.bind("<Button-1>", lambda e: self._elegir_color())

    def _construir_texto(self, altura):
        contenedor = tk.Frame(self, bg=C["dlg_border"])
        contenedor.pack(fill="both", expand=True)

        self.texto = tk.Text(
            contenedor, height=altura, wrap="word",
            font=self._base_font, bg=C["dlg_input"], fg=C["text"],
            insertbackground=C["accent_hover"], relief="flat", bd=0,
            padx=10, pady=8, undo=True,
        )
        scrollbar = ttk.Scrollbar(contenedor, command=self.texto.yview)
        self.texto.configure(yscrollcommand=scrollbar.set)
        self.texto.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scrollbar.pack(side="right", fill="y")

    def _configurar_tags(self):
        """Crea cada tag como una variación del font base, para que los
        tamaños/negritas se combinen visualmente sin pisarse entre sí."""
        for tag, cfg in _TAG_CONFIG.items():
            opciones = {}
            f = tkfont.Font(font=self._base_font)
            if "weight" in cfg:
                f.configure(weight=cfg["weight"])
            if "slant" in cfg:
                f.configure(slant=cfg["slant"])
            if "size" in cfg:
                f.configure(size=cfg["size"])
            opciones["font"] = f
            if "underline" in cfg:
                opciones["underline"] = cfg["underline"]
            if "overstrike" in cfg:
                opciones["overstrike"] = cfg["overstrike"]
            self.texto.tag_configure(tag, **opciones)

    def _bindear_atajos(self):
        def _atajo(tag):
            return lambda e: (self._alternar_tag(tag), "break")[1]

        self.texto.bind("<Control-b>", _atajo("bold"))
        self.texto.bind("<Control-i>", _atajo("italic"))
        self.texto.bind("<Control-u>", _atajo("underline"))

    # ── Lógica de formato ────────────────────────────────────────────
    def _alternar_tag(self, tag: str):
        try:
            inicio, fin = self.texto.index("sel.first"), self.texto.index("sel.last")
        except tk.TclError:
            return  # no hay texto seleccionado
        tags_actuales = self.texto.tag_names("sel.first")
        if tag in tags_actuales:
            self.texto.tag_remove(tag, inicio, fin)
        else:
            self.texto.tag_add(tag, inicio, fin)

    def _elegir_color(self):
        try:
            self.texto.index("sel.first")
        except tk.TclError:
            return  # no hay texto seleccionado
        color = colorchooser.askcolor(title="Elegir color de texto")[1]
        if not color:
            return
        tag = "color_" + color.lstrip("#")
        self.texto.tag_configure(tag, foreground=color)
        self.texto.tag_add(tag, "sel.first", "sel.last")

    # ── API pública ──────────────────────────────────────────────────
    def get_contenido(self) -> dict:
        return serializar_texto(self.texto)

    def set_contenido(self, data: dict):
        deserializar_texto(self.texto, data)

    def limpiar(self):
        self.texto.delete("1.0", "end")
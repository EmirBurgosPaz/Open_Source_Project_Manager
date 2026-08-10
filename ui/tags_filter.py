"""
ui/widgets/tags_filter_bar.py

Fila de chips de tags para filtrar la lista de queries. Click en un chip
lo activa/desactiva; un botón alterna el modo AND / OR. En cada cambio
llama on_change(tags_seleccionados_display, modo).

Uso:
    self.tags_filter_bar = TagsFilterBar(
        container, self.tags_manager, on_change=self._on_tags_filter_change,
        bg=C["bg"], fg=C["white"]
    )
    self.tags_filter_bar.pack(fill="x", pady=(0, 10))

    # tras crear/editar/eliminar tags en otro lado:
    self.tags_filter_bar.refresh()
"""

import tkinter as tk
from config import C
from utils.ui_helpers import add_hover, lighten

class TagsFilterBar(tk.Frame):
    def __init__(self, parent, tags_manager, on_change, bg="#1e1e1e", fg="#ffffff", **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.tags_manager = tags_manager
        self.on_change = on_change
        self.bg = bg
        self.fg = fg
        self._seleccionados = set()  # claves normalizadas
        self._modo = "OR"

        self.header = tk.Frame(self, bg=bg)
        self.header.pack(fill="x", anchor="w")

        tk.Label(self.header, text="🏷️ Tags:", bg=bg, fg=fg,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))

        self.btn_modo = tk.Button(
            self.header, text="Modo: cualquiera (OR)", command=self._toggle_modo,
            bg=C["button"], fg=fg, relief="flat", font=("Segoe UI", 8), padx=6
        )
        add_hover(self.btn_modo , lighten(C["accent"], 0.25), C["button"])
        self.btn_modo.pack(side="left", padx=(0, 10))

        self.btn_limpiar = tk.Button(
            self.header, text="Limpiar", command=self.limpiar,
            bg=C["button"], fg=fg, relief="flat", font=("Segoe UI", 8), padx=6
        )
        add_hover(self.btn_limpiar , lighten(C["accent"], 0.25), C["button"])
        self.btn_limpiar.pack(side="left")

        self.chips_row = tk.Frame(self, bg=bg)
        self.chips_row.pack(fill="x", anchor="w", pady=(4, 0))

        self.refresh()

    def refresh(self):
        """Repinta los chips disponibles. Llamar tras crear/renombrar/borrar tags."""
        for w in self.chips_row.winfo_children():
            w.destroy()

        tags = self.tags_manager.obtener_todos()
        if not tags:
            tk.Label(self.chips_row, text="(sin tags todavía)", bg=self.bg,
                     fg="#888888", font=("Segoe UI", 8)).pack(side="left")
            return

        # Descarta selecciones de tags que ya no existen (renombrados/eliminados)
        claves_vigentes = {t["clave"] for t in tags}
        self._seleccionados &= claves_vigentes

        for t in tags:
            activo = t["clave"] in self._seleccionados
            self._crear_chip(t, activo)

    def _crear_chip(self, t, activo):
        color = t["color"] if activo else "#3a3a3a"
        chip = tk.Frame(self.chips_row, bg=color, highlightbackground=t["color"],
                         highlightthickness=1)
        lbl = tk.Label(chip, text=t["display"], bg=color,
                       fg="white" if activo else "#cccccc",
                       font=("Segoe UI", 9), padx=8, pady=3, cursor="hand2")
        lbl.pack()
        lbl.bind("<Button-1>", lambda e, clave=t["clave"]: self._toggle_tag(clave))
        chip.pack(side="left", padx=(0, 6), pady=2)

    def _toggle_tag(self, clave):
        if clave in self._seleccionados:
            self._seleccionados.discard(clave)
        else:
            self._seleccionados.add(clave)
        self.refresh()
        self._emit()

    def _toggle_modo(self):
        self._modo = "AND" if self._modo == "OR" else "OR"
        texto = "Modo: todos (AND)" if self._modo == "AND" else "Modo: cualquiera (OR)"
        self.btn_modo.config(text=texto)
        if self._seleccionados:
            self._emit()

    def limpiar(self):
        if not self._seleccionados:
            return
        self._seleccionados.clear()
        self.refresh()
        self._emit()

    def _emit(self):
        seleccion_display = [self.tags_manager.display_de(c) for c in self._seleccionados]
        self.on_change(seleccion_display, self._modo)
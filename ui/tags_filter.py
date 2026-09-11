"""
ui/widgets/tags_filter_bar.py

Filtro de tags por dropdown (combobox de selección múltiple) para no
ocupar espacio fijo en la vista con una fila de chips. Se abre un menú
con checkbuttons, uno por tag, coloreado según el color del tag. Un
botón alterna el modo AND / OR. En cada cambio llama
on_change(tags_seleccionados_display, modo).

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

        # clave -> tk.BooleanVar del checkbutton correspondiente en el menú
        self._vars = {}

        self.header = tk.Frame(self, bg=bg)
        self.header.pack(fill="x", anchor="w")

        tk.Label(self.header, text="🏷️ Tags:", bg=bg, fg=fg,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))

        # --- Dropdown de selección múltiple (reemplaza la fila de chips) ---
        # Importante: el Menu debe crearse con el Menubutton como padre
        # (master=self.mb), si no, en varios entornos el click no despliega
        # el menú.
        self.mb = tk.Menubutton(
            self.header, text="Todos los tags",
            bg=C["button"], fg=fg, relief="flat", font=("Segoe UI", 9),
            padx=8, pady=2, direction="below", anchor="w"
        )
        add_hover(self.mb, lighten(C["accent"], 0.25), C["button"])
        self.mb.pack(side="left", padx=(0, 10))

        self.menu = tk.Menu(self.mb, tearoff=0, bg="#2a2a2a", fg=fg,
                             activebackground=C["accent"], activeforeground="white",
                             font=("Segoe UI", 9))
        self.mb.config(menu=self.menu)

        self.btn_modo = tk.Button(
            self.header, text="Modo: cualquiera (OR)", command=self._toggle_modo,
            bg=C["button"], fg=fg, relief="flat", font=("Segoe UI", 8), padx=6
        )
        add_hover(self.btn_modo, lighten(C["accent"], 0.25), C["button"])
        self.btn_modo.pack(side="left", padx=(0, 10))

        self.btn_limpiar = tk.Button(
            self.header, text="Limpiar", command=self.limpiar,
            bg=C["button"], fg=fg, relief="flat", font=("Segoe UI", 8), padx=6,
            state="disabled"
        )
        add_hover(self.btn_limpiar, lighten(C["accent"], 0.25), C["button"])
        self.btn_limpiar.pack(side="left")

        self.refresh()

    # ------------------------------------------------------------------
    # Reconstrucción del menú (solo cuando cambian los tags disponibles:
    # crear, renombrar o borrar un tag desde otro lado)
    # ------------------------------------------------------------------
    def refresh(self):
        """Repuebla el dropdown. Llamar tras crear/renombrar/borrar tags."""
        self.menu.delete(0, "end")
        self._vars.clear()

        tags = self.tags_manager.obtener_todos()

        if not tags:
            self.menu.add_command(label="(sin tags todavía)", state="disabled")
            self._seleccionados.clear()
            self._actualizar_estado()
            return

        # Descarta selecciones de tags que ya no existen (renombrados/eliminados)
        claves_vigentes = {t["clave"] for t in tags}
        habia_cambios = not self._seleccionados.issubset(claves_vigentes)
        self._seleccionados &= claves_vigentes

        for t in tags:
            clave = t["clave"]
            var = tk.BooleanVar(value=clave in self._seleccionados)
            self._vars[clave] = var
            self.menu.add_checkbutton(
                label=t["display"],
                variable=var,
                onvalue=True, offvalue=False,
                foreground=t["color"],
                selectcolor=t["color"],
                activeforeground=t["color"],
                command=lambda c=clave: self._on_check(c),
            )

        self.menu.add_separator()
        self.menu.add_command(label="Limpiar selección", command=self.limpiar)

        self._actualizar_estado()
        if habia_cambios:
            self._emit()

    # ------------------------------------------------------------------
    # Interacción: cambiar un checkbutton NO reconstruye el menú, solo
    # actualiza el set de selección y el texto del botón. Esto es lo que
    # lo hace instantáneo aunque haya muchos tags.
    # ------------------------------------------------------------------
    def _on_check(self, clave):
        var = self._vars.get(clave)
        if var is None:
            return
        if var.get():
            self._seleccionados.add(clave)
        else:
            self._seleccionados.discard(clave)
        self._actualizar_estado()
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
        for var in self._vars.values():
            var.set(False)
        self._seleccionados.clear()
        self._actualizar_estado()
        self._emit()

    # ------------------------------------------------------------------
    # Texto del Menubutton: resume la selección para que el usuario sepa
    # qué está filtrando sin tener que abrir el dropdown.
    # ------------------------------------------------------------------
    def _actualizar_estado(self):
        n = len(self._seleccionados)
        if n == 0:
            texto = "Todos los tags"
        elif n <= 2:
            displays = [self.tags_manager.display_de(c) for c in self._seleccionados]
            texto = ", ".join(displays)
        else:
            texto = f"{n} tags seleccionados"
        self.mb.config(text=texto)
        self.btn_limpiar.config(state="normal" if n else "disabled")

    def _emit(self):
        seleccion_display = [self.tags_manager.display_de(c) for c in self._seleccionados]
        self.on_change(seleccion_display, self._modo)
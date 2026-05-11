"""
ui/project_dialog.py — Diálogo para crear y editar proyectos.
"""

import tkinter as tk
from config import C, PROJECT_COLORS
from utils.ui_helpers import make_label, make_entry, center_window


class ProjectDialog(tk.Toplevel):
    """
    Resultado en `self.result`:
      - None              → cancelado
      - {"deleted": True} → borrar proyecto
      - {"name": ..., "color": ...} → crear/actualizar
    """

    def __init__(self, parent, project: dict = None):
        super().__init__(parent)
        self.result  = None
        self.project = project

        self.title("Editar proyecto" if project else "Nuevo proyecto")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()

        self.selected_color = tk.StringVar(
            value=project["color"] if project else PROJECT_COLORS[0]
        )

        self._build(project)
        self.e_name.focus()
        center_window(self, parent)

    def _build(self, project):
        bg = C["dlg_bg"]

        make_label(self, "Nombre del proyecto", bg=bg).pack(anchor="w", padx=16, pady=(16, 2))
        self.e_name = make_entry(self, project["name"] if project else "")
        self.e_name.pack(fill="x", padx=16)

        make_label(self, "Color", bg=bg).pack(anchor="w", padx=16, pady=(12, 6))

        grid = tk.Frame(self, bg=bg)
        grid.pack(padx=16, pady=(0, 4))
        self._swatches = []
        for i, color in enumerate(PROJECT_COLORS):
            btn = tk.Label(grid, bg=color, width=3, height=1, cursor="hand2", relief="flat", bd=2)
            btn.grid(row=i // 5, column=i % 5, padx=3, pady=3)
            btn.bind("<Button-1>", lambda e, c=color: self._pick_color(c))
            self._swatches.append((btn, color))
        self._update_swatches()

        prev_row = tk.Frame(self, bg=bg)
        prev_row.pack(padx=16, pady=(4, 0))
        make_label(prev_row, "Vista previa:", bg=bg).pack(side="left")
        self.preview_dot = tk.Label(prev_row, text="  ●  Nombre del proyecto",
                                    bg=bg, fg=self.selected_color.get(),
                                    font=("Helvetica", 10))
        self.preview_dot.pack(side="left", padx=6)
        self.e_name.bind("<KeyRelease>", self._update_preview)

        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(12, 0))
        self._build_buttons(project, bg)

    def _build_buttons(self, project, bg):
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if project:
            tk.Button(btn_row, text="Eliminar proyecto",
                      bg="#3A1A1A", fg="#E05555",
                      font=("Helvetica", 10), relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=self._on_delete).pack(side="left")

        tk.Button(btn_row, text="Cancelar",
                  bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_row, text="Guardar" if project else "Crear proyecto",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._on_save).pack(side="right")

    def _pick_color(self, color):
        self.selected_color.set(color)
        self._update_swatches()
        self._update_preview()

    def _update_swatches(self):
        selected = self.selected_color.get()
        for btn, color in self._swatches:
            btn.config(relief="solid" if color == selected else "flat",
                       bd=2 if color == selected else 0,
                       highlightthickness=2 if color == selected else 0,
                       highlightbackground="#FFFFFF" if color == selected else C["dlg_bg"])

    def _update_preview(self, event=None):
        name = self.e_name.get().strip() or "Nombre del proyecto"
        self.preview_dot.config(text=f"  ●  {name}", fg=self.selected_color.get())

    def _on_save(self):
        from tkinter import messagebox
        name = self.e_name.get().strip()
        if not name:
            messagebox.showwarning("Campo vacío", "El nombre no puede estar vacío.", parent=self)
            return
        self.result = {"name": name, "color": self.selected_color.get()}
        self.destroy()

    def _on_delete(self):
        self.result = {"deleted": True}
        self.destroy()

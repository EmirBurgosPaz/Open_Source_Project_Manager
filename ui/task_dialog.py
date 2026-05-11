"""
ui/task_dialog.py — Diálogo para crear y editar tareas.
Solo responsabilidad: capturar datos del usuario y devolverlos.
La validación y guardado los hace TaskService.
"""

import tkinter as tk
from datetime import date
from config import C, COLUMNS, PRIORITY_OPTIONS, MEMBERS
from utils.ui_helpers import make_label, make_entry, make_dark_combobox, center_window


class TaskDialog(tk.Toplevel):
    """
    Abre un formulario modal para crear o editar una tarea.
    Tras cerrarse, consultar `self.result`:
      - None      → usuario canceló
      - {"deleted": True} → usuario quiso eliminar
      - dict con los campos → datos listos para TaskService
    """

    def __init__(self, parent, projects: list, task: dict = None, default_status: str = "todo"):
        super().__init__(parent)
        self.result   = None
        self.projects = projects
        self.task     = task
        self.prio_var = None
        self.assign_var = None

        self.title("Editar tarea" if task else "Nueva tarea")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()

        self._build(task, default_status)
        self.e_title.focus()
        center_window(self, parent)

    # ── Construcción del formulario ───────────────────────────────────────────

    def _build(self, task, default_status):
        bg = C["dlg_bg"]

        make_label(self, "Título").pack(anchor="w", padx=16, pady=(8, 2))
        self.e_title = make_entry(self, task["title"] if task else "")
        self.e_title.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Descripción").pack(anchor="w", padx=16, pady=(8, 2))
        self.e_desc = make_entry(self, task.get("description", "") if task else "")
        self.e_desc.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Proyecto").pack(anchor="w", padx=16, pady=(8, 2))
        proj_names   = [p["name"] for p in self.projects]
        default_proj = next((p["name"] for p in self.projects
                             if task and p["id"] == task.get("project")), proj_names[0])
        self.proj_var, proj_cb = make_dark_combobox(self, proj_names, default_proj)
        proj_cb.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Estado").pack(anchor="w", padx=16, pady=(8, 2))
        status_labels    = [c[1] for c in COLUMNS]
        self._status_ids = [c[0] for c in COLUMNS]
        default_st = (next((c[1] for c in COLUMNS if c[0] == task["status"]), status_labels[0])
                      if task else
                      next((c[1] for c in COLUMNS if c[0] == default_status), status_labels[1]))
        self.status_var, status_cb = make_dark_combobox(self, status_labels, default_st)
        status_cb.pack(fill="x", padx=16, pady=(0, 2))

        # Fila: Prioridad + Asignado
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        for side, label_text, attr, opts, default_val in [
            ("left",  "Prioridad",  "prio_var",   PRIORITY_OPTIONS, task["priority"] if task else "Media"),
            ("left",  "Asignado a", "assign_var",  MEMBERS,          task["assign"]   if task else MEMBERS[0]),
        ]:
            col = tk.Frame(row, bg=bg)
            col.pack(side=side, fill="x", expand=True)
            make_label(col, label_text, bg=bg).pack(anchor="w", padx=16, pady=(8, 2))
            var, cb = make_dark_combobox(col, opts, default_val)
            cb.pack(fill="x", padx=16, pady=(0, 2))
            setattr(self, attr, var)

        make_label(self, "Fecha límite (AAAA-MM-DD)").pack(anchor="w", padx=16, pady=(8, 2))
        self.e_due = make_entry(self, task["due"] if task else str(date.today()))
        self.e_due.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Fecha de creación").pack(anchor="w", padx=16, pady=(8, 2))
        self.e_created = make_entry(
            self,
            task.get("created", str(date.today())) if task else str(date.today()),
            disabled=True,
        )
        self.e_created.pack(fill="x", padx=16, pady=(0, 2))

        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(12, 0))
        self._build_buttons(task, bg)

    def _build_buttons(self, task, bg):
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if task:
            tk.Button(btn_row, text="Eliminar",
                      bg="#3A1A1A", fg="#E05555",
                      font=("Helvetica", 10), relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=self._on_delete).pack(side="left")

        tk.Button(btn_row, text="Cancelar",
                  bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_row, text="Guardar" if task else "Crear tarea",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._on_save).pack(side="right")

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_save(self):
        status_label = self.status_var.get()
        status_labels = [c[1] for c in COLUMNS]
        status_idx = status_labels.index(status_label)
        proj_name  = self.proj_var.get()
        proj       = next(p for p in self.projects if p["name"] == proj_name)

        self.result = {
            "title":       self.e_title.get().strip(),
            "project":     proj["id"],
            "description": self.e_desc.get().strip(),
            "status":      self._status_ids[status_idx],
            "priority":    self.prio_var.get(),
            "assign":      self.assign_var.get(),
            "due":         self.e_due.get().strip(),
            "created":     self.e_created.get().strip(),
        }
        self.destroy()

    def _on_delete(self):
        from tkinter import messagebox
        if messagebox.askyesno("Eliminar", "¿Eliminar esta tarea?", parent=self):
            self.result = {"deleted": True}
            self.destroy()

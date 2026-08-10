"""
ui/task_dialog.py — Diálogo para crear y editar tareas.
Solo responsabilidad: capturar datos del usuario y devolverlos.
La validación y guardado los hace TaskService.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date
from config import C, COLUMNS_STATUS, PRIORITY_OPTIONS, KEYBOARD_KEYS, COLUMNS_STATUS_DEFAULT, POSITIONS_OPTIONS
import config
from utils.ui_helpers import make_label, make_entry, make_dark_combobox, center_window, add_hover, lighten

class TaskDialog(tk.Toplevel):
    """
    Abre un formulario modal para crear o editar una tarea.
    Tras cerrarse, consultar `self.result`:
      - None      → usuario canceló
      - {"deleted": True} → usuario quiso eliminar
      - dict con los campos → datos listos para TaskService
    """

    WIDTH = 460

    def __init__(self, parent, projects: list, task: dict = None, default_status: str = "todo", default_project_id=None):
        super().__init__(parent)

        self.result = None
        self.projects = projects
        self.task = task
        self.prio_var = None
        self.assign_var = None
        self.default_project_id = default_project_id
        self.position_var = None

        # Ocultar ventana mientras se construye
        self.withdraw()

        self.title("Editar tarea" if task else "Nueva tarea")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.transient(parent)
        self.grab_set()

        self._build(task, default_status)
        self.bind(KEYBOARD_KEYS["enter"], self._on_save)
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)
        self.e_title.focus()

        # Mostrar y centrar SOLO después de construir todo
        self.update_idletasks()
        center_window(self, parent)
        self.deiconify()

    # ── Helpers visuales ───────────────────────────────────────────────────

    def _section(self, parent, text):
        """Encabezado pequeño de sección, con línea divisoria arriba."""
        wrap = tk.Frame(parent, bg=C["dlg_bg"])
        wrap.pack(fill="x", padx=16, pady=(14, 4))
        tk.Frame(wrap, bg=C["dlg_border"], height=1).pack(fill="x", pady=(0, 6))
        tk.Label(
            wrap, text=text.upper(), bg=C["dlg_bg"], fg=C["accent"],
            font=("Helvetica", 8, "bold"),
        ).pack(anchor="w")
        return wrap

    def _grid_row(self, parent, fields):
        """
        Renderiza una fila de N campos lado a lado en un grid parejo.
        fields: lista de tuplas (label_text, builder_fn) donde builder_fn(col_frame) -> widget
        """
        row = tk.Frame(parent, bg=C["dlg_bg"])
        row.pack(fill="x", padx=16)
        for i, (label_text, builder_fn) in enumerate(fields):
            col = tk.Frame(row, bg=C["dlg_bg"])
            col.grid(row=0, column=i, sticky="nsew", padx=(0, 10) if i < len(fields) - 1 else 0)
            row.grid_columnconfigure(i, weight=1, uniform="col")
            make_label(col, label_text, bg=C["dlg_bg"]).pack(anchor="w", pady=(0, 2))
            builder_fn(col)
        return row

    def _style_entry(self, entry):
        """Aplica un borde sutil que resalta en foco, sin romper si el widget no lo soporta."""
        try:
            entry.configure(
                highlightthickness=1,
                highlightbackground=C["dlg_border"],
                highlightcolor=C["accent"],
                bd=0,
            )
        except Exception:
            pass
        return entry

    # ── Construcción del formulario ───────────────────────────────────────

    def _build(self, task, default_status):
        bg = C["dlg_bg"]
        self.minsize(self.WIDTH, 0)

        # ── Sección: Datos generales ──
        self._section(self, "Datos generales")

        # Título (ancho completo, es el campo más importante)
        title_wrap = tk.Frame(self, bg=bg)
        title_wrap.pack(fill="x", padx=16, pady=(0, 6))
        make_label(title_wrap, "Solicitud", bg=bg).pack(anchor="w", pady=(0, 2))
        self.e_title = self._style_entry(make_entry(title_wrap, task["title"] if task else ""))
        self.e_title.pack(fill="x", ipady=3)

        # Proyecto / Posición
        proj_names = [p["name"] for p in self.projects]
        target_id = task.get("project") if task else self.default_project_id
        default_proj = next((p["name"] for p in self.projects if p["id"] == target_id), proj_names[0])

        self._position_map = dict(POSITIONS_OPTIONS)
        position_labels = [p[0] for p in POSITIONS_OPTIONS]
        default_position = task.get("position", position_labels[0]) if task else ""

        def build_proj(col):
            self.proj_var, cb = make_dark_combobox(col, proj_names, default_proj)
            cb.pack(fill="x")

        def build_position(col):
            self.position_var, cb = make_dark_combobox(col, position_labels, default_position)
            cb.pack(fill="x")
            cb.bind("<<ComboboxSelected>>", self._on_position_change)

        self._grid_row(self, [
            ("Proyecto", build_proj),
            ("Posición", build_position),
        ])

        # Solicitante / Area
        def build_requester(col):
            self.e_desc = self._style_entry(make_entry(col, task.get("requester", "") if task else ""))
            self.e_desc.pack(fill="x", ipady=3)

        def build_client(col):
            self.e_client = self._style_entry(make_entry(col, task.get("client", "") if task else ""))
            self.e_client.pack(fill="x", ipady=3)

        self._grid_row(self, [
            ("Solicitante", build_requester),
            ("Area", build_client),
        ])

        # ── Sección: Estado y responsable ──
        self._section(self, "Estado y responsable")

        status_labels = [c[1] for c in COLUMNS_STATUS]
        status_ids = [c[0] for c in COLUMNS_STATUS]
        if task:
            default_status_label = next((c[1] for c in COLUMNS_STATUS if c[0] == task.get("status", COLUMNS_STATUS_DEFAULT)), status_labels[0])
        else:
            default_status_label = next((c[1] for c in COLUMNS_STATUS if c[0] == COLUMNS_STATUS_DEFAULT), status_labels[0])
        self._status_ids = status_ids

        def build_auth(col):
            self.e_auth = self._style_entry(
                make_entry(col, self._position_map.get(default_position, ""), disabled=True)
            )
            self.e_auth.pack(fill="x", ipady=3)

        def build_status(col):
            self.status_var, cb = make_dark_combobox(col, status_labels, default_status_label)
            cb.pack(fill="x")

        self._grid_row(self, [
            ("Autorización", build_auth),
            ("Estado", build_status),
        ])

        def build_prio(col):
            self.prio_var, cb = make_dark_combobox(col, PRIORITY_OPTIONS, task["priority"] if task else "Media")
            cb.pack(fill="x")

        def build_assign(col):
            member_names = [m["name"] for m in config.MEMBERS]
            self.assign_var, cb = make_dark_combobox(
                col, member_names, task["assign"] if task else config.MEMBERS[0]["name"]
            )
            cb.pack(fill="x")

        self._grid_row(self, [
            ("Prioridad", build_prio),
            ("Asignado a", build_assign),
        ])

        # ── Sección: Fechas ──
        self._section(self, "Fechas")

        def build_due(col):
            self.e_due = self._style_entry(make_entry(col, task["due"] if task else str(date.today())))
            self.e_due.pack(fill="x", ipady=3)

        def build_created(col):
            self.e_created = self._style_entry(make_entry(
                col, task.get("created", str(date.today())) if task else str(date.today()), disabled=True
            ))
            self.e_created.pack(fill="x", ipady=3)

        self._grid_row(self, [
            ("Fecha límite (AAAA-MM-DD)", build_due),
            ("Fecha de creación", build_created),
        ])

        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(16, 0))
        self._build_buttons(task, bg)

    def _build_buttons(self, task, bg):
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if task:
            delete_btn = tk.Button(
                btn_row, text="Eliminar", bg=C["button"],fg=C["white"],
                font=("Helvetica", 10), relief="flat", bd=0,
                padx=10, pady=6, cursor="hand2",
                activeforeground=C["button"],
                command=self._on_delete,
            )
            delete_btn.pack(side="left")
            add_hover(delete_btn, lighten(C["delete"], 0.35), C["button"])

        cancel_btn = tk.Button(
            btn_row, text="Cancelar", bg=C["button"],fg=C["white"],
            font=("Helvetica", 10), relief="flat", bd=0,
            padx=10, pady=6, cursor="hand2",
            activeforeground=C["button"],
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(6, 0))
        add_hover(cancel_btn, lighten(C["accent"], 0.25), C["button"])

        save_btn = tk.Button(
            btn_row, text="Guardar" if task else "Crear tarea", bg=C["button"],fg=C["white"],
            font=("Helvetica", 10, "bold"), relief="flat", bd=0,
            padx=14, pady=6, cursor="hand2",
            activeforeground=C["button"],
            command=self._on_save,
        )
        save_btn.pack(side="right")
        add_hover(save_btn,  lighten(C["accent"], 0.15), C["button"])

    # ── Handlers ─────────────────────────────────────────────────────────

    def _on_position_change(self, event=None):
        position = self.position_var.get()
        authorization = self._position_map.get(position, "")

        self.e_auth.configure(state="normal")
        self.e_auth.delete(0, tk.END)
        self.e_auth.insert(0, authorization)
        self.e_auth.configure(state="disabled")

    def _on_save(self, event=None):
        # Validación mínima: el título es obligatorio
        title = self.e_title.get().strip()
        if not title:
            messagebox.showwarning("Falta información", "La solicitud (título) no puede estar vacía.", parent=self)
            self.e_title.focus()
            return

        due = self.e_due.get().strip()
        if due:
            try:
                date.fromisoformat(due)
            except ValueError:
                messagebox.showwarning(
                    "Fecha inválida",
                    "La fecha límite debe tener el formato AAAA-MM-DD.",
                    parent=self,
                )
                self.e_due.focus()
                return

        status_idx = [c[1] for c in COLUMNS_STATUS].index(self.status_var.get())

        proj_name = self.proj_var.get()
        proj = next(p for p in self.projects if p["name"] == proj_name)

        self.result = {
            "title": title,
            "project": proj["id"],
            "requester": self.e_desc.get().strip(),
            "client": self.e_client.get().strip(),
            "position": self.position_var.get(),
            "authorization": self.e_auth.get().strip(),
            "status": self._status_ids[status_idx],
            "priority": self.prio_var.get(),
            "assign": self.assign_var.get(),
            "due": due,
            "created": self.e_created.get().strip(),
        }
        self.destroy()

    def _on_delete(self):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta tarea?", parent=self):
            self.result = {"deleted": True}
            self.destroy()

    def _on_close(self, event=None):
        self.destroy()
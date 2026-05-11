"""
Project Manager — Aplicación de gestión de proyectos
Requiere: Python 3.8+ (tkinter viene incluido)
Ejecutar: python project_manager.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, date

# ── Datos iniciales ──────────────────────────────────────────────────────────

DATA_FILE = "projects_data.json"

DEFAULT_PROJECTS = [
    {"id": "p1", "name": "App Móvil",   "color": "#7C6FE0"},
    {"id": "p2", "name": "Sitio Web",   "color": "#1D9E75"},
    {"id": "p3", "name": "API Backend", "color": "#EF9F27"},
]

DEFAULT_TASKS = [
    {"id": 1, "title": "Diseño de pantallas de onboarding",  "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Ana R.",    "due": "2026-05-15"},
    {"id": 2, "title": "Integración con Firebase Auth",       "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Carlos M.", "due": "2026-05-18"},
    {"id": 3, "title": "Componente de búsqueda global",       "status": "todo",     "project": "p2", "priority": "Media", "assign": "Laura P.",  "due": "2026-05-20"},
    {"id": 4, "title": "Optimización de imágenes WebP",       "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-10"},
    {"id": 5, "title": "Endpoint de pagos con Stripe",        "status": "review",   "project": "p3", "priority": "Alta",  "assign": "Jorge G.",  "due": "2026-05-14"},
    {"id": 6, "title": "Tests de integración en CI/CD",       "status": "todo",     "project": "p3", "priority": "Media", "assign": "Carlos M.", "due": "2026-05-22"},
    {"id": 7, "title": "Documentación de la API REST",        "status": "backlog",  "project": "p3", "priority": "Baja",  "assign": "Laura P.",  "due": "2026-05-30"},
    {"id": 8, "title": "Push notifications iOS",              "status": "backlog",  "project": "p1", "priority": "Media", "assign": "Jorge G.",  "due": "2026-05-28"},
    {"id": 9, "title": "Rediseño del footer",                 "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-08"},
]

COLUMNS = [
    ("backlog",  "Backlog",       "#6B6A66"),
    ("todo",     "Por hacer",     "#4A90D9"),
    ("progress", "En progreso",   "#E6A817"),
    ("review",   "En revisión",   "#9B8FE8"),
    ("done",     "Completado",    "#2ECC71"),
]

PRIORITY_COLORS = {"Alta": "#E05555", "Media": "#E6A817", "Baja": "#2ECC71"}
MEMBERS = ["Ana R.", "Carlos M.", "Laura P.", "Jorge G."]

PROJECT_COLORS = [
    "#7C6FE0", "#1D9E75", "#EF9F27", "#E05555", "#4A90D9",
    "#E8678A", "#2ECC71", "#F39C12", "#1ABC9C", "#9B59B6",
]

# ── Paleta oscura ────────────────────────────────────────────────────────────

C = {
    "bg":        "#1A1A1E",
    "sidebar":   "#141417",
    "panel":     "#22222A",
    "border":    "#2E2E38",
    "text":      "#E8E8EC",
    "muted":     "#7A7A8A",
    "accent":    "#7C6FE0",
    "accent_dk": "#5A4FBA",
    "hover":     "#2A2A36",
    "row_alt":   "#1F1F26",
    # tags proyecto
    "tag_p1_bg": "#2A2542", "tag_p1_fg": "#A090F0",
    "tag_p2_bg": "#1A3028", "tag_p2_fg": "#40C48A",
    "tag_p3_bg": "#332A10", "tag_p3_fg": "#E6A817",
    # diálogo
    "dlg_bg":    "#1E1E26",
    "dlg_input": "#2A2A36",
    "dlg_border":"#3A3A4A",
}

# ── Persistencia ─────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d.get("projects", DEFAULT_PROJECTS), d.get("tasks", DEFAULT_TASKS), d.get("next_id", 10)
    return DEFAULT_PROJECTS, DEFAULT_TASKS, 10

def save_data(projects, tasks, next_id):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"projects": projects, "tasks": tasks, "next_id": next_id}, f, ensure_ascii=False, indent=2)

# ── Diálogo: Nueva / Editar tarea ────────────────────────────────────────────

class TaskDialog(tk.Toplevel):
    def __init__(self, parent, projects, task=None, default_status="todo"):
        super().__init__(parent)
        self.result   = None
        self.projects = projects
        self.task     = task

        self.title("Editar tarea" if task else "Nueva tarea")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()

        self._build(task, default_status)
        self.e_title.focus()
        self._center(parent)

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=C["dlg_bg"], fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", padx=16, pady=(8, 2))

    def _entry(self, parent, value=""):
        e = tk.Entry(parent, font=("Helvetica", 11),
                     bg=C["dlg_input"], fg=C["text"],
                     insertbackground=C["text"],
                     relief="flat", bd=0,
                     highlightthickness=1,
                     highlightbackground=C["dlg_border"],
                     highlightcolor=C["accent"])
        e.pack(fill="x", padx=16, pady=(0, 2))
        if value:
            e.insert(0, value)
        return e

    def _combo(self, parent, values, default):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=C["dlg_input"],
                        background=C["dlg_input"],
                        foreground=C["text"],
                        arrowcolor=C["muted"],
                        bordercolor=C["dlg_border"],
                        lightcolor=C["dlg_input"],
                        darkcolor=C["dlg_input"])
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", C["dlg_input"])],
                  foreground=[("readonly", C["text"])])
        var = tk.StringVar(value=default)
        cb  = ttk.Combobox(parent, textvariable=var, values=values,
                           state="readonly", font=("Helvetica", 11),
                           style="Dark.TCombobox")
        cb.pack(fill="x", padx=16, pady=(0, 2))
        return var

    def _build(self, task, default_status):
        bg = C["dlg_bg"]

        # Título
        self._label(self, "Título")
        self.e_title = self._entry(self, task["title"] if task else "")

        # --- NUEVO CAMPO EXTRA: Descripción ---
        self._label(self, "Descripción")
        self.e_desc = self._entry(self, task.get("description", "") if task else "")

        # Proyecto
        self._label(self, "Proyecto")
        proj_names   = [p["name"] for p in self.projects]
        default_proj = next((p["name"] for p in self.projects
                             if task and p["id"] == task["project"]), proj_names[0])
        self.proj_var = self._combo(self, proj_names, default_proj)

        # Estado
        self._label(self, "Estado")
        status_labels = [c[1] for c in COLUMNS]
        status_ids    = [c[0] for c in COLUMNS]
        self._status_ids    = status_ids
        self._status_labels = status_labels
        if task:
            default_st = next((c[1] for c in COLUMNS if c[0] == task["status"]), status_labels[0])
        else:
            default_st = next((c[1] for c in COLUMNS if c[0] == default_status), status_labels[1])
        self.status_var = self._combo(self, status_labels, default_st)

        # Prioridad / Asignado
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")

        left = tk.Frame(row, bg=bg)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="Prioridad", bg=bg, fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", padx=16, pady=(8, 2))
        self.prio_var = tk.StringVar(value=task["priority"] if task else "Media")
        ttk.Combobox(left, textvariable=self.prio_var, values=["Alta", "Media", "Baja"],
                     state="readonly", font=("Helvetica", 11),
                     style="Dark.TCombobox").pack(fill="x", padx=16, pady=(0, 2))

        right = tk.Frame(row, bg=bg)
        right.pack(side="left", fill="x", expand=True)
        tk.Label(right, text="Asignado a", bg=bg, fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", padx=16, pady=(8, 2))
        self.assign_var = tk.StringVar(value=task["assign"] if task else MEMBERS[0])
        ttk.Combobox(right, textvariable=self.assign_var, values=MEMBERS,
                     state="readonly", font=("Helvetica", 11),
                     style="Dark.TCombobox").pack(fill="x", padx=16, pady=(0, 2))

        # Fecha
        self._label(self, "Fecha límite (AAAA-MM-DD)")
        self.e_due = self._entry(self, task["due"] if task else str(date.today()))

        self._label(self, "Fecha de creación")
        fecha_creacion = task.get("created", str(date.today())) if task else str(date.today())
        self.e_created = self._entry(self, fecha_creacion)
        self.e_created.config(state="disabled", disabledbackground=C["hover"], disabledforeground=C["text"])

        # Separador
        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(12, 0))

        # Botones
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if task:
            tk.Button(btn_row, text="Eliminar",
                      bg="#3A1A1A", fg="#E05555",
                      font=("Helvetica", 10), relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=self._delete).pack(side="left")

        tk.Button(btn_row, text="Cancelar",
                  bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_row, text="Guardar" if task else "Crear tarea",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._save).pack(side="right")

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")

    def _save(self):
        title = self.e_title.get().strip()
        if not title:
            messagebox.showwarning("Campo vacío", "El título no puede estar vacío.", parent=self)
            return
        try:
            datetime.strptime(self.e_due.get().strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fecha inválida", "Usa el formato AAAA-MM-DD.", parent=self)
            return
        proj_name  = self.proj_var.get()
        proj       = next(p for p in self.projects if p["name"] == proj_name)
        status_idx = self._status_labels.index(self.status_var.get())
        self.result = {
            "title":   title,
            "project": proj["id"],
            "description": self.e_desc.get(),
            "status":  self._status_ids[status_idx],
            "priority":self.prio_var.get(),
            "assign":  self.assign_var.get(),
            "created":     self.e_created.get().strip(),
            "due":     self.e_due.get().strip(),
            "deleted": False,
        }
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta tarea?", parent=self):
            self.result = {"deleted": True}
            self.destroy()


# ── Diálogo: Nuevo / Editar proyecto ─────────────────────────────────────────

class ProjectDialog(tk.Toplevel):
    COLORS = [
        "#7C6FE0", "#1D9E75", "#EF9F27", "#E05555", "#4A90D9",
        "#E8678A", "#2ECC71", "#F39C12", "#1ABC9C", "#9B59B6",
        "#E67E22", "#3498DB", "#E91E8C", "#00BCD4", "#8BC34A",
    ]

    def __init__(self, parent, project=None):
        super().__init__(parent)
        self.result  = None
        self.project = project

        self.title("Editar proyecto" if project else "Nuevo proyecto")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()

        self.selected_color = tk.StringVar(
            value=project["color"] if project else self.COLORS[0]
        )

        self._build(project)
        self.e_name.focus()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")

    def _build(self, project):
        bg = C["dlg_bg"]

        tk.Label(self, text="Nombre del proyecto", bg=bg, fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", padx=16, pady=(16, 2))

        self.e_name = tk.Entry(self, font=("Helvetica", 11),
                               bg=C["dlg_input"], fg=C["text"],
                               insertbackground=C["text"],
                               relief="flat", bd=0,
                               highlightthickness=1,
                               highlightbackground=C["dlg_border"],
                               highlightcolor=C["accent"])
        self.e_name.pack(fill="x", padx=16)
        if project:
            self.e_name.insert(0, project["name"])

        tk.Label(self, text="Color", bg=bg, fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", padx=16, pady=(12, 6))

        # Color swatches grid
        grid = tk.Frame(self, bg=bg)
        grid.pack(padx=16, pady=(0, 4))
        self._swatches = []
        for i, color in enumerate(self.COLORS):
            btn = tk.Label(grid, bg=color, width=3, height=1,
                           cursor="hand2", relief="flat", bd=2)
            btn.grid(row=i // 5, column=i % 5, padx=3, pady=3)
            btn.bind("<Button-1>", lambda e, c=color: self._pick_color(c))
            self._swatches.append((btn, color))

        self._update_swatches()

        # Preview
        prev_row = tk.Frame(self, bg=bg)
        prev_row.pack(padx=16, pady=(4, 0))
        tk.Label(prev_row, text="Vista previa:", bg=bg, fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left")
        self.preview_dot = tk.Label(prev_row, text="  ●  Nombre del proyecto",
                                    bg=bg, fg=self.selected_color.get(),
                                    font=("Helvetica", 10))
        self.preview_dot.pack(side="left", padx=6)
        self.e_name.bind("<KeyRelease>", self._update_preview)

        # Separator
        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(12, 0))

        # Buttons
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if project:
            tk.Button(btn_row, text="Eliminar proyecto",
                      bg="#3A1A1A", fg="#E05555",
                      font=("Helvetica", 10), relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=self._delete).pack(side="left")

        tk.Button(btn_row, text="Cancelar",
                  bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_row, text="Guardar" if project else "Crear proyecto",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._save).pack(side="right")

    def _pick_color(self, color):
        self.selected_color.set(color)
        self._update_swatches()
        self._update_preview()

    def _update_swatches(self):
        selected = self.selected_color.get()
        for btn, color in self._swatches:
            if color == selected:
                btn.config(relief="solid", bd=2,
                           highlightthickness=2,
                           highlightbackground="#FFFFFF")
            else:
                btn.config(relief="flat", bd=0,
                           highlightthickness=0)

    def _update_preview(self, event=None):
        name = self.e_name.get().strip() or "Nombre del proyecto"
        self.preview_dot.config(text=f"  ●  {name}",
                                fg=self.selected_color.get())

    def _save(self):
        name = self.e_name.get().strip()
        if not name:
            messagebox.showwarning("Campo vacío", "El nombre no puede estar vacío.", parent=self)
            return
        self.result = {"name": name, "color": self.selected_color.get(), "deleted": False}
        self.destroy()

    def _delete(self):
        self.result = {"deleted": True}
        self.destroy()

# ── Aplicación principal ─────────────────────────────────────────────────────

class ProjectManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Manager")
        self.geometry("1050x660")
        self.configure(bg=C["bg"])
        self.minsize(800, 500)

        self.projects, self.tasks, self.next_id = load_data()
        self.next_proj_id = max((int(p["id"][1:]) for p in self.projects if p["id"].startswith("p")), default=0) + 1
        self.filter_project = None

        self._build_ui()
        self.refresh()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=C["sidebar"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Main
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        # Stats bar
        self.stats_frame = tk.Frame(main, bg=C["panel"])
        self.stats_frame.pack(fill="x")
        tk.Frame(main, bg=C["border"], height=1).pack(fill="x")

        # Topbar
        topbar = tk.Frame(main, bg=C["panel"], pady=10)
        topbar.pack(fill="x")
        tk.Frame(main, bg=C["border"], height=1).pack(fill="x")

        self.lbl_title = tk.Label(topbar, text="Todas las tareas",
                                   bg=C["panel"], fg=C["text"],
                                   font=("Helvetica", 13, "bold"))
        self.lbl_title.pack(side="left", padx=16)

        tk.Button(topbar, text="+ Nueva tarea",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=self._new_task).pack(side="right", padx=16)

        # Content
        self.content_frame = tk.Frame(main, bg=C["bg"])
        self.content_frame.pack(fill="both", expand=True)

    def _build_sidebar(self):
        # Logo
        logo = tk.Frame(self.sidebar, bg=C["sidebar"])
        logo.pack(fill="x", padx=14, pady=(18, 10))
        tk.Label(logo, text="◈  Project Manager",
                 bg=C["sidebar"], fg=C["accent"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x")

        # Nav item: Reportes
        self._nav_item(self.sidebar, "📊", "Reportes", self._show_report)

        tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x", pady=8)

        # Header "PROYECTOS"
        ph = tk.Frame(self.sidebar, bg=C["sidebar"])
        ph.pack(fill="x", padx=6)
        tk.Label(ph, text="  PROYECTOS", bg=C["sidebar"], fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left")
        
        add_proj_btn = tk.Label(ph, text="+", bg=C["sidebar"], fg=C["accent"],
                                font=("Helvetica", 14, "bold"), cursor="hand2", padx=4)
        add_proj_btn.pack(side="right")
        add_proj_btn.bind("<Button-1>", lambda e: self._new_project())

        # Contenedor dinámico de proyectos
        self.proj_frame = tk.Frame(self.sidebar, bg=C["sidebar"])
        self.proj_frame.pack(fill="x")

        # Renderizar proyectos (Asegúrate de que self.projects sea tu lista)
        if hasattr(self, 'projects'):
            for p in self.projects:
                self._nav_item(
                    self.proj_frame, "●", p['name'],
                    cmd=lambda e, pid=p['id']: self._filter(pid),
                    edit_cmd=lambda e, pid=p['id']: self._edit_project(pid)  # ✅ aquí
                )

        # Todos (Separado de la lista dinámica)
        self._nav_item(self.sidebar, "◉", "Todos", lambda e: self._filter("all"))

    def _nav_item(self, parent, icon, label, cmd, edit_cmd=None):
        f = tk.Frame(parent, bg=C["sidebar"], cursor="hand2")
        f.pack(fill="x")

        lbl = tk.Label(f, text=f"  {icon}  {label}",
                       bg=C["sidebar"], fg=C["muted"],
                       font=("Helvetica", 10), anchor="w", pady=7,
                       cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)

        # ✅ Botón editar integrado directamente en _nav_item
        edit_lbl = None
        if edit_cmd:
            edit_lbl = tk.Label(f, text="✎", bg=C["sidebar"], fg=C["muted"],
                                font=("Helvetica", 10), cursor="hand2", padx=2)
            edit_lbl.pack(side="right", padx=(0, 2))
            edit_lbl.bind("<Button-1>", edit_cmd)

        # ✅ Freeze correcto de f, lbl y edit_lbl
        def on_enter(e, _f=f, _lbl=lbl, _edit=edit_lbl):
            _f.config(bg=C["hover"])
            _lbl.config(bg=C["hover"], fg=C["accent"])
            if _edit:
                _edit.config(bg=C["hover"], fg=C["accent"])

        def on_leave(e, _f=f, _lbl=lbl, _edit=edit_lbl):
            _f.config(bg=C["sidebar"])
            _lbl.config(bg=C["sidebar"], fg=C["muted"])
            if _edit:
                _edit.config(bg=C["sidebar"], fg=C["muted"])

        # ✅ Bind en los 3 widgets (frame, label, edit)
        widgets = [f, lbl] + ([edit_lbl] if edit_lbl else [])
        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        # Solo el frame y label activan el filtro, no el lápiz
        f.bind("<Button-1>", cmd)
        lbl.bind("<Button-1>", cmd)

    def _rebuild_project_list(self):
        for w in self.proj_frame.winfo_children():
            w.destroy()
        for p in self.projects:
            pid   = p["id"]
            count = len([t for t in self.tasks if t["project"] == pid])

            f = tk.Frame(self.proj_frame, bg=C["sidebar"], cursor="hand2")
            f.pack(fill="x")
            row = tk.Frame(f, bg=C["sidebar"])
            row.pack(fill="x", padx=10, pady=3)

            dot = tk.Label(row, text="●", bg=C["sidebar"], fg=p["color"],
                           font=("Helvetica", 10))
            dot.pack(side="left")

            name_lbl = tk.Label(row, text=p["name"], bg=C["sidebar"], fg=C["text"],
                                font=("Helvetica", 10))
            name_lbl.pack(side="left", padx=4)

            cnt_lbl = tk.Label(row, text=str(count), bg=C["sidebar"], fg=C["muted"],
                               font=("Helvetica", 9))
            cnt_lbl.pack(side="right")

            edit_lbl = tk.Label(row, text="✎", bg=C["sidebar"], fg=C["muted"],
                                font=("Helvetica", 10), cursor="hand2", padx=2)
            edit_lbl.pack(side="right", padx=(0, 2))
            edit_lbl.bind("<Button-1>", lambda e, pid=pid: self._edit_project(pid))

            # ✅ Freeze de TODOS los widgets en on_enter/on_leave
            all_widgets = [f, row, dot, name_lbl, cnt_lbl, edit_lbl]

            def on_enter(e, _ws=all_widgets, _edit=edit_lbl):
                for w in _ws:
                    w.config(bg=C["hover"])
                _edit.config(fg=C["text"])

            def on_leave(e, _ws=all_widgets, _edit=edit_lbl):
                for w in _ws:
                    w.config(bg=C["sidebar"])
                _edit.config(fg=C["muted"])

            def on_click(e, _pid=pid, _name=p["name"]):
                self._filter(_pid, _name)

            # ✅ Bind en todos los widgets excepto edit_lbl (tiene su propio click)
            for w in [f, row, dot, name_lbl, cnt_lbl]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)

            # edit_lbl también necesita hover pero NO el click de filtro
            edit_lbl.bind("<Enter>", on_enter)
            edit_lbl.bind("<Leave>", on_leave)
    # ── Acciones ─────────────────────────────────────────────────────────────

    def _new_project(self):
        dlg = ProjectDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            pid = f"p{self.next_proj_id}"
            self.next_proj_id += 1
            self.projects.append({"id": pid, "name": dlg.result["name"], "color": dlg.result["color"]})
            save_data(self.projects, self.tasks, self.next_id)
            self.refresh()

    def _edit_project(self, pid):
        proj = next((p for p in self.projects if p["id"] == pid), None)
        if not proj:
            return
        dlg = ProjectDialog(self, project=proj)
        self.wait_window(dlg)
        if dlg.result:
            if dlg.result.get("deleted"):
                # Reassign tasks to no project (remove or keep orphaned)
                if not messagebox.askyesno("Eliminar proyecto",
                    f"¿Eliminar '{proj['name']}'? Las tareas asociadas quedarán sin proyecto.",
                    parent=self):
                    return
                self.projects = [p for p in self.projects if p["id"] != pid]
                for t in self.tasks:
                    if t["project"] == pid:
                        t["project"] = self.projects[0]["id"] if self.projects else ""
                if self.filter_project == pid:
                    self.filter_project = None
                    self.lbl_title.config(text="Todas las tareas")
            else:
                proj["name"]  = dlg.result["name"]
                proj["color"] = dlg.result["color"]
            save_data(self.projects, self.tasks, self.next_id)
            self.refresh()

    def _filter(self, pid, name="Todas las tareas"):
        self.filter_project = None if pid == "all" else pid
        self.lbl_title.config(text="Todas las tareas" if pid == "all" else name)
        self.refresh()

    def _new_task(self):
        dlg = TaskDialog(self, self.projects)
        self.wait_window(dlg)
        if dlg.result and not dlg.result.get("deleted"):
            dlg.result["id"] = self.next_id
            self.next_id += 1
            self.tasks.append(dlg.result)
            save_data(self.projects, self.tasks, self.next_id)
            self.refresh()

    def _edit_task(self, task_id):
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        dlg = TaskDialog(self, self.projects, task=task)
        self.wait_window(dlg)
        if dlg.result:
            if dlg.result.get("deleted"):
                self.tasks = [t for t in self.tasks if t["id"] != task_id]
            else:
                dlg.result["id"] = task_id
                idx = next(i for i, t in enumerate(self.tasks) if t["id"] == task_id)
                self.tasks[idx] = dlg.result
            save_data(self.projects, self.tasks, self.next_id)
            self.refresh()

    def _show_report(self):
        total = len(self.tasks)
        done  = len([t for t in self.tasks if t["status"] == "done"])
        alta  = len([t for t in self.tasks if t["priority"] == "Alta" and t["status"] != "done"])
        lines = [
            f"Total de tareas:             {total}",
            f"Completadas:                 {done}  ({int(done/total*100) if total else 0}%)",
            f"Alta prioridad (pendientes): {alta}",
            "",
            "Por proyecto:",
        ]
        for p in self.projects:
            pt = [t for t in self.tasks if t["project"] == p["id"]]
            pd = [t for t in pt if t["status"] == "done"]
            lines.append(f"  {p['name']}: {len(pd)}/{len(pt)} completadas")
        messagebox.showinfo("Reporte", "\n".join(lines))

    # ── Render ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._rebuild_project_list()
        self._render_stats()
        for w in self.content_frame.winfo_children():
            w.destroy()
        visible = (self.tasks if not self.filter_project
                   else [t for t in self.tasks if t["project"] == self.filter_project])
        self._render_list(visible)

    def _render_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        total    = len(self.tasks)
        done     = len([t for t in self.tasks if t["status"] == "done"])
        progress = len([t for t in self.tasks if t["status"] == "progress"])
        high     = len([t for t in self.tasks if t["priority"] == "Alta" and t["status"] != "done"])
        for label, val, color in [
            ("Total",        total,    C["text"]),
            ("Completadas",  done,     "#2ECC71"),
            ("En progreso",  progress, "#E6A817"),
            ("Alta prioridad", high,   "#E05555"),
        ]:
            f = tk.Frame(self.stats_frame, bg=C["panel"])
            f.pack(side="left", padx=14, pady=10)
            tk.Label(f, text=str(val), bg=C["panel"], fg=color,
                     font=("Helvetica", 20, "bold")).pack()
            tk.Label(f, text=label, bg=C["panel"], fg=C["muted"],
                     font=("Helvetica", 9)).pack()
        # separador vertical entre stats
        tk.Frame(self.stats_frame, bg=C["border"], width=1).pack(side="left", fill="y", pady=6)

    def _render_list(self, tasks):
        # Configurar estilo Treeview oscuro
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                        background=C["bg"],
                        foreground=C["text"],
                        fieldbackground=C["bg"],
                        bordercolor=C["border"],
                        rowheight=36,
                        font=("Helvetica", 10))
        style.configure("Dark.Treeview.Heading",
                        background=C["panel"],
                        foreground=C["muted"],
                        bordercolor=C["border"],
                        relief="flat",
                        font=("Helvetica", 9, "bold"))
        style.map("Dark.Treeview",
                  background=[("selected", C["accent_dk"])],
                  foreground=[("selected", "#FFFFFF")])

        frame = tk.Frame(self.content_frame, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        cols = ("Tarea", "Proyecto", "Estado", "Prioridad", "Asignado", "Fecha")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview", selectmode="browse")

        widths = [340, 110, 115, 85, 105, 95]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w", minwidth=60)

        # Filas alternas
        tree.tag_configure("odd",  background=C["bg"])
        tree.tag_configure("even", background=C["row_alt"])

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        self._iid_map = {}
        tag_bg = {"p1": C["tag_p1_bg"], "p2": C["tag_p2_bg"], "p3": C["tag_p3_bg"]}

        for i, t in enumerate(tasks):
            proj = next((p for p in self.projects if p["id"] == t["project"]), {"name": "?"})
            col  = next((c for c in COLUMNS if c[0] == t["status"]),  ("?", "?", "#888"))
            row_tag = "even" if i % 2 == 0 else "odd"
            iid = tree.insert("", "end", tags=(row_tag,), values=(
                t["title"],
                proj["name"],
                col[1],
                t["priority"],
                t["assign"],
                t["due"],
            ))
            self._iid_map[iid] = t["id"]

        tree.bind("<Double-1>", lambda e: self._list_edit(tree))

        # Hint
        hint = tk.Label(frame,
                        text="Doble clic en una fila para editar · Filtrar por proyecto en la barra lateral",
                        bg=C["bg"], fg=C["muted"], font=("Helvetica", 9))
        hint.pack(pady=6)

    def _list_edit(self, tree):
        sel = tree.selection()
        if not sel:
            return
        tid = self._iid_map.get(sel[0])
        if tid:
            self._edit_task(tid)

# ── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ProjectManagerApp()
    app.mainloop()

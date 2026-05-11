"""
ui/sidebar.py — Barra lateral con navegación por proyectos.
Solo responsabilidad: mostrar proyectos y disparar callbacks.
"""

import tkinter as tk
from config import C


class Sidebar(tk.Frame):
    """
    Callbacks esperados:
      on_filter(project_id | "all")
      on_new_project()
      on_edit_project(project_id)
      on_report()
    """

    def __init__(self, parent, on_filter, on_new_project, on_edit_project, on_report):
        super().__init__(parent, bg=C["sidebar"], width=200)
        self.pack_propagate(False)

        self.on_filter        = on_filter
        self.on_new_project   = on_new_project
        self.on_edit_project  = on_edit_project
        self.on_report        = on_report

        self._build_static()
        self.proj_frame = tk.Frame(self, bg=C["sidebar"])
        self.proj_frame.pack(fill="x")
        self._nav_item(self, "◉", "Todos", lambda e: self.on_filter("all"))

    # ── Estructura fija ───────────────────────────────────────────────────────

    def _build_static(self):
        logo = tk.Frame(self, bg=C["sidebar"])
        logo.pack(fill="x", padx=14, pady=(18, 10))
        tk.Label(logo, text="◈  Project Manager",
                 bg=C["sidebar"], fg=C["accent"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        self._nav_item(self, "📊", "Reportes", lambda e: self.on_report())
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", pady=8)

        ph = tk.Frame(self, bg=C["sidebar"])
        ph.pack(fill="x", padx=6)
        tk.Label(ph, text="  PROYECTOS", bg=C["sidebar"], fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left")
        add = tk.Label(ph, text="+", bg=C["sidebar"], fg=C["accent"],
                       font=("Helvetica", 14, "bold"), cursor="hand2", padx=4)
        add.pack(side="right")
        add.bind("<Button-1>", lambda e: self.on_new_project())

    # ── Lista dinámica de proyectos ───────────────────────────────────────────

    def rebuild(self, projects: list, tasks: list):
        for w in self.proj_frame.winfo_children():
            w.destroy()

        for p in projects:
            pid   = p.id
            count = sum(1 for t in tasks if t.project_id == pid)
            self._project_row(pid, p.name, p.color, count)

    def _project_row(self, pid: str, name: str, color: str, count: int):
        f = tk.Frame(self.proj_frame, bg=C["sidebar"], cursor="hand2")
        f.pack(fill="x")
        row = tk.Frame(f, bg=C["sidebar"])
        row.pack(fill="x", padx=10, pady=3)

        dot      = tk.Label(row, text="●",      bg=C["sidebar"], fg=color,     font=("Helvetica", 10))
        name_lbl = tk.Label(row, text=name,     bg=C["sidebar"], fg=C["text"], font=("Helvetica", 10))
        cnt_lbl  = tk.Label(row, text=str(count), bg=C["sidebar"], fg=C["muted"], font=("Helvetica", 9))
        edit_lbl = tk.Label(row, text="✎",      bg=C["sidebar"], fg=C["muted"], font=("Helvetica", 10), cursor="hand2", padx=2)

        dot.pack(side="left")
        name_lbl.pack(side="left", padx=4)
        cnt_lbl.pack(side="right")
        edit_lbl.pack(side="right", padx=(0, 2))

        edit_lbl.bind("<Button-1>", lambda e, _pid=pid: self.on_edit_project(_pid))

        all_widgets = [f, row, dot, name_lbl, cnt_lbl, edit_lbl]

        def on_enter(e, _ws=all_widgets, _edit=edit_lbl):
            for w in _ws:
                w.config(bg=C["hover"])
            _edit.config(fg=C["text"])

        def on_leave(e, _ws=all_widgets, _edit=edit_lbl):
            for w in _ws:
                w.config(bg=C["sidebar"])
            _edit.config(fg=C["muted"])

        for w in [f, row, dot, name_lbl, cnt_lbl]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e, _pid=pid, _name=name: self.on_filter(_pid, _name))

        edit_lbl.bind("<Enter>", on_enter)
        edit_lbl.bind("<Leave>", on_leave)

    def _nav_item(self, parent, icon, label, cmd):
        f   = tk.Frame(parent, bg=C["sidebar"], cursor="hand2")
        f.pack(fill="x")
        lbl = tk.Label(f, text=f"  {icon}  {label}",
                       bg=C["sidebar"], fg=C["muted"],
                       font=("Helvetica", 10), anchor="w", pady=7, cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)

        def on_enter(e):
            f.config(bg=C["hover"])
            lbl.config(bg=C["hover"], fg=C["accent"])

        def on_leave(e):
            f.config(bg=C["sidebar"])
            lbl.config(bg=C["sidebar"], fg=C["muted"])

        for w in [f, lbl]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", cmd)

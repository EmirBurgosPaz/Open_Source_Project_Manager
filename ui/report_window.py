"""
ui/report_window.py — Ventana de reportes para Project Manager.
Muestra estadísticas, gráficas y tabla detallada de tareas.
Permite exportar a Excel.

Dependencias externas:
    pip install matplotlib openpyxl
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from openpyxl.styles import PatternFill, Font, Alignment

from config import C, COLUMNS_STATUS, STATUS_COLORS, PRIORITY_COLORS, STATUS_FILL, PRIORITY_FILL, KEYBOARD_KEYS
from utils.ui_helpers import center_window

import openpyxl

# ── Helpers ───────────────────────────────────────────────────────────────────

STATUS_LABEL = {k: v for k, v in COLUMNS_STATUS}


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


# ── Ventana principal ─────────────────────────────────────────────────────────

class ReportWindow(tk.Toplevel):
    """Ventana de reportes. Se abre desde main._show_report()."""

    def __init__(self, master, task_service):
        super().__init__(master)
        self.withdraw()

        self.task_service = task_service
        self.title("Reportes")
        self.configure(bg=C["bg"])

        

        # Estado de filtros
        self._filter_project = tk.StringVar(value="all")
        self._filter_status  = tk.StringVar(value="all")
        self._filter_priority = tk.StringVar(value="all")
        self._date_from = tk.StringVar(value="")
        self._date_to   = tk.StringVar(value="")

        self._build_ui()
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)

        center_window(self, master)

        self._refresh()

        self.attributes('-alpha', 1.0)
        self.deiconify()
        # Tamaño y posición centrad

        self.after(30, lambda: self.attributes('-alpha', 1.0))

        self.focus()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Encabezado ──
        header = tk.Frame(self, bg=C["sidebar"], pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Reportes", bg=C["sidebar"], fg=C["text"],
                 font=("Helvetica", 15, "bold")).pack(side="left", padx=20)
        tk.Button(header, text="Cerrar", bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 9), relief="flat", bd=0,
                  padx=10, pady=4, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=16)
        tk.Button(header, text="Exportar Excel", bg=C["accent"], fg="white",
                      font=("Helvetica", 9, "bold"), relief="flat", bd=0,
                      padx=12, pady=4, cursor="hand2",
                      command=self._export_excel).pack(side="right", padx=6)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Barra de filtros ──
        self._build_filter_bar()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Tarjetas de resumen ──
        self.stats_frame = tk.Frame(self, bg=C["bg"])
        self.stats_frame.pack(fill="x", padx=20, pady=14)

        # ── Contenido principal (gráfica + tabla) ──
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # Gráfica izquierda
        self.chart_frame = tk.Frame(body, bg=C["panel"], width=420)
        self.chart_frame.pack(side="left", fill="both", padx=(16, 8), pady=(0, 16))
        self.chart_frame.pack_propagate(False)

        # Tabla derecha
        table_outer = tk.Frame(body, bg=C["bg"])
        table_outer.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=(0, 16))
        self._build_table(table_outer)

    def _build_filter_bar(self):
        bar = tk.Frame(self, bg=C["panel"], pady=8)
        bar.pack(fill="x")

        def lbl(parent, text):
            tk.Label(parent, text=text, bg=C["panel"], fg=C["muted"],
                     font=("Helvetica", 8)).pack(side="left", padx=(10, 2))

        def combo(parent, var, values, width=14):
            cb = ttk.Combobox(parent, textvariable=var, values=values,
                              state="readonly", width=width)
            cb.pack(side="left", padx=(0, 6))
            cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())
            return cb

        # Estilo para comboboxes
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                fieldbackground=C["panel"],
                background=C["panel"],
                foreground=C["text"],
                arrowcolor=C["muted"],
                bordercolor=C["border"],
                selectbackground=C["dlg_input"],
                selectforeground=C["text"],          # ← antes era C["panel"] (invisible)
                insertcolor=C["text"],
                padding=(6, 4))

        style.map("TCombobox",
          fieldbackground=[("readonly", C["dlg_input"]),
                           ("active",   C["panel"]),    # ← nuevo
                           ("focus",    C["panel"])],   # ← antes era accent (muy oscuro)
          background=[("active",   C["hover"]),         # ← fondo del botón flecha
                      ("pressed",  C["accent_dk"])],
          foreground=[("readonly", C["text"]),
                      ("active",   C["text"]),
                      ("disabled", C["disabled_fg"])],
          selectbackground=[("readonly", C["dlg_input"]),
                            ("focus",    C["dlg_input"])],
          selectforeground=[("readonly", C["text"]),
                            ("focus",    C["text"])],
          bordercolor=[("focus",   C["accent"]),
                       ("!focus",  C["border"])])       # ← antes era accent siempre

        # Proyecto
        projects = self.task_service.projects
        proj_vals = [("all", "Todos los proyectos")] + [(p.id, p.name) for p in projects]
        self._proj_ids = [v[0] for v in proj_vals]
        self._proj_labels = [v[1] for v in proj_vals]
        self._proj_var_label = tk.StringVar(value="Todos los proyectos")

        lbl(bar, "Proyecto:")
        proj_cb = ttk.Combobox(bar, textvariable=self._proj_var_label,
                               values=self._proj_labels, state="readonly", width=18)
        proj_cb.pack(side="left", padx=(0, 6))
        proj_cb.bind("<<ComboboxSelected>>", self._on_proj_change)

        # Estado
        status_vals = ["Todos"] + [v for _, v in COLUMNS_STATUS]
        lbl(bar, "Estado:")
        self._status_label_var = tk.StringVar(value="Todos")
        s_cb = ttk.Combobox(bar, textvariable=self._status_label_var,
                             values=status_vals, state="readonly", width=14)
        s_cb.pack(side="left", padx=(0, 6))
        s_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Prioridad
        lbl(bar, "Prioridad:")
        self._priority_var = tk.StringVar(value="Todas")
        p_cb = ttk.Combobox(bar, textvariable=self._priority_var,
                             values=["Todas", "Alta", "Media", "Baja"],
                             state="readonly", width=10)
        p_cb.pack(side="left", padx=(0, 6))
        p_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Rango de fechas
        lbl(bar, "Desde:")
        e_from = tk.Entry(bar, textvariable=self._date_from, width=11,
                          bg=C["dlg_input"], fg=C["text"], insertbackground=C["text"],
                          relief="flat", font=("Helvetica", 9))
        e_from.pack(side="left", padx=(0, 4))
        e_from.insert(0, "AAAA-MM-DD")
        e_from.bind("<FocusIn>",  lambda e: e_from.delete(0, "end") if e_from.get() == "AAAA-MM-DD" else None)
        e_from.bind("<FocusOut>", lambda e: (e_from.insert(0, "AAAA-MM-DD") if not e_from.get() else None))
        e_from.bind("<Return>", lambda e: self._refresh())

        lbl(bar, "Hasta:")
        e_to = tk.Entry(bar, textvariable=self._date_to, width=11,
                        bg=C["dlg_input"], fg=C["text"], insertbackground=C["text"],
                        relief="flat", font=("Helvetica", 9))
        e_to.pack(side="left", padx=(0, 4))
        e_to.insert(0, "AAAA-MM-DD")
        e_to.bind("<FocusIn>",  lambda e: e_to.delete(0, "end") if e_to.get() == "AAAA-MM-DD" else None)
        e_to.bind("<FocusOut>", lambda e: (e_to.insert(0, "AAAA-MM-DD") if not e_to.get() else None))
        e_to.bind("<Return>", lambda e: self._refresh())

        tk.Button(bar, text="Aplicar", bg=C["accent"], fg="white",
                  font=("Helvetica", 8, "bold"), relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._refresh).pack(side="left", padx=6)

        tk.Button(bar, text="Limpiar", bg=C["hover"], fg=C["muted"],
                  font=("Helvetica", 8), relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._clear_filters).pack(side="left")

    def _build_table(self, parent):
        # Título
        tk.Label(parent, text="Detalle de tareas", bg=C["bg"], fg=C["text"],
                 font=("Helvetica", 10, "bold")).pack(anchor="w", padx=4, pady=(0, 6))

        # Frame con scroll
        wrapper = tk.Frame(parent, bg=C["border"], bd=1)
        wrapper.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Report.Treeview",
                         background=C["panel"],
                         foreground=C["text"],
                         fieldbackground=C["panel"],
                         borderwidth=0,
                         rowheight=28,
                         font=("Helvetica", 9))
        style.configure("Report.Treeview.Heading",
                         background=C["sidebar"],
                         foreground=C["muted"],
                         borderwidth=0,
                         font=("Helvetica", 8, "bold"))
        style.map("Report.Treeview",
                  background=[("selected", C["accent_dk"])],
                  foreground=[("selected", "white")])

        cols = ("title", "project", "status", "priority", "assign", "due", "client")
        self.tree = ttk.Treeview(wrapper, columns=cols, show="headings",
                                  style="Report.Treeview")

        headers = {
            "title":    ("Tarea",        260),
            "project":  ("Proyecto",     110),
            "status":   ("Estado",        95),
            "priority": ("Prioridad",     80),
            "assign":   ("Asignado",     100),
            "due":      ("Vencimiento",   95),
            "client":   ("Cliente",      100),
        }
        for col, (heading, width) in headers.items():
            self.tree.heading(col, text=heading,
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=width, minwidth=60, anchor="w")

        # Tags de color por estado
        for status_id, color in STATUS_COLORS.items():
            self.tree.tag_configure(f"s_{status_id}", foreground=color)
        self.tree.tag_configure("row_alt", background=C["row_alt"])

        vsb = ttk.Scrollbar(wrapper, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(wrapper, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        self._sort_col = None
        self._sort_asc = True

    # ── Lógica de filtrado ────────────────────────────────────────────────────

    def _on_proj_change(self, event=None):
        label = self._proj_var_label.get()
        idx = self._proj_labels.index(label)
        self._filter_project.set(self._proj_ids[idx])
        self._refresh()

    def _clear_filters(self):
        self._proj_var_label.set("Todos los proyectos")
        self._filter_project.set("all")
        self._status_label_var.set("Todos")
        self._priority_var.set("Todas")
        self._date_from.set("AAAA-MM-DD")
        self._date_to.set("AAAA-MM-DD")
        self._refresh()

    def _get_filtered_tasks(self):
        tasks = self.task_service.get_all()

        # Proyecto
        proj = self._filter_project.get()
        if proj and proj != "all":
            tasks = [t for t in tasks if t.project_id == proj]

        # Estado
        status_lbl = self._status_label_var.get()
        if status_lbl and status_lbl != "Todos":
            status_id = next((k for k, v in COLUMNS_STATUS if v == status_lbl), None)
            if status_id:
                tasks = [t for t in tasks if t.status == status_id]

        # Prioridad
        prio = self._priority_var.get()
        if prio and prio != "Todas":
            tasks = [t for t in tasks if t.priority == prio]

        # Fechas
        def parse_date(s):
            try:
                return datetime.strptime(s.strip(), "%Y-%m-%d")
            except Exception:
                return None

        d_from = parse_date(self._date_from.get())
        d_to   = parse_date(self._date_to.get())
        if d_from or d_to:
            result = []
            for t in tasks:
                td = parse_date(t.due)
                if not td:
                    continue
                if d_from and td < d_from:
                    continue
                if d_to and td > d_to:
                    continue
                result.append(t)
            tasks = result

        return tasks

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        tasks = self._get_filtered_tasks()
        self._render_chart(tasks)
        self._render_table(tasks)


    def _render_chart(self, tasks):
        # Ocultar el frame durante la construcción
        self.chart_frame.pack_forget()

        for w in self.chart_frame.winfo_children():
            w.destroy()

        # Notebook interno para 2 gráficas
        nb_style = ttk.Style()
        nb_style.configure("Chart.TNotebook", background=C["panel"], borderwidth=0)
        nb_style.configure("Chart.TNotebook.Tab",
                           background=C["hover"], foreground=C["muted"],
                           padding=[8, 4], font=("Helvetica", 8))
        nb_style.map("Chart.TNotebook.Tab",
                     background=[("selected", C["accent"])],
                     foreground=[("selected", "white")])

        nb = ttk.Notebook(self.chart_frame, style="Chart.TNotebook")
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # — Gráfica 1: tareas por estado —
        f1 = tk.Frame(nb, bg=C["panel"])
        nb.add(f1, text="Por estado")
        self._chart_by_status(f1, tasks)

        # — Gráfica 2: tareas por proyecto —
        f2 = tk.Frame(nb, bg=C["panel"])
        nb.add(f2, text="Por proyecto")
        self._chart_by_project(f2, tasks)

        # — Gráfica 3: por prioridad —
        f3 = tk.Frame(nb, bg=C["panel"])
        nb.add(f3, text="Por prioridad")
        self._chart_by_priority(f3, tasks)

        # Forzar actualización antes de mostrar
        self.chart_frame.update_idletasks()
        self.chart_frame.pack(fill="both", expand=True)  # Restaurar el pack según tu layout

    def _make_figure(self):
        bg = C["panel"]
        # Crear figura completamente configurada desde el inicio
        fig = Figure(figsize=(4, 3.2), dpi=90, facecolor=bg, edgecolor=bg)
        ax = fig.add_subplot(111, facecolor=bg)

        # Configurar todo antes de que se renderice
        ax.tick_params(colors=C["muted"], labelsize=7)
        ax.xaxis.label.set_color(C["muted"])
        ax.yaxis.label.set_color(C["muted"])

        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])

        return fig, ax

    def _embed_chart(self, parent, fig):
        # Crear canvas con fondo transparente
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().configure(bg=C["panel"], highlightthickness=0)

        # Renderizar antes de mostrar
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        return canvas  # Por si necesitas referencia

    def _chart_by_status(self, parent, tasks):
        counts = {}
        for _, label in COLUMNS_STATUS:
            counts[label] = 0
        for t in tasks:
            label = STATUS_LABEL.get(t.status, t.status)
            counts[label] = counts.get(label, 0) + 1

        labels = [k for k, v in counts.items() if v > 0]
        values = [counts[k] for k in labels]
        colors = [_hex_to_rgb(STATUS_COLORS.get(
            next((k for k, v in COLUMNS_STATUS if v == lb), "todo"), C["accent"]))
            for lb in labels]

        if not values:
            tk.Label(parent, text="Sin datos", bg=C["panel"], fg=C["muted"]).pack(expand=True)
            return

        fig, ax = self._make_figure()
        bars = ax.barh(labels, values, color=colors, height=0.5)
        ax.bar_label(bars, fmt="%d", color=C["text"], fontsize=7, padding=3)
        ax.set_xlabel("Tareas", color=C["muted"], fontsize=7)
        ax.set_title("Por estado", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    def _chart_by_project(self, parent, tasks):
        proj_map = {p.id: p.name for p in self.task_service.projects}
        counts = {}
        colors_map = {p.id: p.color for p in self.task_service.projects}
        for t in tasks:
            name = proj_map.get(t.project_id, "Sin proyecto")
            counts[name] = counts.get(name, 0) + 1
        color_list = [_hex_to_rgb(colors_map.get(
            next((p.id for p in self.task_service.projects if p.name == name), ""), C["accent"]))
            for name in counts]

        if not counts:
            tk.Label(parent, text="Sin datos", bg=C["panel"], fg=C["muted"]).pack(expand=True)
            return

        fig, ax = self._make_figure()
        wedges, texts, autotexts = ax.pie(
            list(counts.values()),
            labels=list(counts.keys()),
            colors=color_list,
            autopct="%1.0f%%",
            startangle=90,
            textprops={"color": C["text"], "fontsize": 7},
        )
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(C["bg"])
        ax.set_title("Por proyecto", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    def _chart_by_priority(self, parent, tasks):
        counts = {"Alta": 0, "Media": 0, "Baja": 0}
        for t in tasks:
            if t.priority in counts:
                counts[t.priority] += 1

        labels = [k for k, v in counts.items() if v > 0]
        values = [counts[k] for k in labels]
        colors = [_hex_to_rgb(PRIORITY_COLORS.get(k, C["accent"])) for k in labels]

        if not values:
            tk.Label(parent, text="Sin datos", bg=C["panel"], fg=C["muted"]).pack(expand=True)
            return

        fig, ax = self._make_figure()
        bars = ax.bar(labels, values, color=colors, width=0.4)
        ax.bar_label(bars, fmt="%d", color=C["text"], fontsize=7, padding=3)
        ax.set_ylabel("Tareas", color=C["muted"], fontsize=7)
        ax.set_title("Por prioridad", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    def _render_table(self, tasks):
        self.tree.delete(*self.tree.get_children())
        proj_map = {p.id: p.name for p in self.task_service.projects}

        for i, t in enumerate(tasks):
            tag = f"s_{t.status}"
            alt = "row_alt" if i % 2 else ""
            self.tree.insert("", "end", iid=str(t.id), tags=(tag, alt),
                             values=(
                                 t.title,
                                 proj_map.get(t.project_id, "—"),
                                 STATUS_LABEL.get(t.status, t.status),
                                 t.priority,
                                 t.assign or "—",
                                 t.due or "—",
                                 getattr(t, "client", "") or "—",
                             ))

    # ── Ordenar tabla ─────────────────────────────────────────────────────────

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=not self._sort_asc)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)

    # ── Exportar Excel ────────────────────────────────────────────────────────

    def _export_excel(self):

        tasks = self._get_filtered_tasks()
        proj_map = {p.id: p.name for p in self.task_service.projects}

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        )
        if not path:
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Tareas"

        # Encabezados
        headers = ["ID", "Tarea", "Proyecto", "Estado", "Prioridad",
                   "Asignado", "Vencimiento", "Cliente", "Descripción"]
        header_fill = PatternFill("solid", fgColor="7C6FE0")
        header_font = Font(bold=True, color="FFFFFF", size=10)

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        ws.row_dimensions[1].height = 22

        # Colores por estado para Excel


        for row_idx, t in enumerate(tasks, 2):
            row_data = [
                t.id,
                t.title,
                proj_map.get(t.project_id, "—"),
                STATUS_LABEL.get(t.status, t.status),
                t.priority,
                t.assign or "—",
                t.due or "—",
                getattr(t, "client", "") or "—",
                getattr(t, "requester", "") or "",
            ]
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.alignment = Alignment(vertical="center", wrap_text=False)
                if col_idx == 4:  # Estado
                    fill_color = STATUS_FILL.get(t.status, "7A7A8A")
                    cell.fill = PatternFill("solid", fgColor=fill_color)
                    cell.font = Font(color="FFFFFF", size=9)
                elif col_idx == 5:  # Prioridad
                    fill_color = PRIORITY_FILL.get(t.priority, "7A7A8A")
                    cell.fill = PatternFill("solid", fgColor=fill_color)
                    cell.font = Font(color="FFFFFF", size=9)
                else:
                    bg = "1F1F26" if row_idx % 2 == 0 else "22222A"
                    cell.fill = PatternFill("solid", fgColor=bg)
                    cell.font = Font(color="E8E8EC", size=9)

            ws.row_dimensions[row_idx].height = 18

        # Anchos de columna
        col_widths = [6, 40, 18, 14, 12, 16, 14, 16, 40]
        for i, width in enumerate(col_widths, 1):
            ws.column_dimensions[
                openpyxl.utils.get_column_letter(i)
            ].width = width

        # Hoja 2: resumen
        ws2 = wb.create_sheet("Resumen")
        total = len(tasks)
        done  = sum(1 for t in tasks if t.status == "done")
        pct   = int(done / total * 100) if total else 0
        summary = [
            ("Generado el",        datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("Total de tareas",    total),
            ("Completadas",        f"{done} ({pct}%)"),
            ("En progreso",        sum(1 for t in tasks if t.status == "progress")),
            ("Alta prioridad",     sum(1 for t in tasks if t.priority == "Alta" and t.status != "done")),
        ]
        for r, (label, val) in enumerate(summary, 1):
            ws2.cell(row=r, column=1, value=label).font = Font(bold=True, color="7C6FE0")
            ws2.cell(row=r, column=2, value=val)

        wb.save(path)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _on_close(self,event = None):
        self.destroy()
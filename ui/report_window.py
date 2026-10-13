"""
ui/report_window.py — Ventana de reportes para Project Manager.
Muestra KPIs, gráficas, tiempo de atención por prioridad y tabla detallada.
Permite exportar a Excel.

Dependencias externas:
    pip install matplotlib openpyxl
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from statistics import median
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

from config import (C, COLUMNS_STATUS, STATUS_COLORS, PRIORITY_COLORS,
                    STATUS_FILL, PRIORITY_FILL, KEYBOARD_KEYS, FIELDS, 
                    STATUS_LABEL, PRIORITIES,HOURS_FIELDS, PLACEHOLDER, CREATED_FIELDS, CLOSED_FIELDS, BASIS_RESOLVED, 
                    BASIS_OPEN, USE_ESTIMATED_HOURS, HOURS_PER_DAY, MINIMUN_DAY)
from utils.ui_helpers import center_window, add_hover, lighten





def estimate_hours(days):
    return days * HOURS_PER_DAY + HOURS_PER_DAY


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def _parse_date(s):
    """Convierte 'AAAA-MM-DD' (o ISO con hora) a datetime. None si no es válida."""
    if not s or not isinstance(s, (str, datetime, date)):
        return None
    if isinstance(s, datetime):
        return s
    if isinstance(s, date):
        return datetime(s.year, s.month, s.day)
    try:
        return datetime.strptime(s.strip()[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _first_attr(obj, names):
    for n in names:
        v = getattr(obj, n, None)
        if v not in (None, ""):
            return v
    return None


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def attention_metrics(tasks, basis):
    """
    Tiempo de atención por prioridad.
    Resueltas: días = cierre - creación (solo tareas 'done' con ambas fechas).
    Abiertas : días = hoy - creación (backlog, tareas no 'done').
    Devuelve {prioridad: dict|None} y una lista con el total.
    """
    today = datetime.now()
    buckets = {p: {"days": [], "hours": []} for p in PRIORITIES}

    for t in tasks:
        if t.priority not in buckets:
            continue
        created = _parse_date(_first_attr(t, CREATED_FIELDS))
        if not created:
            continue
        if basis == BASIS_RESOLVED:
            if t.status != "done":
                continue
            closed = _parse_date(_first_attr(t, CLOSED_FIELDS))
            if not closed:
                continue
            days = max((closed - created).days, 0)
        else:
            if t.status == "done":
                continue
            days = max((today - created).days, 0)

        buckets[t.priority]["days"].append(days)
        if USE_ESTIMATED_HOURS:
            h = estimate_hours(days)
        else:
            h = _to_float(_first_attr(t, HOURS_FIELDS))
        if h is not None:
            buckets[t.priority]["hours"].append(h)

    def summarize(days, hours):
        if not days:
            return None
        n = len(days)
        return {
            "n": n,
            "avg": sum(days) / n + MINIMUN_DAY,
            "median": median(days) + MINIMUN_DAY,
            "pct01": sum(1 for d in days if d <= 1) / n * 100,
            "max": max(days) + MINIMUN_DAY,
            "hours_avg": (sum(hours) / len(hours)) if hours else None,
            "hours_total": sum(hours) if hours else None,
        }

    result = {p: summarize(b["days"], b["hours"]) for p, b in buckets.items()}
    all_days = [d for b in buckets.values() for d in b["days"]]
    all_hours = [h for b in buckets.values() for h in b["hours"]]
    result["Total"] = summarize(all_days, all_hours)
    return result


# ── Ventana principal ─────────────────────────────────────────────────────────

class ReportWindow(tk.Toplevel):
    """Ventana de reportes. Se abre desde main._show_report()."""

    def __init__(self, master, task_service):
        super().__init__(master)
        self.withdraw()

        self.task_service = task_service
        self.title("Reportes")
        self.configure(bg=C["bg"])
        self.geometry("1280x720")   # ancho x alto
        self.minsize(1000, 600) 

        self._filter_project = tk.StringVar(value="all")
        self._date_from = tk.StringVar(value=PLACEHOLDER)
        self._date_to   = tk.StringVar(value=PLACEHOLDER)
        self._basis_var = tk.StringVar(value=BASIS_RESOLVED)

        self._build_ui()
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)

        center_window(self, master)
        self._refresh()
        self.deiconify()
        self.focus()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self, bg=C["sidebar"], pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Reportes", bg=C["sidebar"], fg=C["text"],
                 font=("Helvetica", 15, "bold")).pack(side="left", padx=20)

        close_btn = tk.Button(header, text="Cerrar", bg=C["button"], fg=C["muted"],
                              font=("Helvetica", 9), relief="flat", bd=0,
                              padx=10, pady=4, cursor="hand2", command=self.destroy)
        add_hover(close_btn, lighten(C["accent"], 0.25), C["button"])
        close_btn.pack(side="right", padx=16)

        export_btn = tk.Button(header, text="Exportar Excel", bg=C["button"], fg="white",
                               font=("Helvetica", 9, "bold"), relief="flat", bd=0,
                               padx=12, pady=4, cursor="hand2",
                               command=self._export_excel)
        add_hover(export_btn, lighten(C["accent"], 0.25), C["button"])
        export_btn.pack(side="right", padx=6)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        self._build_filter_bar()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # Tarjetas KPI
        self.stats_frame = tk.Frame(self, bg=C["bg"])
        self.stats_frame.pack(fill="x", padx=16, pady=12)

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self.chart_frame = tk.Frame(body, bg=C["panel"], width=460)
        self.chart_frame.pack(side="left", fill="both", padx=(16, 8), pady=(0, 16))
        self.chart_frame.pack_propagate(False)

        table_outer = tk.Frame(body, bg=C["bg"])
        table_outer.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=(0, 16))
        self._build_table(table_outer)

        # Barra de estado
        self.status_lbl = tk.Label(self, text="", bg=C["bg"], fg=C["muted"],
                                   font=("Helvetica", 8), anchor="w")
        self.status_lbl.pack(fill="x", padx=18, pady=(0, 6))

    def _build_filter_bar(self):
        bar = tk.Frame(self, bg=C["panel"], pady=8)
        bar.pack(fill="x")

        def lbl(text):
            tk.Label(bar, text=text, bg=C["panel"], fg=C["muted"],
                     font=("Helvetica", 8)).pack(side="left", padx=(10, 2))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=C["panel"], background=C["panel"],
                        foreground=C["text"], arrowcolor=C["muted"],
                        bordercolor=C["border"], selectbackground=C["dlg_input"],
                        selectforeground=C["text"], insertcolor=C["text"],
                        padding=(6, 4))
        style.map("TCombobox",
                  fieldbackground=[("readonly", C["dlg_input"]),
                                   ("active", C["panel"]), ("focus", C["panel"])],
                  background=[("active", C["hover"]), ("pressed", C["accent_dk"])],
                  foreground=[("readonly", C["text"]), ("active", C["text"]),
                              ("disabled", C["disabled_fg"])],
                  selectbackground=[("readonly", C["dlg_input"]), ("focus", C["dlg_input"])],
                  selectforeground=[("readonly", C["text"]), ("focus", C["text"])],
                  bordercolor=[("focus", C["accent"]), ("!focus", C["border"])])

        # Proyecto
        projects = self.task_service.projects
        proj_vals = [("all", "Todos los proyectos")] + [(p.id, p.name) for p in projects]
        self._proj_ids = [v[0] for v in proj_vals]
        self._proj_labels = [v[1] for v in proj_vals]
        self._proj_var_label = tk.StringVar(value="Todos los proyectos")

        lbl("Proyecto:")
        proj_cb = ttk.Combobox(bar, textvariable=self._proj_var_label,
                               values=self._proj_labels, state="readonly", width=18)
        proj_cb.pack(side="left", padx=(0, 6))
        proj_cb.bind("<<ComboboxSelected>>", self._on_proj_change)

        # Estado
        lbl("Estado:")
        self._status_label_var = tk.StringVar(value="Todos")
        s_cb = ttk.Combobox(bar, textvariable=self._status_label_var,
                            values=["Todos"] + [v for _, v in COLUMNS_STATUS],
                            state="readonly", width=14)
        s_cb.pack(side="left", padx=(0, 6))
        s_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Prioridad
        lbl("Prioridad:")
        self._priority_var = tk.StringVar(value="Todas")
        p_cb = ttk.Combobox(bar, textvariable=self._priority_var,
                            values=["Todas", *PRIORITIES], state="readonly", width=10)
        p_cb.pack(side="left", padx=(0, 6))
        p_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Fechas
        self._add_date_entry(bar, "Desde:", self._date_from, lbl)
        self._add_date_entry(bar, "Hasta:", self._date_to, lbl)

        apply_btn = tk.Button(bar, text="Aplicar", bg=C["button"], fg=C["white"],
                              font=("Helvetica", 8, "bold"), relief="flat", bd=0,
                              padx=8, pady=3, cursor="hand2", command=self._refresh)
        add_hover(apply_btn, lighten(C["accent"], 0.25), C["button"])
        apply_btn.pack(side="left", padx=6)

        clear_btn = tk.Button(bar, text="Limpiar", bg=C["button"], fg=C["muted"],
                              font=("Helvetica", 8), relief="flat", bd=0,
                              padx=8, pady=3, cursor="hand2", command=self._clear_filters)
        add_hover(clear_btn, lighten(C["accent"], 0.25), C["button"])
        clear_btn.pack(side="left")

    def _add_date_entry(self, bar, text, var, lbl):
        lbl(text)
        e = tk.Entry(bar, textvariable=var, width=11, bg=C["dlg_input"], fg=C["text"],
                     insertbackground=C["accent_hover"], relief="flat",
                     font=("Helvetica", 9))
        e.pack(side="left", padx=(0, 4))
        e.bind("<FocusIn>", lambda ev: e.delete(0, "end") if e.get() == PLACEHOLDER else None)
        e.bind("<FocusOut>", lambda ev: e.insert(0, PLACEHOLDER) if not e.get() else None)
        e.bind("<Return>", lambda ev: self._refresh())

    def _build_table(self, parent):
        tk.Label(parent, text="Detalle de tareas", bg=C["bg"], fg=C["text"],
                 font=("Helvetica", 10, "bold")).pack(anchor="w", padx=4, pady=(0, 6))

        wrapper = tk.Frame(parent, bg=C["border"], bd=1)
        wrapper.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Report.Treeview", background=C["panel"], foreground=C["text"],
                        fieldbackground=C["panel"], borderwidth=0, rowheight=28,
                        font=("Helvetica", 9))
        style.configure("Report.Treeview.Heading", background=C["sidebar"],
                        foreground=C["muted"], borderwidth=0, font=("Helvetica", 8, "bold"))
        style.map("Report.Treeview",
                  background=[("selected", C["accent_dk"])],
                  foreground=[("selected", "white")])

        cols = tuple(f[0] for f in FIELDS)
        self.tree = ttk.Treeview(wrapper, columns=cols, show="headings",
                                 style="Report.Treeview")
        for key, heading, width, _ in FIELDS:
            self.tree.heading(key, text=heading, command=lambda c=key: self._sort_by(c))
            self.tree.column(key, width=width, minwidth=50, anchor="w")

        for status_id, color in STATUS_COLORS.items():
            self.tree.tag_configure(f"s_{status_id}", foreground=color)
        self.tree.tag_configure("row_alt", background=C["row_alt"])

        vsb = ttk.Scrollbar(wrapper, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(wrapper, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        self._sort_col = None
        self._sort_asc = True

    # ── Filtros ───────────────────────────────────────────────────────────────

    def _on_proj_change(self, event=None):
        idx = self._proj_labels.index(self._proj_var_label.get())
        self._filter_project.set(self._proj_ids[idx])
        self._refresh()

    def _clear_filters(self):
        self._proj_var_label.set("Todos los proyectos")
        self._filter_project.set("all")
        self._status_label_var.set("Todos")
        self._priority_var.set("Todas")
        self._date_from.set(PLACEHOLDER)
        self._date_to.set(PLACEHOLDER)
        self._refresh()

    def _get_filtered_tasks(self):
        tasks = self.task_service.get_all()

        proj = self._filter_project.get()
        if proj and proj != "all":
            tasks = [t for t in tasks if t.project_id == proj]

        status_lbl = self._status_label_var.get()
        if status_lbl != "Todos":
            status_id = next((k for k, v in COLUMNS_STATUS if v == status_lbl), None)
            if status_id:
                tasks = [t for t in tasks if t.status == status_id]

        prio = self._priority_var.get()
        if prio != "Todas":
            tasks = [t for t in tasks if t.priority == prio]

        # Fechas (se valida el formato y se avisa si es incorrecto)
        raw_from, raw_to = self._date_from.get().strip(), self._date_to.get().strip()
        d_from, d_to = _parse_date(raw_from), _parse_date(raw_to)
        for raw, parsed, name in ((raw_from, d_from, "Desde"), (raw_to, d_to, "Hasta")):
            if raw and raw != PLACEHOLDER and not parsed:
                self.status_lbl.config(text=f"⚠ Fecha '{name}' inválida (usa AAAA-MM-DD); se ignoró.")

        if d_from or d_to:
            result = []
            for t in tasks:
                td = _parse_date(t.due)
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
        self.status_lbl.config(text="")
        tasks = self._get_filtered_tasks()
        self._render_kpis(tasks)
        self._render_chart(tasks)
        self._render_table(tasks)
        current = self.status_lbl.cget("text")
        if not current:
            self.status_lbl.config(text=f"{len(tasks)} tarea(s) mostradas")

    # ── KPIs ──────────────────────────────────────────────────────────────────

    def _render_kpis(self, tasks):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        today = datetime.now()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        progress = sum(1 for t in tasks if t.status == "progress")
        overdue = 0
        for t in tasks:
            d = _parse_date(t.due)
            if d and d < today and t.status != "done":
                overdue += 1
        pct = f"{done / total * 100:.0f}%" if total else "0%"

        m = attention_metrics(tasks, BASIS_RESOLVED)["Total"]
        avg_txt = f"{m['avg']:.1f} d" if m else "—"

        cards = [
            ("Total", str(total), C["text"]),
            ("Completadas", f"{done} ({pct})", "#4CAF50"),
            ("En progreso", str(progress), C["accent"]),
            ("Vencidas", str(overdue), "#E05A5A"),
            ("Tiempo prom. de atención", avg_txt, C["text"]),
        ]
        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(self.stats_frame, bg=C["panel"], padx=14, pady=8)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            self.stats_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=title, bg=C["panel"], fg=C["muted"],
                     font=("Helvetica", 8)).pack(anchor="w")
            tk.Label(card, text=value, bg=C["panel"], fg=color,
                     font=("Helvetica", 14, "bold")).pack(anchor="w")

    # ── Gráficas ──────────────────────────────────────────────────────────────

    def _render_chart(self, tasks):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        st = ttk.Style()
        st.configure("Chart.TNotebook", background=C["panel"], borderwidth=0)
        st.configure("Chart.TNotebook.Tab", background=C["hover"], foreground=C["muted"],
                     padding=[8, 4], font=("Helvetica", 8))
        st.map("Chart.TNotebook.Tab",
               background=[("selected", C["accent"])],
               foreground=[("selected", "white")])

        nb = ttk.Notebook(self.chart_frame, style="Chart.TNotebook")
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        for title, builder in (("Por estado", self._chart_by_status),
                               ("Por proyecto", self._chart_by_project),
                               ("Por prioridad", self._chart_by_priority),
                               ("Tiempo de atención", self._tab_attention)):
            f = tk.Frame(nb, bg=C["panel"])
            nb.add(f, text=title)
            builder(f, tasks)

    def _make_figure(self, height=3.2):
        bg = C["panel"]
        fig = Figure(figsize=(4.4, height), dpi=90, facecolor=bg, edgecolor=bg)
        ax = fig.add_subplot(111, facecolor=bg)
        ax.tick_params(colors=C["muted"], labelsize=7)
        ax.xaxis.label.set_color(C["muted"])
        ax.yaxis.label.set_color(C["muted"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        return fig, ax

    def _embed_chart(self, parent, fig, **pack_opts):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().configure(bg=C["panel"], highlightthickness=0)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, **pack_opts)
        return canvas

    def _no_data(self, parent):
        tk.Label(parent, text="Sin datos", bg=C["panel"], fg=C["muted"]).pack(expand=True)

    def _chart_by_status(self, parent, tasks):
        counts = {label: 0 for _, label in COLUMNS_STATUS}
        for t in tasks:
            label = STATUS_LABEL.get(t.status, t.status)
            counts[label] = counts.get(label, 0) + 1

        labels = [k for k, v in counts.items() if v > 0]
        if not labels:
            return self._no_data(parent)
        values = [counts[k] for k in labels]
        colors = [_hex_to_rgb(STATUS_COLORS.get(
            next((k for k, v in COLUMNS_STATUS if v == lb), "todo"), C["accent"]))
            for lb in labels]

        fig, ax = self._make_figure()
        bars = ax.barh(labels, values, color=colors, height=0.5)
        ax.bar_label(bars, fmt="%d", color=C["text"], fontsize=7, padding=3)
        ax.set_xlabel("Tareas", fontsize=7)
        ax.set_title("Por estado", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    def _chart_by_project(self, parent, tasks):
        projects = self.task_service.projects
        proj_map = {p.id: p.name for p in projects}
        color_by_name = {p.name: p.color for p in projects}
        counts = {}
        for t in tasks:
            name = proj_map.get(t.project_id, "Sin proyecto")
            counts[name] = counts.get(name, 0) + 1
        if not counts:
            return self._no_data(parent)

        color_list = [_hex_to_rgb(color_by_name.get(n, C["accent"])) for n in counts]
        fig, ax = self._make_figure()
        _, _, autotexts = ax.pie(list(counts.values()), labels=list(counts.keys()),
                                 colors=color_list, autopct="%1.0f%%", startangle=90,
                                 textprops={"color": C["text"], "fontsize": 7})
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(C["bg"])
        ax.set_title("Por proyecto", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    def _chart_by_priority(self, parent, tasks):
        counts = {p: 0 for p in PRIORITIES}
        for t in tasks:
            if t.priority in counts:
                counts[t.priority] += 1
        labels = [k for k, v in counts.items() if v > 0]
        if not labels:
            return self._no_data(parent)
        values = [counts[k] for k in labels]
        colors = [_hex_to_rgb(PRIORITY_COLORS.get(k, C["accent"])) for k in labels]

        fig, ax = self._make_figure()
        bars = ax.bar(labels, values, color=colors, width=0.4)
        ax.bar_label(bars, fmt="%d", color=C["text"], fontsize=7, padding=3)
        ax.set_ylabel("Tareas", fontsize=7)
        ax.set_title("Por prioridad", color=C["text"], fontsize=9, pad=8)
        fig.tight_layout()
        self._embed_chart(parent, fig)

    # ── Pestaña: tiempo de atención ───────────────────────────────────────────

    def _tab_attention(self, parent, tasks):
        top = tk.Frame(parent, bg=C["panel"])
        top.pack(fill="x", padx=6, pady=(6, 2))
        tk.Label(top, text="Base:", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 8)).pack(side="left")
        cb = ttk.Combobox(top, textvariable=self._basis_var, state="readonly", width=28,
                          values=[BASIS_RESOLVED, BASIS_OPEN])
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        metrics = attention_metrics(tasks, self._basis_var.get())

        cols = ("prio", "n", "avg", "med", "pct", "max", "hrs")
        heads = ("Prioridad", "Solic.", "Prom. días", "Mediana", "% 0-1 día", "Máx", "Horas prom.*")
        widths = (62, 44, 62, 56, 62, 40, 70)
        tv = ttk.Treeview(parent, columns=cols, show="headings",
                          style="Report.Treeview", height=4)
        for c_, h, w in zip(cols, heads, widths):
            tv.heading(c_, text=h)
            tv.column(c_, width=w, minwidth=36, anchor="center")
        for name in (*PRIORITIES, "Total"):
            m = metrics[name]
            if m:
                row = (name, m["n"], f"{m['avg']:.2f}", f"{m['median']:g}",
                       f"{m['pct01']:.0f}%", m["max"],
                       f"{m['hours_avg']:.1f}" if m["hours_avg"] is not None else "—")
            else:
                row = (name, 0, "—", "—", "—", "—", "—")
            tv.insert("", "end", values=row)
        tv.pack(fill="x", padx=6, pady=4)
        if USE_ESTIMATED_HOURS:
            tk.Label(parent, text=f"* Horas estimadas: días × {HOURS_PER_DAY} + {HOURS_PER_DAY}",
                     bg=C["panel"], fg=C["muted"], font=("Helvetica", 7)).pack(anchor="w", padx=8)

        data = [(p, metrics[p]) for p in PRIORITIES if metrics[p]]
        if not data:
            tk.Label(parent, text="Sin fechas de creación/cierre para calcular.\n"
                                  "Revisa los nombres de campo en CREATED_FIELDS / CLOSED_FIELDS.",
                     bg=C["panel"], fg=C["muted"], font=("Helvetica", 8),
                     justify="center").pack(expand=True)
            return

        fig, ax = self._make_figure(height=2.4)
        names = [d[0] for d in data]
        avgs = [d[1]["avg"] for d in data]
        meds = [d[1]["median"] for d in data]
        x = range(len(names))
        w = 0.35
        b1 = ax.bar([i - w / 2 for i in x], avgs, w, label="Promedio",
                    color=[_hex_to_rgb(PRIORITY_COLORS.get(n, C["accent"])) for n in names])
        b2 = ax.bar([i + w / 2 for i in x], meds, w, label="Mediana", color=_hex_to_rgb(C["muted"]))
        ax.bar_label(b1, fmt="%.1f", color=C["text"], fontsize=7, padding=2)
        ax.bar_label(b2, fmt="%.1f", color=C["text"], fontsize=7, padding=2)
        ax.set_xticks(list(x))
        ax.set_xticklabels(names)
        ax.set_ylabel("Días", fontsize=7)
        ax.set_title("Promedio vs mediana (días)", color=C["text"], fontsize=9, pad=6)
        ax.legend(fontsize=7, facecolor=C["panel"], edgecolor=C["border"], labelcolor=C["text"])
        fig.tight_layout()
        self._embed_chart(parent, fig)

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _task_value(self, t, key, proj_map):
        if key == "project":
            return proj_map.get(t.project_id, "—")
        if key == "status":
            return STATUS_LABEL.get(t.status, t.status)
        val = getattr(t, key, "")
        return "—" if val in ("", None) else val

    def _render_table(self, tasks):
        self.tree.delete(*self.tree.get_children())
        proj_map = {p.id: p.name for p in self.task_service.projects}
        for i, t in enumerate(tasks):
            tags = (f"s_{t.status}", "row_alt" if i % 2 else "")
            values = tuple(self._task_value(t, f[0], proj_map) for f in FIELDS)
            self.tree.insert("", "end", iid=str(t.id), tags=tags, values=values)
        self._sort_col = None

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col, self._sort_asc = col, True

        def key(item):
            v = item[0]
            try:
                return (0, float(v), "")
            except (ValueError, TypeError):
                return (1, 0, str(v).lower())

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(key=key, reverse=not self._sort_asc)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)

        # Indicador de orden en el encabezado
        for key_, heading, *_ in FIELDS:
            arrow = (" ▲" if self._sort_asc else " ▼") if key_ == col else ""
            self.tree.heading(key_, text=heading + arrow)

    # ── Exportar Excel ────────────────────────────────────────────────────────

    def _export_excel(self):
        tasks = self._get_filtered_tasks()
        proj_map = {p.id: p.name for p in self.task_service.projects}

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
        if not path:
            return

        try:
            wb = openpyxl.Workbook()
            self._xl_tasks_sheet(wb.active, tasks, proj_map)
            self._xl_attention_sheet(wb.create_sheet("Tiempo de atención"), tasks)
            self._xl_summary_sheet(wb.create_sheet("Resumen"), tasks)
            wb.save(path)
        except PermissionError:
            messagebox.showerror("Error", "No se pudo guardar: el archivo está abierto en otro programa.")
            return
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo exportar:\n{exc}")
            return
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _xl_tasks_sheet(self, ws, tasks, proj_map):
        ws.title = "Reporte de Tareas"
        header_fill = PatternFill("solid", fgColor="7C6FE0")
        header_font = Font(bold=True, color="FFFFFF", size=10)

        for col_idx, f in enumerate(FIELDS, 1):
            cell = ws.cell(row=1, column=col_idx, value=f[1])
            cell.fill, cell.font = header_fill, header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 22

        for row_idx, t in enumerate(tasks, 2):
            for col_idx, (key, *_rest) in enumerate(FIELDS, 1):
                cell = ws.cell(row=row_idx, column=col_idx,
                               value=self._task_value(t, key, proj_map))
                cell.alignment = Alignment(vertical="center", wrap_text=False)
                if key == "status":
                    cell.fill = PatternFill("solid", fgColor=STATUS_FILL.get(t.status, "7A7A8A"))
                    cell.font = Font(color="FFFFFF", size=9)
                elif key == "priority":
                    cell.fill = PatternFill("solid", fgColor=PRIORITY_FILL.get(t.priority, "7A7A8A"))
                    cell.font = Font(color="FFFFFF", size=9)
                else:
                    bg = "1F1F26" if row_idx % 2 == 0 else "22222A"
                    cell.fill = PatternFill("solid", fgColor=bg)
                    cell.font = Font(color="E8E8EC", size=9)
            ws.row_dimensions[row_idx].height = 18

        for i, (*_, xl_width) in enumerate(FIELDS, 1):
            ws.column_dimensions[get_column_letter(i)].width = xl_width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def _xl_attention_sheet(self, ws, tasks):
        heads = ["Base", "Prioridad", "Solicitudes", "Promedio días", "Mediana días",
                 "% atendidas 0-1 día", "Máx días", "Horas totales (est.)", "Horas por solicitud (est.)"]
        hf = PatternFill("solid", fgColor="7C6FE0")
        for c, h in enumerate(heads, 1):
            cell = ws.cell(row=1, column=c, value=h)
            cell.fill, cell.font = hf, Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center")

        r = 2
        for basis in (BASIS_RESOLVED, BASIS_OPEN):
            metrics = attention_metrics(tasks, basis)
            for name in (*PRIORITIES, "Total"):
                m = metrics[name]
                vals = [basis, name, 0, None, None, None, None, None, None]
                if m:
                    vals = [basis, name, m["n"], round(m["avg"], 2), m["median"],
                            round(m["pct01"] / 100, 4), m["max"],
                            m["hours_total"],
                            round(m["hours_avg"], 2) if m["hours_avg"] is not None else None]
                for c, v in enumerate(vals, 1):
                    cell = ws.cell(row=r, column=c, value=v)
                    if c == 6 and v is not None:
                        cell.number_format = "0%"
                    if name == "Total":
                        cell.font = Font(bold=True)
                r += 1

        for c, w in enumerate((30, 12, 12, 14, 14, 18, 10, 14, 18), 1):
            ws.column_dimensions[get_column_letter(c)].width = w
        ws.freeze_panes = "A2"

    def _xl_summary_sheet(self, ws, tasks):
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        pct = int(done / total * 100) if total else 0
        summary = [
            ("Generado el", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("Total de tareas", total),
            ("Completadas", f"{done} ({pct}%)"),
            ("En progreso", sum(1 for t in tasks if t.status == "progress")),
            ("Alta prioridad pendiente", sum(1 for t in tasks if t.priority == "Alta" and t.status != "done")),
        ]
        for r, (label, val) in enumerate(summary, 1):
            ws.cell(row=r, column=1, value=label).font = Font(bold=True, color="7C6FE0")
            ws.cell(row=r, column=2, value=val)
        ws.column_dimensions["A"].width = 26
        ws.column_dimensions["B"].width = 22

    def _on_close(self, event=None):
        self.destroy()
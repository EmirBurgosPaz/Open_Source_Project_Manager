"""
ui/task_list.py — Widget de tabla de tareas (Treeview).
Responsabilidad: renderizar tareas, notificar doble-clic y exponer
utilidades de UX (orden, filtro rápido, atajos de teclado, tooltips
y una gama de color por prioridad + atraso).
"""

import tkinter as tk
from tkinter import ttk
from config import C, COLUMNS_STATUS, PRIORITY_STYLE , DEFAULT_PRIORITY_STYLE ,  OVERDUE_LEVELS , SOON_BG, SOON_FG , PRIORITY_ORDER 
from datetime import date
from utils.ui_helpers import setup_treeview_style, setup_treeview_hover



class TaskList(tk.Frame):
    """
    Muestra tareas en una tabla con color por prioridad y por atraso.
    on_edit_task(task_id) se llama al hacer doble clic / Enter.
    """

    def __init__(self, parent, on_edit_task, on_duplicate_task, on_delete_task, on_reorder_task):
        super().__init__(parent, bg=C["bg"])
        self.on_edit_task = on_edit_task
        self.on_duplicate_task = on_duplicate_task
        self.on_delete_task = on_delete_task
        self.on_reorder_task = on_reorder_task

        self._iid_map: dict = {}
        self._iid_tags: dict = {}
        self._iid_meta: dict = {}          # iid -> {"priority":..., "due_delta":..., "search":...}
        self._configured_tags: set = set()
        self._all_iids: list = []
        self._tree = None
        self._sort_state = {"col": None, "reverse": False}
        self._tooltip = None
        self._last_hovered = None

        

    # ────────────────────────── estilo base ──────────────────────────


    # ─────────────────────────── construcción ─────────────────────────
    def render(self, tasks: list, projects: list):
        """Limpia y vuelve a pintar la lista completa."""
        style_name = setup_treeview_style()
        self._tooltip = None
        self._tt_label = None

        for w in self.winfo_children():
            w.destroy()
        self._iid_map = {}
        self._iid_tags = {}
        self._iid_meta = {}
        self._configured_tags = set()
        self._all_iids = []
        self._sort_state = {"col": None, "reverse": False}

        # ── Barra superior: filtro rápido + resumen ──────────────────
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", pady=(0, 6))

        cols = ("Tarea", "Proyecto", "Area", "Estado", "Prioridad", "Asignado", "Fecha")
        widths = [340, 340, 115, 115, 115, 115, 95]

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        tree = ttk.Treeview(body, columns=cols, show="headings",
                            style=style_name, selectmode="browse")

        vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")

        self._tree = tree
        for col, w in zip(cols, widths):
            tree.heading(col, text=col, anchor="w",
                        command=lambda c=col: self._sort_by(c))
            tree.column(col, width=w, anchor="w", minwidth=w, stretch=False)
        tree.column("Fecha", width=95, anchor="w", minwidth=95, stretch=True)

        tree.tag_configure("odd", background=C["bg"])
        tree.tag_configure("even", background=C["row_alt"])
        tree.tag_configure("hover", background=C["hover"])

        # ──Deseleccionar al hacer clic fuera ──────────────────
        def deselect_all():
            """Deselecciona todos los items y oculta el tooltip."""
            tree.selection_remove(tree.selection())
            self._hide_tooltip()

        def on_click_outside(e):
            """Deselecciona cuando se hace clic fuera de los items."""
            region = tree.identify_region(e.x, e.y)
            if region in ("nothing", "heading"):
                deselect_all()
                return "break"

        # Vincular eventos para deseleccionar
        tree.bind("<Button-1>", on_click_outside, add=True)
        tree.bind("<Button-3>", on_click_outside, add=True)   # Windows/Linux
        tree.bind("<Button-2>", on_click_outside, add=True)   # macOS

        # Deseleccionar con Escape
        tree.bind("<Escape>", lambda e: deselect_all())

        # Deseleccionar al hacer clic en el scrollbar
        vsb.bind("<Button-1>", lambda e: deselect_all())

        # ── Menú contextual ────────────────────────────────────────────
        menu = tk.Menu(self, tearoff=0, bg=C["panel"], fg=C["text"],
                       activebackground=C["accent"], activeforeground="white",
                       font=("Helvetica", 10), bd=0)
        menu.add_command(label="✎  Editar", command=lambda: self._on_double_click(tree))
        menu.add_command(label="⧉  Duplicar", command=lambda: self._on_duplicate(tree))
        menu.add_separator()
        menu.add_command(label="✕  Eliminar", command=lambda: self._on_delete(tree))

        def show_menu(e):
            row = tree.identify_row(e.y)
            if row:
                tree.selection_set(row)
                menu.tk_popup(e.x_root, e.y_root)
            else:
                # Si se hace clic derecho fuera, deseleccionar
                deselect_all()

        tree.bind("<Button-3>", show_menu)   # clic derecho Windows/Linux
        tree.bind("<Button-2>", show_menu)   # clic derecho macOS

        # ── Atajos de teclado ─────────────────────────────────────────
        tree.bind("<Return>", lambda e: self._on_double_click(tree))
        tree.bind("<KP_Enter>", lambda e: self._on_double_click(tree))
        tree.bind("<Delete>", lambda e: self._on_delete(tree))
        tree.bind("<Control-d>", lambda e: self._on_duplicate(tree))
        tree.bind("<Double-1>", lambda e: self._on_double_click(tree))

        # ── Drag & Drop ───────────────────────────────────────────────
        self._drag_source = None

        def on_drag_start(e):
            row = tree.identify_row(e.y)
            if row:
                self._drag_source = row
                tree.selection_set(row)

        def on_drag_motion(e):
            if not self._drag_source:
                return
            target = tree.identify_row(e.y)
            if target and target != self._drag_source:
                tree.selection_set(target)

        def on_drag_release(e):
            if not self._drag_source:
                return
            target = tree.identify_row(e.y)
            if target and target != self._drag_source:
                self._swap_rows(tree, self._drag_source, target)
            self._drag_source = None

        tree.bind("<ButtonPress-1>", on_drag_start)
        tree.bind("<B1-Motion>", on_drag_motion)
        tree.bind("<ButtonRelease-1>", on_drag_release)

        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill="both", expand=True)

        proj_map = {p.id: p.name for p in projects}

        overdue_count = 0
        today_count = 0

        for i, task in enumerate(tasks):
            tag, due_delta = self._resolve_tag(tree, task, i)
            prio_style = PRIORITY_STYLE.get(task.priority, DEFAULT_PRIORITY_STYLE)

            if due_delta is not None and due_delta < 0 and task.status != "done":
                overdue_count += 1
            if due_delta == 0 and task.status != "done":
                today_count += 1

            status_label = next((c[1] for c in COLUMNS_STATUS if c[0] == task.status), task.status)

            prio_label = f"{task.priority} {prio_style['icon']}"

            iid = tree.insert("", "end", tags=(tag,), values=(
                task.title,
                proj_map.get(task.project_id, "?"),
                task.client,
                status_label,
                prio_label,
                task.assign,
                task.due,
            ))

            self._iid_map[iid] = task.id
            self._iid_tags[iid] = (tag,)
            self._iid_meta[iid] = {
                "priority": task.priority,
                "due": task.due,
                "due_delta": due_delta,
                "search": f"{task.title} {task.client} {task.assign}".lower(),
            }
            self._all_iids.append(iid)

        tk.Label(self,
                 text="Doble clic o Enter para editar · Supr elimina · Ctrl+D duplica · "
                      "Filtrar por proyecto en la barra lateral",
                 bg=C["bg"], fg=C["muted"], font=("Helvetica", 9)).pack(pady=6)

        # ── Hover + tooltip de fecha ───────────────────────────────────
        def _extra_motion(e, row):
            col = tree.identify_column(e.x)
            if row and col == f"#{cols.index('Fecha') + 1}":
                self._show_tooltip(e.x_root, e.y_root, row)
            else:
                self._hide_tooltip()

        def _extra_leave(e):
            self._hide_tooltip()

        setup_treeview_hover(
            tree,
            get_base_tag=lambda iid: self._iid_tags.get(iid, ("odd",)),
            on_motion_extra=_extra_motion,
            on_leave_extra=_extra_leave,
        )
    # ───────────────────────── color por fila ─────────────────────────
    def _resolve_tag(self, tree, task, idx):
        """Calcula un único tag compuesto (prioridad + atraso + estado)
        y lo registra en el Treeview la primera vez que se usa."""
        prio_style = PRIORITY_STYLE.get(task.priority, DEFAULT_PRIORITY_STYLE)
        due_delta = None
        try:
            due_delta = (date.fromisoformat(task.due) - date.today()).days
        except (ValueError, TypeError):
            pass

        if task.status == "done":
            key, bg, fg, bold = "done", C["done_bg"], C["done_fg"], False

        elif due_delta is not None and due_delta < 0:
            days_late = -due_delta
            level = next((lvl for lvl in OVERDUE_LEVELS if days_late >= lvl[0]), OVERDUE_LEVELS[-1])
            key = f"overdue_{level[0]}_{'b' if prio_style['bold'] else 'n'}"
            bg, fg, bold = level[1], level[2], prio_style["bold"]

        elif due_delta == 0:
            key = f"due_today_{'b' if prio_style['bold'] else 'n'}"
            bg, fg, bold = C["today_bg"], C["today_fg"], prio_style["bold"]

        elif due_delta is not None and 0 < due_delta <= 3:
            key = f"due_soon_{'b' if prio_style['bold'] else 'n'}"
            bg, fg, bold = SOON_BG, SOON_FG, prio_style["bold"]

        else:
            key = f"prio_{task.priority}"
            bg, fg, bold = prio_style["bg"], prio_style["fg"], prio_style["bold"]

        if key not in self._configured_tags:
            tree.tag_configure(key, background=bg, foreground=fg,
                              font=("Helvetica", 10, "bold" if bold else "normal"))
            self._configured_tags.add(key)

        return key, due_delta




    # ───────────────────────────── orden ───────────────────────────────
    def _sort_by(self, col):
        tree = self._tree
        if not tree:
            return
        
        # Deseleccionar todas las tareas antes de ordenar
        tree.selection_remove(tree.selection())
        self._hide_tooltip()
        
        reverse = self._sort_state["col"] == col and not self._sort_state["reverse"]
    
        def sort_key(iid):
            meta = self._iid_meta.get(iid, {})
            if col == "Prioridad":
                return PRIORITY_ORDER.get(meta.get("priority"), 99)
            if col == "Fecha":
                try:
                    return date.fromisoformat(meta.get("due"))
                except (ValueError, TypeError):
                    return date.max
            return str(tree.set(iid, col)).lower()
    
        ordered = sorted(self._all_iids, key=sort_key, reverse=reverse)
        for index, iid in enumerate(ordered):
            tree.move(iid, "", index)
    
        self._sort_state = {"col": col, "reverse": reverse}
        cols = ("Tarea", "Proyecto", "Area", "Estado", "Prioridad", "Asignado", "Fecha")
        for c in cols:
            label = c
            if c == col:
                label += " ▼" if reverse else " ▲"
            tree.heading(c, text=label, command=lambda c=c: self._sort_by(c))

    # ───────────────────────── tooltip de fecha ────────────────────────
    def _show_tooltip(self, x, y, iid):
        meta = self._iid_meta.get(iid)
        if not meta:
            return
        delta = meta.get("due_delta")
        if delta is None:
            text = "Sin fecha válida"
        elif delta < 0:
            text = f"Atrasada {-delta} día{'s' if -delta != 1 else ''}"
        elif delta == 0:
            text = "Vence hoy"
        else:
            text = f"Vence en {delta} día{'s' if delta != 1 else ''}"

        if self._tooltip is None or not self._tooltip.winfo_exists():
            self._tooltip = tk.Toplevel(self)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.configure(bg=C["dlg_border"])
            self._tt_label = tk.Label(self._tooltip, text=text, bg=C["panel"], fg=C["text"],
                                      font=("Helvetica", 9), padx=8, pady=3)
            self._tt_label.pack(padx=1, pady=1)
        else:
            self._tt_label.config(text=text)
        self._tooltip.wm_geometry(f"+{x + 12}+{y + 12}")
        self._tooltip.deiconify()

    def _hide_tooltip(self):
        if self._tooltip is not None and self._tooltip.winfo_exists():
            self._tooltip.withdraw()

    # ───────────────────────── callbacks de fila ───────────────────────
    def _on_double_click(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = self._iid_map.get(sel[0])
        if task_id is not None:
            self.on_edit_task(task_id)

    def _on_duplicate(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = self._iid_map.get(sel[0])
        if task_id is not None:
            self.on_duplicate_task(task_id)

    def _on_delete(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = self._iid_map.get(sel[0])
        if task_id is not None:
            self.on_delete_task(task_id)

    def _swap_rows(self, tree, source_iid: str, target_iid: str):
        src_idx = tree.index(source_iid)
        tgt_idx = tree.index(target_iid)

        tree.move(source_iid, "", tgt_idx)
        tree.move(target_iid, "", src_idx)

        src_id = self._iid_map.get(source_iid)
        tgt_id = self._iid_map.get(target_iid)
        if src_id is not None and tgt_id is not None:
            self.on_reorder_task(src_id, tgt_id)
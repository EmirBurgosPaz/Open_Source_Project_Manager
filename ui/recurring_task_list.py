import tkinter as tk
from tkinter import ttk
from config import C


class RecurringTaskList(tk.Frame):
    def __init__(self, parent, on_edit, on_new, on_reorder_task):
        super().__init__(parent, bg=C["bg"])
        self.on_edit = on_edit
        self._iid_map = {}
        self._build_header(on_new)
        self._setup_style()
        self.on_reorder_task = on_reorder_task

    def _build_header(self, on_new):
        header = tk.Frame(self, bg=C["panel"])
        header.pack(fill="x")
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        self.table_frame = tk.Frame(self, bg=C["bg"])
        self.table_frame.pack(fill="both", expand=True)

    def _setup_style(self):
        style = ttk.Style()
        style.configure("Recurring.Treeview",
                        background=C["bg"], foreground=C["text"],
                        fieldbackground=C["bg"], bordercolor=C["border"],
                        rowheight=32, font=("Helvetica", 10))
        style.configure("Recurring.Treeview.Heading",
                        background=C["panel"], foreground=C["muted"],
                        bordercolor=C["border"], relief="flat",
                        font=("Helvetica", 9, "bold"))
        style.map("Recurring.Treeview",
                  background=[("selected", C["accent_dk"])],
                  foreground=[("selected", "#FFFFFF")])

    def render(self, tasks: list):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self._iid_map = {}

        cols   = ("Categoría", "Tarea", "Frecuencia", "Status", "Prioridad")
        widths = [100, 320, 110, 110, 80]

        tree = ttk.Treeview(self.table_frame, columns=cols, show="headings",
                            style="Recurring.Treeview", selectmode="browse")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w", minwidth=60)

        tree.tag_configure("odd",  background=C["bg"])
        tree.tag_configure("even", background=C["row_alt"])
        tree.tag_configure("odd_hover",  background=C["hover"])
        tree.tag_configure("even_hover", background=C["hover"])

        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        for i, task in enumerate(tasks):
            iid = tree.insert("", "end", tags=("even" if i % 2 == 0 else "odd",), values=(
                task.category,
                task.title,
                task.frequency,
                task.status,
                task.priority,
            ))
            self._iid_map[iid] = task.id

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

        tree.bind("<ButtonPress-1>",   on_drag_start)
        tree.bind("<B1-Motion>",       on_drag_motion)
        tree.bind("<ButtonRelease-1>", on_drag_release)

        # Hover
        self._last_hovered = None

        def on_motion(e):
            row = tree.identify_row(e.y)
            if row == self._last_hovered:
                return
            if self._last_hovered and self._last_hovered in tree.get_children():
                idx = tree.index(self._last_hovered)
                tree.item(self._last_hovered, tags=("even" if idx % 2 == 0 else "odd",))
            if row:
                idx = tree.index(row)
                tree.item(row, tags=(f"{'even' if idx % 2 == 0 else 'odd'}_hover",))
            self._last_hovered = row

        def on_leave(e):
            if self._last_hovered and self._last_hovered in tree.get_children():
                idx = tree.index(self._last_hovered)
                tree.item(self._last_hovered, tags=("even" if idx % 2 == 0 else "odd",))
            self._last_hovered = None

        tree.bind("<Motion>",     on_motion)
        tree.bind("<Leave>",      on_leave)
        tree.bind("<Double-1>",   lambda e: self._on_double_click(tree))



    def _on_double_click(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = self._iid_map.get(sel[0])
        if task_id is not None:
            self.on_edit(task_id)
    
    def _swap_rows(self, tree, source_iid: str, target_iid: str):
        src_idx = tree.index(source_iid)
        tgt_idx = tree.index(target_iid)

        # Intercambiar en el Treeview visualmente
        tree.move(source_iid, "", tgt_idx)
        tree.move(target_iid, "", src_idx)

        # Notificar al exterior con los ids reales
        src_id = self._iid_map.get(source_iid)
        tgt_id = self._iid_map.get(target_iid)
        if src_id is not None and tgt_id is not None:
            self.on_reorder_task(src_id, tgt_id)
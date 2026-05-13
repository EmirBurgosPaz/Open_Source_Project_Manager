"""
ui/task_list.py — Widget de tabla de tareas (Treeview).
Solo responsabilidad: renderizar tareas y notificar doble-clic.
"""

import tkinter as tk
from tkinter import ttk
from config import C, COLUMNS, PRIORITY_COLORS
from datetime import date

class TaskList(tk.Frame):
    """
    Muestra tareas en una tabla con filas alternadas.
    on_edit_task(task_id) se llama al hacer doble clic.
    """

    def __init__(self, parent, on_edit_task, on_duplicate_task, on_delete_task,on_reorder_task):
        super().__init__(parent, bg=C["bg"])
        self.on_edit_task = on_edit_task
        self._iid_map: dict = {}
        self._setup_style()
        self.on_duplicate_task = on_duplicate_task
        self.on_delete_task    = on_delete_task
        self.on_reorder_task = on_reorder_task

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                        background=C["bg"], foreground=C["text"],
                        fieldbackground=C["bg"], bordercolor=C["border"],
                        rowheight=36, font=("Helvetica", 10))
        style.configure("Dark.Treeview.Heading",
                        background=C["panel"], foreground=C["muted"],
                        bordercolor=C["border"], relief="flat",
                        font=("Helvetica", 9, "bold"))
        style.map("Dark.Treeview",
                  background=[("selected", C["accent_dk"])],
                  foreground=[("selected", C["white"])])

    def render(self, tasks: list, projects: list):
        """Limpia y vuelve a pintar la lista completa."""
        for w in self.winfo_children():
            w.destroy()
        self._iid_map = {}

        cols   = ("Tarea", "Proyecto", "Estado", "Prioridad", "Asignado", "Fecha")
        widths = [340, 110, 115, 85, 105, 95]

        tree = ttk.Treeview(self, columns=cols, show="headings",
                            style="Dark.Treeview", selectmode="browse")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w", minwidth=60)
        

        tree.tag_configure("todo",    foreground=C["todo_fg"])  # ← agrega
        tree.tag_configure("revision",    foreground=C["progress_tasks"])  # ← agrega
        tree.tag_configure("high_priority", background=C["high_bg"])
        tree.tag_configure("odd",  background=C["bg"])
        tree.tag_configure("even", background=C["row_alt"])
        tree.tag_configure("overdue",   background=C["over_bg"], foreground=C["over_fg"])  # ← agrega
        tree.tag_configure("due_today", background=C["today_bg"], foreground=C["today_fg"])  # ← agrega
        # Tags de hover
        tree.tag_configure("odd_hover",  background=C["hover"])
        tree.tag_configure("even_hover", background=C["hover"])
        tree.tag_configure("hover",     background=C["hover"])
        self._iid_tags = {}
        
        # Menú contextual
        menu = tk.Menu(self, tearoff=0, bg=C["panel"], fg=C["text"],
                       activebackground=C["accent"], activeforeground="white",
                       font=("Helvetica", 10), bd=0)
        menu.add_command(label="✎  Editar",    command=lambda: self._on_double_click(tree))
        menu.add_command(label="⧉  Duplicar",  command=lambda: self._on_duplicate(tree))
        menu.add_separator()
        menu.add_command(label="✕  Eliminar",  command=lambda: self._on_delete(tree))

        def show_menu(e):
            row = tree.identify_row(e.y)
            if row:
                tree.selection_set(row)
                menu.tk_popup(e.x_root, e.y_root)

        tree.bind("<Button-3>", show_menu)   # clic derecho Windows/Linux
        tree.bind("<Button-2>", show_menu)   # clic derecho macOS

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

        vsb = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        proj_map = {p.id: p.name for p in projects}

        for i, task in enumerate(tasks):

            col_info = next((c for c in COLUMNS if c[0] == task.status), ("?", "?", "#888"))

            base_tag = self._due_tag(task.due, i, task.status)

            tags_fila = (base_tag,)

            # 3. Evaluamos si la tarea está "por hacer" y agregamos el tag "todo"
            # Asegúrate de que "todo" coincida exactamente con la palabra 
            # que usas en el estatus (podría ser "To-Do" o "todo")

            if task.status != "done":
                tags_fila = (base_tag, "todo")

            if task.status == "review":
                tags_fila = (base_tag, "revision")
            
            if task.priority == "Alta": 
                tags_fila = (base_tag, "high_priority")

            iid = tree.insert("", "end", tags=tags_fila, values=(
                task.title,
                proj_map.get(task.project_id, "?"),
                col_info[1],
                task.priority,
                task.assign,
                task.due,
            ))

            self._iid_map[iid] = task.id
            self._iid_tags[iid] = tags_fila

        tree.bind("<Double-1>", lambda e: self._on_double_click(tree))

        tk.Label(self,
                 text="Doble clic en una fila para editar · Filtrar por proyecto en la barra lateral",
                 bg=C["bg"], fg=C["muted"], font=("Helvetica", 9)).pack(pady=6)

            # Variable para rastrear la fila anterior
        self._last_hovered = None
        
        def on_motion(e):

            row = tree.identify_row(e.y)

            if row == self._last_hovered:
                return
            
            if self._last_hovered and self._last_hovered in tree.get_children():

                original_tag = self._iid_tags.get(self._last_hovered,( "odd",))
                tree.item(self._last_hovered, tags=original_tag)

            if row:
                tree.item(row, tags=("hover",))

            self._last_hovered = row

        def on_leave(e):
        
            if self._last_hovered and self._last_hovered in tree.get_children():

                original_tag = self._iid_tags.get(self._last_hovered, ("odd",))

                tree.item(self._last_hovered, tags=original_tag)

            self._last_hovered = None

        tree.bind("<Motion>", on_motion)
        tree.bind("<Leave>",  on_leave)


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

        # Intercambiar en el Treeview visualmente
        tree.move(source_iid, "", tgt_idx)
        tree.move(target_iid, "", src_idx)

        # Notificar al exterior con los ids reales
        src_id = self._iid_map.get(source_iid)
        tgt_id = self._iid_map.get(target_iid)
        if src_id is not None and tgt_id is not None:
            self.on_reorder_task(src_id, tgt_id)

    def _due_tag(self, due_str: str, idx: int, status : str) -> str:
        try:
            
            due  = date.fromisoformat(due_str)
            hoy  = date.today()
            if (due < hoy) and (status != "done"):
                return "overdue"
            if (due == hoy) and (status != "done"):
                return "due_today"
        except (ValueError, TypeError):
            pass
        return "even" if idx % 2 == 0 else "odd"
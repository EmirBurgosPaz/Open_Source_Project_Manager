"""
ui/task_list.py — Widget de tabla de tareas (Treeview).
Solo responsabilidad: renderizar tareas y notificar doble-clic.
"""

import tkinter as tk
from tkinter import ttk
from config import C, COLUMNS


class TaskList(tk.Frame):
    """
    Muestra tareas en una tabla con filas alternadas.
    on_edit_task(task_id) se llama al hacer doble clic.
    """

    def __init__(self, parent, on_edit_task):
        super().__init__(parent, bg=C["bg"])
        self.on_edit_task = on_edit_task
        self._iid_map: dict = {}
        self._setup_style()

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
                  foreground=[("selected", "#FFFFFF")])

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

        tree.tag_configure("odd",  background=C["bg"])
        tree.tag_configure("even", background=C["row_alt"])

        # Tags de hover
        tree.tag_configure("odd_hover",  background=C["hover"])
        tree.tag_configure("even_hover", background=C["hover"])
        
        # Variable para rastrear la fila anterior
        self._last_hovered = None
        
        def on_motion(e):
            row = tree.identify_row(e.y)
            if row == self._last_hovered:
                return
            # Restaurar fila anterior
            if self._last_hovered and self._last_hovered in tree.get_children():
                idx = tree.index(self._last_hovered)
                tree.item(self._last_hovered, tags=("even" if idx % 2 == 0 else "odd",))
            # Aplicar hover a la fila actual
            if row:
                idx = tree.index(row)
                tree.item(row, tags=(f"{'even' if idx % 2 == 0 else 'odd'}_hover",))
            self._last_hovered = row
        
        def on_leave(e):
            if self._last_hovered and self._last_hovered in tree.get_children():
                idx = tree.index(self._last_hovered)
                tree.item(self._last_hovered, tags=("even" if idx % 2 == 0 else "odd",))
            self._last_hovered = None
        
        tree.bind("<Motion>", on_motion)
        tree.bind("<Leave>",  on_leave)

        vsb = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        proj_map = {p.id: p.name for p in projects}

        for i, task in enumerate(tasks):
            col_info = next((c for c in COLUMNS if c[0] == task.status), ("?", "?", "#888"))
            iid = tree.insert("", "end", tags=("even" if i % 2 == 0 else "odd",), values=(
                task.title,
                proj_map.get(task.project_id, "?"),
                col_info[1],
                task.priority,
                task.assign,
                task.due,
            ))
            self._iid_map[iid] = task.id

        tree.bind("<Double-1>", lambda e: self._on_double_click(tree))

        tk.Label(self,
                 text="Doble clic en una fila para editar · Filtrar por proyecto en la barra lateral",
                 bg=C["bg"], fg=C["muted"], font=("Helvetica", 9)).pack(pady=6)

    def _on_double_click(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = self._iid_map.get(sel[0])
        if task_id is not None:
            self.on_edit_task(task_id)

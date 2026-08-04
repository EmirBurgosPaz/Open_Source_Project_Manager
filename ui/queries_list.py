"""
ui/queries_list.py

Vista principal del módulo de documentación de queries.
Sigue el mismo patrón que task_list.py: Treeview + menú contextual +
container de filtros arriba. Pensada para integrarse como una pestaña
más del sidebar (ej. "Queries" junto a Proyectos / Tareas).

Uso típico dentro de tu app:

    from ui.queries_list import QueriesListFrame

    frame = QueriesListFrame(contenedor)
    frame.pack(fill="both", expand=True)
"""

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from config import C
except ImportError:
    C = {
        "bg": "#1e1e2e",
        "bg_secondary": "#181825",
        "bg": "#cdd6f4",
        "accent": "#89b4fa",
        "panel": "#313244",
        "border": "#45475a",
        "danger": "#f38ba8",
        "success": "#a6e3a1",
        "hover": "#313244",
        "row_alt": "#181825",
        "panel": "#1e1e2e",
        "muted": "#6c7086",
    }

from storage.queries_manager import CATEGORIAS_DEFAULT
from storage.queries_manager import QueriesManager
from ui.queries_dialog import QueriesDialog


class QueriesListFrame(tk.Frame):
    def __init__(self, parent, data_file="queries_data.json"):
        super().__init__(parent, bg=C["bg"])
        self.manager = QueriesManager(data_file)
        self._filtro_categoria = "Todas"
        self._filtro_texto = ""
        self._all_iids = []
        self._iid_map = {}
        
        self._build_ui()
        self.render()

    # ---------- UI ----------

    def _build_ui(self):
        """Construye la estructura completa de la UI"""
        # Contenedor principal
        container = tk.Frame(self, bg=C["bg"])
        container.pack(fill="both", expand=True, padx=12, pady=12)
        
        # ── Barra de filtros ──────────────────────────────────────────
        filter_frame = tk.Frame(container, bg=C["bg"], relief="flat", bd=1)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        filter_content = tk.Frame(filter_frame, bg=C["bg"])
        filter_content.pack(fill="x", padx=12, pady=8)
        
        # Buscar
        tk.Label(filter_content, text="🔍 Buscar:", bg=C["panel"], fg=C["white"]).pack(side="left")
        self.entry_buscar = tk.Entry(
            filter_content, bg=C["panel"], fg=C["white"],
            insertbackground=C["bg"], relief="flat", width=30
        )
        self.entry_buscar.pack(side="left", padx=(6, 12))
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._on_filter_change())
        
        # Categoría
        tk.Label(filter_content, text="📂 Categoría:", bg=C["bg_secondary"], fg=C["bg"]).pack(side="left")
        self.combo_filtro = ttk.Combobox(
            filter_content, values=["Todas"] + CATEGORIAS_DEFAULT, 
            state="readonly", width=25
        )
        self.combo_filtro.set("Todas")
        self.combo_filtro.pack(side="left", padx=(6, 12))
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())
        
        # Botón Nueva Query
        tk.Button(
            filter_content, text="Crear querrie ➕", command=self._nueva_query,
            bg=C["accent"], fg=C["white"], relief="flat", 
            padx=15, pady=5, font=("Segoe UI", 10, "bold"), cursor="hand2"
        ).pack(side="right")
        
        # ── Contador de resultados ────────────────────────────────────
        self.lbl_count = tk.Label(
            container, text="", bg=C["bg"], fg=C["muted"],
            font=("Segoe UI", 9), anchor="w"
        )
        self.lbl_count.pack(fill="x", pady=(0, 6))
        
        # ── Treeview ──────────────────────────────────────────────────
        body = tk.Frame(container, bg=C["bg"])
        body.pack(fill="both", expand=True)
        
        cols = ("Nombre", "Categoría", "Origen", "Modificado")
        widths = [280, 200, 150, 150]
        
        self.tree = ttk.Treeview(body, columns=cols, show="headings",
                                 style="Dark.Treeview", selectmode="browse")
        
        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=w, anchor="w", minwidth=w, stretch=False)
        
        # Configurar tags para colores alternos
        self.tree.tag_configure("odd", background=C["bg"])
        self.tree.tag_configure("even", background=C["row_alt"])
        self.tree.tag_configure("hover", background=C["hover"])
        
        # ── Eventos ───────────────────────────────────────────────────
        self.tree.bind("<Double-1>", lambda e: self._editar_seleccionada())
        self.tree.bind("<Button-3>", self._menu_contextual)
        self.tree.bind("<Return>", lambda e: self._editar_seleccionada())
        self.tree.bind("<KP_Enter>", lambda e: self._editar_seleccionada())
        self.tree.bind("<Delete>", lambda e: self._eliminar_seleccionada())
        self.tree.bind("<Control-d>", lambda e: self._duplicar_seleccionada())
        
        # Hover effect
        self._last_hovered = None
        
        def on_motion(e):
            row = self.tree.identify_row(e.y)
            if row != self._last_hovered:
                if self._last_hovered and self._last_hovered in self.tree.get_children():
                    idx = self._all_iids.index(self._last_hovered) if self._last_hovered in self._all_iids else 0
                    tag = "even" if idx % 2 else "odd"
                    self.tree.item(self._last_hovered, tags=(tag,))
                if row:
                    self.tree.item(row, tags=("hover",))
                self._last_hovered = row
        
        def on_leave(e):
            if self._last_hovered and self._last_hovered in self.tree.get_children():
                idx = self._all_iids.index(self._last_hovered) if self._last_hovered in self._all_iids else 0
                tag = "even" if idx % 2 else "odd"
                self.tree.item(self._last_hovered, tags=(tag,))
            self._last_hovered = None
        
        self.tree.bind("<Motion>", on_motion)
        self.tree.bind("<Leave>", on_leave)
        
        # ── Menú contextual ──────────────────────────────────────────
        self.menu = tk.Menu(self, tearoff=0, bg=C["panel"], fg=C["text"],
                           activebackground=C["accent"], activeforeground="white",
                           font=("Helvetica", 10), bd=0)
        self.menu.add_command(label="✏️  Editar", command=self._editar_seleccionada)
        self.menu.add_command(label="📋  Duplicar", command=self._duplicar_seleccionada)
        self.menu.add_command(label="📄  Copiar SQL", command=self._copiar_sql)
        self.menu.add_separator()
        self.menu.add_command(label="🗑️  Eliminar", command=self._eliminar_seleccionada)
        
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill="both", expand=True)
        
        # ── Pie de página ────────────────────────────────────────────
        tk.Label(
            container,
            text="Doble clic o Enter para editar · Supr elimina · Ctrl+D duplica",
            bg=C["bg"], fg=C["muted"], 
            font=("Segoe UI", 9), anchor="w"
        ).pack(fill="x", pady=(8, 0))

    # ---------- Render ----------

    def render(self):
        """Limpia y vuelve a pintar la lista completa."""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self._all_iids = []
        self._iid_map = {}
        
        # Obtener datos filtrados
        categoria = self._filtro_categoria
        texto = self._filtro_texto
        resultados = self.manager.filtrar(categoria=categoria, texto=texto)
        
        # Ordenar por fecha de modificación (más reciente primero)
        resultados_ordenados = sorted(resultados, key=lambda x: x["modificado"], reverse=True)
        
        # Insertar en el treeview
        for idx, q in enumerate(resultados_ordenados):
            tag = "even" if idx % 2 else "odd"
            
            iid = self.tree.insert("", "end", iid=q["id"], tags=(tag,), values=(
                q["nombre"],
                q["categoria"],
                q.get("origen", ""),
                q["modificado"]
            ))
            
            self._all_iids.append(iid)
            self._iid_map[iid] = q["id"]
        
        # Actualizar contador
        total = len(resultados_ordenados)
        self.lbl_count.config(text=f"📊 {total} consulta{'s' if total != 1 else ''} encontrada{'s' if total != 1 else ''}")

    # ---------- Filtros ----------

    def _on_filter_change(self):
        """Actualiza los filtros y refresca la vista."""
        self._filtro_categoria = self.combo_filtro.get()
        self._filtro_texto = self.entry_buscar.get().strip()
        self.render()

    # ---------- Acciones ----------

    def _nueva_query(self):
        QueriesDialog(self, self.manager, on_saved=self.render)

    def _seleccion_actual(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _editar_seleccionada(self):
        qid = self._seleccion_actual()
        if qid:
            QueriesDialog(self, self.manager, query_id=qid, on_saved=self.render)

    def _duplicar_seleccionada(self):
        qid = self._seleccion_actual()
        if qid:
            self.manager.duplicar(qid)
            self.render()

    def _copiar_sql(self):
        qid = self._seleccion_actual()
        if qid:
            q = self.manager.obtener(qid)
            self.clipboard_clear()
            self.clipboard_append(q.get("sql", ""))

    def _eliminar_seleccionada(self):
        qid = self._seleccion_actual()
        if not qid:
            return
        q = self.manager.obtener(qid)
        if messagebox.askyesno("Eliminar query", f"¿Eliminar '{q['nombre']}'?"):
            self.manager.eliminar(qid)
            self.render()

    def _menu_contextual(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.tk_popup(event.x_root, event.y_root)



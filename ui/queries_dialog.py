"""
ui/queries_dialog.py

Diálogo modal para crear o editar una query documentada.
Sigue el mismo patrón visual que task_dialog.py / project_dialog.py.

Uso:
    QueriesDialog(parent, manager, on_saved=callback)                # crear
    QueriesDialog(parent, manager, query_id="uuid", on_saved=cb)      # editar
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import C, KEYBOARD_KEYS

from storage.queries_manager import CATEGORIAS_DEFAULT
from storage.queries_manager import ORIGENES_DEFAULT


class QueriesDialog(tk.Toplevel):
    def __init__(self, parent, manager, query_id=None, on_saved=None):
        super().__init__(parent)
        self.manager = manager
        self.query_id = query_id
        self.on_saved = on_saved
        self.existing = manager.obtener(query_id) if query_id else None

        self.title("Editar query" if self.existing else "Nueva query")
        self.focus()
        self.configure(bg=C["bg"])
        self.geometry("800x920")
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        if self.existing:
            self._cargar_datos(self.existing)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)

    # ---------- UI ----------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        form = tk.Frame(self, bg=C["bg"])
        form.pack(fill="both", expand=True, padx=8, pady=8)

        # Nombre
        tk.Label(form, text="Nombre", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", **pad
        )
        self.entry_nombre = tk.Entry(
            form, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat"
        )
        self.entry_nombre.pack(fill="x", padx=12)
        self.entry_nombre.focus()

        # Categoría + Origen en la misma fila
        fila = tk.Frame(form, bg=C["bg"])
        fila.pack(fill="x", padx=12, pady=(10, 0))

        col1 = tk.Frame(fila, bg=C["bg"])
        col1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Label(col1, text="Categoría", bg=C["bg"], fg=C["white"]).pack(anchor="w")
        self.combo_categoria = ttk.Combobox(
            col1, values=CATEGORIAS_DEFAULT, state="normal"
        )
        self.combo_categoria.pack(fill="x")

        col2 = tk.Frame(fila, bg=C["bg"])
        col2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(col2, text="Origen / conexión", bg=C["bg"], fg=C["white"]).pack(anchor="w")
        self.combo_origen = ttk.Combobox(
            col2, values=ORIGENES_DEFAULT, state="normal"
        )
        self.combo_origen.pack(fill="x")

        # Descripción
        tk.Label(form, text="Descripción / para qué sirve", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        self.text_desc = tk.Text(
            form, height=3, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat", wrap="word"
        )
        self.text_desc.pack(fill="x", padx=12)

        # SQL
        tk.Label(form, text="SQL", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        sql_frame = tk.Frame(form, bg=C["bg"])
        sql_frame.pack(fill="both", expand=True, padx=12)

        scroll = tk.Scrollbar(sql_frame)
        scroll.pack(side="right", fill="y")

        self.text_sql = tk.Text(
            sql_frame, bg=C["bg_secondary"], fg=C["accent"],
            insertbackground=C["accent_hover"], relief="flat", wrap="none",
            font=("Consolas", 10), undo=True, yscrollcommand=scroll.set
        )
        self.text_sql.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.text_sql.yview)

        # Tags
        tk.Label(form, text="Tags (separados por coma)", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        self.entry_tags = tk.Entry(
            form, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat"
        )
        self.entry_tags.pack(fill="x", padx=12)

        # Botones
        botones = tk.Frame(self, bg=C["bg"])
        botones.pack(fill="x", padx=12, pady=10)

        tk.Button(
            botones, text="Cancelar", command=self.destroy,
            bg=C["border"], fg=C["white"], relief="flat", padx=14
        ).pack(side="right", padx=(6, 0))

        # Botón Guardar - AHORA VISIBLE Y FUNCIONAL
        self.btn_guardar = tk.Button(
            botones, text="Guardar", command=self._guardar,
            bg=C["accent"], fg=C["white"], relief="flat", padx=14
        )
        self.btn_guardar.pack(side="right")

        # Enlazar Ctrl+S para guardar
        self.bind(KEYBOARD_KEYS["save"], lambda e: self._guardar())

    # ---------- Datos ----------

    def _cargar_datos(self, q):
        self.entry_nombre.insert(0, q["nombre"])
        self.combo_categoria.set(q["categoria"])
        self.combo_origen.set(q.get("origen", ""))
        self.text_desc.insert("1.0", q.get("descripcion", ""))
        self.text_sql.insert("1.0", q.get("sql", ""))
        self.entry_tags.insert(0, ", ".join(q.get("tags", [])))

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        categoria = self.combo_categoria.get().strip()
        origen = self.combo_origen.get().strip()
        descripcion = self.text_desc.get("1.0", "end").strip()
        sql = self.text_sql.get("1.0", "end").strip()
        tags = [t.strip() for t in self.entry_tags.get().split(",") if t.strip()]

        if not nombre:
            messagebox.showwarning("Falta información", "El nombre es obligatorio.")
            return
        if not sql:
            messagebox.showwarning("Falta información", "El SQL no puede estar vacío.")
            return
        if not categoria:
            messagebox.showwarning("Falta información", "Selecciona o escribe una categoría.")
            return

        if self.existing:
            self.manager.actualizar(
                self.query_id,
                nombre=nombre, categoria=categoria, origen=origen,
                descripcion=descripcion, sql=sql, tags=tags,
            )
        else:
            self.manager.agregar(nombre, categoria, origen, descripcion, sql, tags)

        if self.on_saved:
            self.on_saved()
        self.destroy()

    def _on_close(self, event=None):
            self.destroy()
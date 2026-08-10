"""
ui/tags_admin_dialog.py

Diálogo para gestionar tags: renombrar, cambiar color, fusionar con otro
tag, o eliminar por completo. Muestra cuántas queries usa cada tag.

Uso:
    TagsAdminDialog(self, self.tags_manager, self.manager, on_changed=callback)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser

from config import C


class TagsAdminDialog(tk.Toplevel):
    def __init__(self, parent, tags_manager, queries_manager, on_changed=None):
        super().__init__(parent)
        self.tags_manager = tags_manager
        self.queries_manager = queries_manager
        self.on_changed = on_changed

        self.title("Gestionar tags")
        self.configure(bg=C["bg"])
        self.geometry("480x520")
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._render()

    def _build_ui(self):
        cont = tk.Frame(self, bg=C["bg"])
        cont.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(cont, text="Tags existentes", bg=C["bg"], fg=C["white"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        body = tk.Frame(cont, bg=C["bg"])
        body.pack(fill="both", expand=True)

        cols = ("Tag", "Usos")
        self.tree = ttk.Treeview(body, columns=cols, show="headings",
                                 style="Dark.Treeview", selectmode="browse")
        self.tree.heading("Tag", text="Tag", anchor="w")
        self.tree.heading("Usos", text="Usos", anchor="w")
        self.tree.column("Tag", width=300, anchor="w")
        self.tree.column("Usos", width=80, anchor="w")

        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill="both", expand=True)

        botones = tk.Frame(cont, bg=C["bg"])
        botones.pack(fill="x", pady=(10, 0))

        tk.Button(botones, text="✏️ Renombrar", command=self._renombrar,
                 bg=C["button"], fg=C["white"], relief="flat", padx=10
                 ).pack(side="left", padx=(0, 6))
        tk.Button(botones, text="🎨 Color", command=self._cambiar_color,
                 bg=C["button"], fg=C["white"], relief="flat", padx=10
                 ).pack(side="left", padx=(0, 6))
        tk.Button(botones, text="🔀 Fusionar con...", command=self._fusionar,
                 bg=C["button"], fg=C["white"], relief="flat", padx=10
                 ).pack(side="left", padx=(0, 6))
        tk.Button(botones, text="🗑️ Eliminar", command=self._eliminar,
                 bg=C["delete"], fg=C["white"], relief="flat", padx=10
                 ).pack(side="left")

        tk.Button(cont, text="Cerrar", command=self.destroy,
                 bg=C["border"], fg=C["white"], relief="flat", padx=14
                 ).pack(anchor="e", pady=(10, 0))

    # ---------- Render ----------

    def _render(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conteo = self.tags_manager.conteo_uso(self.queries_manager)
        for t in self.tags_manager.obtener_todos():
            usos = conteo.get(t["clave"], 0)
            self.tree.insert("", "end", iid=t["clave"], values=(t["display"], usos))

    def _seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecciona un tag", "Elige un tag de la lista primero.")
            return None
        clave = sel[0]
        return self.tags_manager.display_de(clave)

    def _refrescar_todo(self):
        self._render()
        if self.on_changed:
            self.on_changed()

    # ---------- Acciones ----------

    def _renombrar(self):
        actual = self._seleccion()
        if not actual:
            return
        nuevo = simpledialog.askstring("Renombrar tag", f"Nuevo nombre para '{actual}':",
                                       initialvalue=actual, parent=self)
        if nuevo and nuevo.strip() and nuevo.strip() != actual:
            self.tags_manager.renombrar(actual, nuevo.strip(), self.queries_manager)
            self._refrescar_todo()

    def _cambiar_color(self):
        actual = self._seleccion()
        if not actual:
            return
        color_actual = self.tags_manager.color_de(actual)
        resultado = colorchooser.askcolor(color=color_actual, parent=self, title=f"Color para '{actual}'")
        if resultado and resultado[1]:
            self.tags_manager.set_color(actual, resultado[1])
            self._refrescar_todo()

    def _fusionar(self):
        actual = self._seleccion()
        if not actual:
            return
        destino = simpledialog.askstring(
            "Fusionar tag",
            f"¿Fusionar '{actual}' con qué otro tag?\n"
            f"(las queries de '{actual}' pasarán a usar el tag destino)",
            parent=self
        )
        if destino and destino.strip() and destino.strip().lower() != actual.lower():
            self.tags_manager.fusionar(actual, destino.strip(), self.queries_manager)
            self._refrescar_todo()

    def _eliminar(self):
        actual = self._seleccion()
        if not actual:
            return
        conteo = self.tags_manager.conteo_uso(self.queries_manager)
        clave = self.tags_manager.normalizar(actual)
        usos = conteo.get(clave, 0)
        if messagebox.askyesno(
            "Eliminar tag",
            f"¿Eliminar el tag '{actual}'? Se quitará de {usos} query(s)."
        ):
            self.tags_manager.eliminar(actual, self.queries_manager)
            self._refrescar_todo()
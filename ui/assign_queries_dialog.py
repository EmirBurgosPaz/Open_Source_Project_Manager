"""
ui/assign_queries_dialog.py

Diálogo modal para asignar queries existentes a un documento.
Mismo espíritu visual que EditDocumentDialog / TagsAdminDialog:
una lista de checkboxes (una por query) más buscador simple.
"""

import tkinter as tk
from tkinter import ttk
from config import C
from utils.ui_helpers import add_hover, lighten


class AssignQueriesDialog(tk.Toplevel):
    """
    Permite marcar/desmarcar qué queries están asociadas a un documento.

    Uso:
        AssignQueriesDialog(
            master, doc, queries_manager,
            on_save=lambda query_ids: ...
        )
    """

    def __init__(self, master, doc, queries_manager, on_save):
        super().__init__(master)
        self.doc = doc
        self.queries_manager = queries_manager
        self.on_save = on_save

        self.title(f"Asignar queries: {doc.nombre_documento}")
        self.configure(bg=C["bg"])
        self.resizable(False, True)
        self.transient(master)
        self.grab_set()

        seleccionadas = set(doc.query_ids or [])
        self._vars = {}  # query_id -> tk.BooleanVar

        # ── Buscador ─────────────────────────────────────────────
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(top, text="🔍 Buscar query:", bg=C["bg"], fg=C["white"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        self.entry_buscar = tk.Entry(
            top, bg=C["panel"], fg=C["white"], insertbackground=C["white"],
            relief="flat", width=30, bd=0,
            highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["accent"],
        )
        self.entry_buscar.pack(side="left", padx=(8, 0), ipady=3, fill="x", expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._filtrar_lista())

        # ── Lista con scroll ─────────────────────────────────────
        list_container = tk.Frame(self, bg=C["bg"], highlightthickness=1,
                                   highlightbackground=C["border"], highlightcolor=C["border"])
        list_container.pack(fill="both", expand=True, padx=10, pady=6)

        canvas = tk.Canvas(list_container, bg=C["panel"], highlightthickness=0,
                            width=340, height=280)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.checks_frame = tk.Frame(canvas, bg=C["panel"])

        self.checks_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.checks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._all_queries = list(self.queries_manager.queries)
        for q in sorted(self._all_queries, key=lambda x: x["nombre"].lower()):
            var = tk.BooleanVar(value=q["id"] in seleccionadas)
            self._vars[q["id"]] = var
            self._crear_fila(q, var)

        # ── Botones ──────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        cancel_btn = tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                                bg=C["bg"], fg=C["white"], relief="flat")
        cancel_btn.pack(side="right", padx=(6, 0))

        save_btn = tk.Button(btn_frame, text="Guardar", command=self._save,
                              bg=C["button"], fg=C["white"], relief="flat")
        add_hover(save_btn, lighten(C["accent"], 0.25), C["button"])
        save_btn.pack(side="right")

    def _crear_fila(self, q, var):
        fila = tk.Frame(self.checks_frame, bg=C["panel"])
        fila.pack(fill="x", padx=6, pady=2)
        fila._query_nombre = q["nombre"].lower()  # para el filtro de búsqueda

        chk = tk.Checkbutton(
            fila, text=q["nombre"], variable=var,
            bg=C["panel"], fg=C["white"], selectcolor=C["bg"],
            activebackground=C["panel"], activeforeground=C["white"],
            anchor="w", font=("Segoe UI", 9)
        )
        chk.pack(side="left", fill="x", expand=True)

        if q.get("categoria"):
            tk.Label(fila, text=q["categoria"], bg=C["panel"], fg=C["border"],
                      font=("Segoe UI", 8)).pack(side="right", padx=(0, 6))

    def _filtrar_lista(self):
        texto = self.entry_buscar.get().strip().lower()
        for fila in self.checks_frame.winfo_children():
            visible = texto in getattr(fila, "_query_nombre", "")
            if visible:
                fila.pack(fill="x", padx=6, pady=2)
            else:
                fila.pack_forget()

    def _save(self):
        seleccionadas = [qid for qid, var in self._vars.items() if var.get()]
        self.on_save(seleccionadas)
        self.destroy()
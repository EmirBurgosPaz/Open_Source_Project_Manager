"""
ui/notas_list.py — Panel de lista de Notas (Treeview), tema oscuro,
siguiendo el mismo patrón que el panel Documents_list.
"""

import tkinter as tk
from tkinter import ttk

from config import C
from services.notas_service import NotasService
from ui.notas_dialog import NotaDialog
from utils.ui_helpers import setup_treeview_style, make_entry, setup_treeview_hover


class NotasListFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])
        self.service = NotasService()

        # Estado de filtros — inicializado ANTES de _build_ui() para que
        # render() no falle si algo lo dispara durante la construcción.
        self._filtro_texto = ""
        self._filtro_tag = None

        self._build_ui()
        self.render()

    # ── UI ───────────────────────────────────────────────────────────
    def _build_ui(self):
        header = tk.Frame(self, bg=C["bg"])
        header.pack(fill="x", padx=10, pady=(10, 6))

        nuevo_btn = tk.Label(header, text="+ Nueva", bg=C["accent"], fg="white",
                              font=("Helvetica", 10, "bold"), padx=10, pady=4,
                              cursor="hand2")
        nuevo_btn.pack(side="right")
        nuevo_btn.bind("<Button-1>", lambda e: self._nueva_nota())


        tk.Label(
                    header, text="🔍 Buscar:", bg=C["panel"], fg=C["white"],
                    font=("Segoe UI", 9, "bold")
                ).pack(side="left")

        buscador = tk.Entry(
            header, bg=C["bg"], fg=C["white"],
            insertbackground=C["white"], relief="flat", width=32,
            highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["accent"],
            bd=0
        )
        buscador.pack(fill="x", padx=10, pady=(0, 8))
        self.busqueda_entry = make_entry(buscador)
        self.busqueda_entry.pack(fill="x")
        self.busqueda_entry.bind("<KeyRelease>", self._on_buscar)

        style_name = setup_treeview_style("Notas.Treeview")
        cols = ("titulo", "tags", "fecha")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  style=style_name, selectmode="browse")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("tags", text="Tags")
        self.tree.heading("fecha", text="Modificado")
        self.tree.column("titulo", width=220, anchor="w")
        self.tree.column("tags", width=140, anchor="w")
        self.tree.column("fecha", width=130, anchor="center")

        self.tree.tag_configure("odd", background=C["bg"])
        self.tree.tag_configure("even", background=C["row_alt"])
        self.tree.tag_configure("hover", background=C["hover"])

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", self._on_doble_click)
        setup_treeview_hover(self.tree)

    # ── Render ───────────────────────────────────────────────────────
    def render(self):
        self.tree.delete(*self.tree.get_children())
        notas = self.service.buscar(self._filtro_texto, self._filtro_tag)
        for i, nota in enumerate(notas):
            fecha = nota.fecha_modificacion[:10]
            tags_txt = ", ".join(nota.tags)
            tag_fila = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end",tags=(tag_fila,), iid=nota.id,
                              values=(nota.titulo or "(sin título)", tags_txt, fecha))

    def set_filtro_tag(self, tag: str = None):
        self._filtro_tag = tag
        self.render()

    # ── Eventos ──────────────────────────────────────────────────────
    def _on_buscar(self, event=None):
        self._filtro_texto = self.busqueda_entry.get()
        self.render()

    def _on_doble_click(self, event):
        sel = self.tree.selection()
        if sel:
            NotaDialog(self, nota_id=sel[0], on_guardado=self.render)

    def _nueva_nota(self):
        nota = self.service.crear()
        self.render()
        if nota:
            NotaDialog(self, nota_id=nota.id, on_guardado=self.render)
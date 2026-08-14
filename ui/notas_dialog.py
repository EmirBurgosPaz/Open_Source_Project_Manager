"""
ui/notas_dialog.py — Diálogo de creación/edición de una Nota (texto enriquecido).
"""

import tkinter as tk

from config import C
from services.notas_service import NotasService
from utils.ui_helpers import make_label, make_entry, center_window, add_hover, lighten
from utils.rich_text import RichTextEditor


class NotaDialog(tk.Toplevel):
    def __init__(self, parent, nota_id: str = None, on_guardado=None):
        super().__init__(parent)
        self.service = NotasService()
        self.nota = self.service.obtener(nota_id) if nota_id else self.service.crear()
        self.on_guardado = on_guardado

        self.title("Nota")
        self.configure(bg=C["dlg_bg"])
        self.geometry("800x620")
        self.minsize(560, 520)
        center_window(self, parent)
        self._build_ui()
        self.update_idletasks()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        cont = tk.Frame(self, bg=C["dlg_bg"], padx=16, pady=16)
        cont.pack(fill="both", expand=True)

        make_label(cont, "Título").pack(anchor="w")
        self.titulo_entry = make_entry(cont, value=self.nota.titulo)
        self.titulo_entry.pack(fill="x", pady=(0, 10))
        self.titulo_entry.focus()

        make_label(cont, "Tags (separados por coma)").pack(anchor="w")
        self.tags_entry = make_entry(cont, value=", ".join(self.nota.tags))
        self.tags_entry.pack(fill="x", pady=(0, 10))

        make_label(cont, "Contenido").pack(anchor="w")
        self.editor = RichTextEditor(cont, altura=16)
        self.editor.pack(fill="both", expand=True, pady=(6, 10))
        self.editor.set_contenido(self.nota.contenido)

        botones = tk.Frame(cont, bg=C["dlg_bg"])
        botones.pack(fill="x")

        save_btn = tk.Label(botones, text="Guardar", bg=C["button"], fg=C["white"],
                                font=("Helvetica", 10, "bold"), padx=14, pady=6,
                                cursor="hand2")
        save_btn.pack(side="right")
        add_hover(save_btn , lighten(C["accent"], 0.25), C["button"])
        save_btn.bind("<Button-1>", lambda e: self._guardar())

        delete_btn = tk.Label(botones, text="Eliminar", bg=C["delete"], fg=C["white"],
                                 font=("Helvetica", 10), padx=14, pady=6,
                                 cursor="hand2")
        delete_btn.pack(side="right", padx=(0, 8))
        add_hover(delete_btn , lighten(C["delete"], 0.25), C["delete"])
        delete_btn.bind("<Button-1>", lambda e: self._eliminar())

    def _guardar(self):
        self.nota.titulo = self.titulo_entry.get().strip()
        self.nota.tags = [t.strip() for t in self.tags_entry.get().split(",") if t.strip()]
        self.nota.contenido = self.editor.get_contenido()
        self.service.actualizar(self.nota)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()

    def _eliminar(self):
        self.service.eliminar(self.nota.id)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()
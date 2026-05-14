"""
ui/members_dialog.py — Diálogo para gestionar miembros con edición por doble clic.
"""

import tkinter as tk
from config import C, KEYBOARD_KEYS
from utils.ui_helpers import center_window


class MembersDialog(tk.Toplevel):
    def __init__(self, parent, members: list[dict]):
        super().__init__(parent)
        self.title("Equipo")
        self.minsize(500, 450)
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()
        
        # Normalizar datos de entrada
        self.members = [
            m.copy() if isinstance(m, dict) else {"name": str(m), "pos": "", "team": ""} 
            for m in members
        ]

        self._build()
        self.focus()

        self.bind(KEYBOARD_KEYS["enter"], self._add_member)
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)
        
        center_window(self, parent)

    def _build(self):
        bg = C["dlg_bg"]

        # Encabezado
        header_frame = tk.Frame(self, bg=bg)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))
        
        tk.Label(header_frame, text="Miembros del Equipo", bg=bg, fg=C["text"],
                 font=("Helvetica", 14, "bold")).pack(side="left")
        
        tk.Label(self, text="Tip: Doble clic en un campo para editarlo", 
                 bg=bg, fg=C["muted"], font=("Helvetica", 8, "italic")).pack(anchor="w", padx=16)

        # Títulos de Columnas (Simulación de Tabla)
        cols_header = tk.Frame(self, bg=bg)
        cols_header.pack(fill="x", padx=16, pady=(10, 0))
        for text, weight in [("Nombre", 3), ("Posición", 3), ("Equipo", 2)]:
            lbl = tk.Label(cols_header, text=text, bg=bg, fg=C["muted"], 
                           font=("Helvetica", 9, "bold"), anchor="w")
            lbl.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(cols_header, text="", width=4, bg=bg).pack(side="right") # Espacio para el botón X

        # Área de Lista
        self.rows_frame = tk.Frame(self, bg=bg)
        self.rows_frame.pack(fill="both", expand=True, padx=16, pady=5)
        
        self._render_rows()

        # Formulario de entrada
        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(10, 0))
        form_frame = tk.Frame(self, bg=bg)
        form_frame.pack(fill="x", padx=16, pady=20)
        
        # Layout de inputs
        for i in range(3): form_frame.columnconfigure(i, weight=1)

        self.e_name = self._create_add_input(form_frame, "Nombre", 0)
        self.e_pos = self._create_add_input(form_frame, "Posición", 1)
        self.e_team = self._create_add_input(form_frame, "Equipo", 2)

        tk.Button(form_frame, text="+ Agregar Miembro", bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  pady=6, cursor="hand2", command=self._add_member).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    def _create_add_input(self, parent, placeholder, col):
        f = tk.Frame(parent, bg=C["dlg_border"], padx=1, pady=1)
        f.grid(row=0, column=col, padx=3, sticky="ew")
        e = tk.Entry(f, font=("Helvetica", 10), bg=C["dlg_input"], fg=C["text"],
                     insertbackground=C["text"], relief="flat", bd=0, justify="center")
        e.insert(0, placeholder)
        e.bind("<FocusIn>", lambda _: e.delete(0, "end") if e.get() == placeholder else None)
        e.bind("<FocusOut>", lambda _: e.insert(0, placeholder) if not e.get() else None)
        e.pack(fill="x", ipady=3)
        return e

    def _render_rows(self):
        for w in self.rows_frame.winfo_children(): w.destroy()

        for i, m in enumerate(self.members):
            row = tk.Frame(self.rows_frame, bg=C["dlg_input"], pady=2)
            row.pack(fill="x", pady=2)

            # Crear campos editables
            self._create_editable_cell(row, m, "name", i, expand_weight=3)
            self._create_editable_cell(row, m, "pos", i, expand_weight=3)
            self._create_editable_cell(row, m, "team", i, expand_weight=2)

            # Botón eliminar
            tk.Button(row, text="✕", bg=C["dlg_input"], fg="#ff5555", font=("Helvetica", 10),
                      relief="flat", bd=0, cursor="hand2", command=lambda _idx=i: self._remove(_idx)).pack(side="right", padx=10)

    def _create_editable_cell(self, parent, member_dict, key, member_idx, expand_weight):
        cell_frame = tk.Frame(parent, bg=C["dlg_input"])
        cell_frame.pack(side="left", expand=True, fill="x", padx=5)
        
        val = member_dict[key] or "---"
        lbl = tk.Label(cell_frame, text=val, bg=C["dlg_input"], fg=C["text"],
                       font=("Helvetica", 9), anchor="w", pady=4)
        lbl.pack(fill="x")

        def on_double_click(event):
            lbl.pack_forget()
            edit_entry = tk.Entry(cell_frame, font=("Helvetica", 9), bg=C["dlg_bg"], 
                                  fg=C["text"], relief="flat", highlightthickness=1,
                                  highlightbackground=C["accent"])
            edit_entry.insert(0, member_dict[key])
            edit_entry.pack(fill="x")
            edit_entry.focus_set()

            def save_edit(event=None):
                # Desvincular el evento global para evitar errores al destruir el widget
                self.unbind_all("<Button-1>")
                new_val = edit_entry.get().strip()
                self.members[member_idx][key] = new_val
                edit_entry.destroy()
                self._render_rows()

            def check_click_outside(event):
                # Si el widget que recibió el clic NO es el entry de edición, guardar y cerrar
                if event.widget != edit_entry:
                    save_edit()

            # Vincular eventos de cierre/guardado
            edit_entry.bind("<Return>", save_edit)
            # El bind_all captura clics en cualquier parte de la aplicación
            self.bind_all("<Button-1>", check_click_outside)

        lbl.bind("<Double-Button-1>", on_double_click)

    def _add_member(self, event=None):
        n, p, t = self.e_name.get(), self.e_pos.get(), self.e_team.get()
        if n and n != "Nombre":
            self.members.append({
                "name": n,
                "pos": p if p != "Posición" else "",
                "team": t if t != "Equipo" else ""
            })
            # Resetear formulario
            for e, ph in [(self.e_name, "Nombre"), (self.e_pos, "Posición"), (self.e_team, "Equipo")]:
                e.delete(0, "end")
                e.insert(0, ph)
            self._render_rows()

    def _remove(self, idx: int):
        self.members.pop(idx)
        self._render_rows()

    def _on_close(self,event = None):
        self.destroy()
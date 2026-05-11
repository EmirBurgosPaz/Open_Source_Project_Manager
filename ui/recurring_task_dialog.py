import tkinter as tk
from config import C, FREQUENCY_OPTIONS, STATUS_OPTIONS, CATEGORY_OPTIONS, PRIORITY_OPTIONS
from utils.ui_helpers import make_label
from utils.ui_helpers import make_entry
from utils.ui_helpers import make_dark_combobox
from utils.ui_helpers import center_window




class RecurringTaskDialog(tk.Toplevel):
    def __init__(self, parent, task=None):
        super().__init__(parent)
        self.result = None
        self.title("Editar tarea" if task else "Nueva tarea recurrente")
        self.resizable(False, False)
        self.configure(bg=C["dlg_bg"])
        self.grab_set()
        self._build(task)
        center_window(self, parent)

    def _build(self, task):
        bg = C["dlg_bg"]

        make_label(self, "Categoría").pack(anchor="w", padx=16, pady=(12, 2))
        self.category_var, category_cb = make_dark_combobox(
            self, CATEGORY_OPTIONS , task.category if task else "Manual"
        )
        category_cb.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Tarea").pack(anchor="w", padx=16, pady=(8, 2))
        self.e_title = make_entry(self, task.title if task else "")
        self.e_title.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Frecuencia").pack(anchor="w", padx=16, pady=(8, 2))
        self.freq_var, freq_cb = make_dark_combobox(
            self, FREQUENCY_OPTIONS, task.frequency if task else "Semanal"
        )
        freq_cb.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Status").pack(anchor="w", padx=16, pady=(8, 2))
        self.status_var, status_cb = make_dark_combobox(
            self, STATUS_OPTIONS, task.status if task else "CFM"
        )
        status_cb.pack(fill="x", padx=16, pady=(0, 2))

        make_label(self, "Prioridad").pack(anchor="w", padx=16, pady=(8, 2))
        self.prio_var, prio_cb = make_dark_combobox(
            self, PRIORITY_OPTIONS , str(task.priority) if task else "Media")
        prio_cb.pack(fill="x", padx=16, pady=(0, 2))

        tk.Frame(self, bg=C["dlg_border"], height=1).pack(fill="x", pady=(12, 0))

        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        if task:
            tk.Button(btn_row, text="Eliminar",
                      bg="#3A1A1A", fg="#E05555",
                      font=("Helvetica", 10), relief="flat", bd=0,
                      padx=10, pady=5, cursor="hand2",
                      command=self._on_delete).pack(side="left")

        tk.Button(btn_row, text="Cancelar",
                  bg=C["panel"], fg=C["muted"],
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=5, cursor="hand2",
                  command=self.destroy).pack(side="right", padx=(6, 0))

        tk.Button(btn_row, text="Guardar" if task else "Crear",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._on_save).pack(side="right")

    def _on_save(self):
        title = self.e_title.get().strip()
        if not title:
            from tkinter import messagebox
            messagebox.showwarning("Campo vacío", "El nombre no puede estar vacío.", parent=self)
            return
        self.result = {
            "title":     title,
            "category":  self.category_var.get(),
            "frequency": self.freq_var.get(),
            "status":    self.status_var.get(),
            "priority":  self.prio_var.get(),
        }
        self.destroy()

    def _on_delete(self):
        self.result = {"deleted": True}
        self.destroy()
    
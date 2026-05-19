"""
ui/filter_bar.py — Barra de filtros dinámicos sobre la lista de tareas.
"""
import tkinter as tk
from tkinter import ttk
from config import C, COLUMNS_STATUS, PRIORITY_OPTIONS
import config


class FilterBar(tk.Frame):
    """
    Llama on_filter(filters) cada vez que cambia algún filtro.
    filters es un dict: {"status": str, "priority": str, "assign": str, "search": str}
    """

    def __init__(self, parent, on_filter):
        super().__init__(parent, bg=C["panel"])
        self.on_filter = on_filter
        self._build()
        self.after(10, self._on_change)
        

    def _build(self):
        # Búsqueda por texto
        tk.Label(self, text="Tarea", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 11)).pack(side="left", padx=(12, 2), pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_change)
        e = tk.Entry(self, textvariable=self.search_var,
                 font=("Helvetica", 10),
                 bg=C["dlg_input"], fg=C["text"],
                 insertbackground=C["bg"],
                 relief="flat", bd=0,
                 highlightthickness=1,
                 highlightbackground=C["dlg_border"],
                 highlightcolor=C["bg"],
                 width=20)
        e.pack(side="left", padx=(0, 12), pady=8, ipady=3)

        # Separador
        tk.Label(self, text="Cliente", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 11)).pack(side="left", padx=(12, 2), pady=8)

        self.client_var = tk.StringVar()
        self.client_var.trace_add("write", self._on_change)
        e = tk.Entry(self, textvariable=self.client_var,
                 font=("Helvetica", 10),
                 bg=C["dlg_input"], fg=C["text"],
                 insertbackground=C["bg"],
                 relief="flat", bd=0,
                 highlightthickness=1,
                 highlightbackground=C["dlg_border"],
                 highlightcolor=C["bg"],
                 width=20)
        e.pack(side="left", padx=(0, 12), pady=8, ipady=3)


        tk.Frame(self, bg=C["border"], width=1).pack(side="left", fill="y", pady=6)

        # Filtro Estado
        tk.Label(self, text="Estado", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left", padx=(12, 4))
                 
        # 1. Agregamos "Activas" al principio de la lista
        status_opts = ["Activas", "Todos"] + [c[1] for c in COLUMNS_STATUS]
        
        # 2. Lo ponemos como el valor por defecto
        self.status_var = tk.StringVar(value="Activas")
        
        self.status_var.trace_add("write", self._on_change)
        self._combo(status_opts, self.status_var).pack(side="left", padx=(0, 12))

        # Filtro Prioridad
        tk.Label(self, text="Prioridad", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left", padx=(0, 4))
        prio_opts = ["Todas"] + PRIORITY_OPTIONS
        self.prio_var = tk.StringVar(value="Todas")
        self.prio_var.trace_add("write", self._on_change)
        self._combo(prio_opts, self.prio_var).pack(side="left", padx=(0, 12))

        # Filtro Asignado
        tk.Label(self, text="Asignado", bg=C["panel"], fg=C["muted"],
                 font=("Helvetica", 9)).pack(side="left", padx=(0, 4))
        self.assign_var = tk.StringVar(value="Todos")
        self.assign_var.trace_add("write", self._on_change)
        self._assign_cb = self._combo(["Todos"], self.assign_var)
        self._assign_cb.pack(side="left", padx=(0, 12))

        # Botón limpiar
        tk.Button(self, text="✕ Limpiar",
                        bg=C["hover"], fg=C["muted"],
                        font=("Helvetica", 9), relief="flat", bd=0,
                        padx=8, pady=3, cursor="hand2",
                        activebackground=C["hover"],
                        activeforeground=C["panel"],
                        command=self.clear).pack(side="right", padx=12)

    def _combo(self, values, var):
        style = ttk.Style()
        
        # 1. FORZAR UN TEMA PERMISIVO
        # El tema 'clam' permite modificar los fondos en todos los sistemas operativos.
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # 2. CONFIGURAR LA CAJA PRINCIPAL
        style.configure("Filter.TCombobox",
                        fieldbackground=C["dlg_input"],
                        background=C["panel"], # Fondo exterior
                        foreground=C["text"],
                        arrowcolor=C["text"],  # Color de la flechita
                        bordercolor=C["dlg_border"],
                        lightcolor=C["panel"],
                        darkcolor=C["panel"],
                        selectbackground=C["accent"], # Resalte al seleccionarlo
                        selectforeground=C["text"],
                        padding=(6, 4))
                        
        style.map("Filter.TCombobox",
                  fieldbackground=[("readonly", C["dlg_input"]),
                                   ("focus",    C["accent"])],
                  foreground=[("readonly", C["text"])],
                  bordercolor=[("focus",   C["accent"]), # Brilla con el color acento
                               ("!focus",  C["dlg_border"])])

        # 3. EL TRUCO PARA EL MENÚ DESPLEGABLE
        # Le decimos a Tkinter globalmente que pinte las listas de los Combobox
        self.option_add("*TCombobox*Listbox.background", C["dlg_input"])
        self.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", C["text"])
        self.option_add("*TCombobox*Listbox.font", ("Helvetica", 9))

        cb = ttk.Combobox(self, textvariable=var, values=values,
                          state="readonly", font=("Helvetica", 9),
                          style="Filter.TCombobox", width=12)
        return cb

    def refresh_members(self):
        """Actualiza el combo de asignados con los miembros actuales."""
        members = ["Todos"] + [m["name"] for m in config.MEMBERS]
        self._assign_cb["values"] = members
        if self.assign_var.get() not in members:
            self.assign_var.set("Todos")

    def clear(self):
        self.client_var.set("")
        self.search_var.set("")
        self.status_var.set("Activas")
        self.prio_var.set("Todas")
        self.assign_var.set("Todos")

    def _on_change(self, *args):
        self.on_filter({
            "client":   self.client_var.get().strip().lower(),
            "search":   self.search_var.get().strip().lower(),
            "status":   self.status_var.get(),
            "priority": self.prio_var.get(),
            "assign":   self.assign_var.get(),
        })

    def get_filters(self) -> dict:
        return {
            "search":   self.search_var.get().strip().lower(),
            "status":   self.status_var.get(),
            "priority": self.prio_var.get(),
            "assign":   self.assign_var.get(),
        }
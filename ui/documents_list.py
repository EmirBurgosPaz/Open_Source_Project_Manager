import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config import C,KEYBOARD_KEYS
from utils.ui_helpers import setup_treeview_style, add_hover, lighten, setup_treeview_hover
from datetime import date
import subprocess
import platform
import os


class Documents_list(ttk.Frame):
    def __init__(self, master, document_service, **kwargs):
        super().__init__(master, **kwargs)
        self.service = document_service
        self._last_sort = None
        self._build_ui()
        self.service.refresh_all_mtimes()
        self._populate()


    def _build_ui(self):
        style = ttk.Style()
        style.configure("Documents.TFrame", background=C["bg"])
        self.configure(style="Documents.TFrame")

        toolbar = tk.Frame(self, bg=C["bg"])
        toolbar.pack(fill="x", padx=6, pady=(6, 4))

        add_btn = tk.Button(toolbar, text="+ Agregar archivo", command=self._on_add_file,
                  bg=C["button"], fg=C["white"], relief="flat")
        add_hover(add_btn , lighten(C["accent"], 0.25), C["button"])
        add_btn.pack(side="right")

        columns = ("nombre", "activo", "Fecha_update", "pertenece")

        style_name = setup_treeview_style()

        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", style=style_name)
        self.tree.heading("nombre", text="Documento", command=lambda: self._sort_by("nombre", False))
        self.tree.heading("activo", text="Activo", command=lambda: self._sort_by("activo", False))
        self.tree.heading("Fecha_update", text="Última modificación", command=lambda: self._sort_by("Fecha_update", False))
        self.tree.heading("pertenece", text="Pertenece", command=lambda: self._sort_by("pertenece", False))
        self.tree.column("nombre", width=160, anchor="w")
        self.tree.column("activo", width=20, anchor="center")
        self.tree.column("Fecha_update", width=80, anchor="center")
        self.tree.column("pertenece", width=100, anchor="w")
        self._sort_state = {} 
        self.tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind(KEYBOARD_KEYS["supr"], self._on_supr_click)

        # Configurar tags para colores alternos
        self.tree.tag_configure("odd", background=C["bg"])
        self.tree.tag_configure("even", background=C["row_alt"])
        self.tree.tag_configure("hover", background=C["hover"])

        setup_treeview_hover(self.tree)

    def _populate(self):
        i = 0
        self.tree.delete(*self.tree.get_children())
        for doc in self.service.get_all():
            i = i + 1
            estado = "☑" if doc.activo else "☐"
            self.tree.insert("", "end",tags=("even" if i % 2 == 0 else "odd",), iid=doc.ruta_documento,
                              values=(doc.nombre_documento,  estado, doc.fecha_modificacion, doc.pertenece))

        if self._last_sort:
            col, reverse = self._last_sort
            self._sort_by(col, reverse, remember=False)

    def _on_add_file(self):
        ruta = filedialog.askopenfilename(title="Seleccionar documento")
        if not ruta:
            return
        self.service.add_document(ruta)
        self._populate()

    def _on_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return

        col_index = int(col.replace("#", "")) - 1
        col_name = self.tree["columns"][col_index]

        if col_name == "activo":
            self.service.toggle_activo(row)
            self._populate()

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0, bg=C["bg"], fg=C["white"])
        menu.add_command(label="Eliminar", command=lambda: self._on_delete(row))
        menu.add_command(label="Abrir ubicación", command=lambda: self._on_open_location(row))
        menu.tk_popup(event.x_root, event.y_root)

    def _on_supr_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        self._on_delete(row)

    def _on_delete(self, ruta):
        if messagebox.askyesno("Confirmar", "¿Eliminar este documento de la lista?"):
            self.service.remove_document(ruta)
            self._populate()    

    def render(self, documents=None):
        # si tu método interno ya lee del service, no necesita el argumento
        self._populate()  # reemplaza "_populate" por el nombre real de tu método interno

    def _sort_by(self, col, reverse,  remember=True):
        items = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children("")]

        if col == "activo":
            # ordenar por booleano real, no por el símbolo ☑/☐
            items = [(self.tree.set(iid, col) == "☑", iid) for iid in self.tree.get_children("")]
        elif col == "Fecha_update":
            # si fecha_modificacion es date/datetime, mejor ordenar por el objeto original
            docs = {doc.ruta_documento: doc for doc in self.service.get_all()}
            items = [(docs[iid].fecha_modificacion, iid) for iid in self.tree.get_children("")]
        else:
            items = [(self.tree.set(iid, col).lower(), iid) for iid in self.tree.get_children("")]

        items.sort(key=lambda x: x[0], reverse=reverse)

        for index, (_, iid) in enumerate(items):
            self.tree.move(iid, "", index)

        # actualizar flecha visual y alternar orden para el próximo clic
        for c in self.tree["columns"]:
            text = self.tree.heading(c, "text").rstrip(" ▲▼")
            self.tree.heading(c, text=text)

        arrow = " ▼" if reverse else " ▲"
        current_text = self.tree.heading(col, "text").rstrip(" ▲▼")
        self.tree.heading(col, text=current_text + arrow,
                           command=lambda: self._sort_by(col, not reverse))

        if remember:
            self._last_sort = (col, reverse)
    def _on_open_location(self, ruta):
        if not os.path.exists(ruta):
            messagebox.showerror("Error", "El archivo ya no existe en esa ubicación.")
            return

        sistema = platform.system()
        try:
            if sistema == "Windows":
                # abre el explorador y selecciona el archivo
                subprocess.run(["explorer", "/select,", os.path.normpath(ruta)])
            elif sistema == "Darwin":  # macOS
                subprocess.run(["open", "-R", ruta])
            else:  # Linux
                carpeta = os.path.dirname(ruta)
                subprocess.run(["xdg-open", carpeta])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la ubicación:\n{e}")
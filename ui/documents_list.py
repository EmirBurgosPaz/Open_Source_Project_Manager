import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config import C


class Documents_list(ttk.Frame):
    def __init__(self, master, document_service, **kwargs):
        super().__init__(master, **kwargs)
        self.service = document_service
        self._build_ui()
        self._populate()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Documents.TFrame", background=C["bg"])
        self.configure(style="Documents.TFrame")

        toolbar = tk.Frame(self, bg=C["bg"])
        toolbar.pack(fill="x", padx=6, pady=(6, 4))

        tk.Button(toolbar, text="+ Agregar archivo", command=self._on_add_file,
                  bg=C["accent"], fg=C["white"], relief="flat").pack(side="left")

        tk.Button(toolbar, text="Actualizar fechas", command=self._on_refresh_mtimes,
                  bg=C["accent"], fg=C["white"], relief="flat").pack(side="left", padx=(6, 0))

        columns = ("nombre", "activo", "pertenece")

        style.configure("Documents.Treeview",
                         background=C["panel"],
                         foreground=C["text"],
                         fieldbackground=C["panel"],
                         borderwidth=0)
        style.configure("Documents.Treeview.Heading",
                         background=C["sidebar"],
                         foreground=C["text"])
        style.map("Documents.Treeview",
                  background=[("selected", C["accent"])])

        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", style="Documents.Treeview")
        self.tree.heading("nombre", text="Documento")
        self.tree.heading("activo", text="Activo")
        self.tree.heading("pertenece", text="Pertenece")
        self.tree.column("nombre", width=160, anchor="w")
        self.tree.column("activo", width=60, anchor="center")
        self.tree.column("pertenece", width=100, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Button-3>", self._on_right_click)

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        for doc in self.service.get_all():
            estado = "☑" if doc.activo else "☐"
            self.tree.insert("", "end", iid=doc.ruta_documento,
                              values=(doc.nombre_documento,  estado, doc.pertenece))

    def _on_add_file(self):
        ruta = filedialog.askopenfilename(title="Seleccionar documento")
        if not ruta:
            return
        self.service.add_document(ruta)
        self._populate()

    def _on_refresh_mtimes(self):
        cambiados = self.service.refresh_all_mtimes()
        self._populate()
        if cambiados:
            messagebox.showinfo("Documentos", f"{len(cambiados)} documento(s) actualizado(s).")

    def _on_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if row and col == "#3":  # columna "activo"
            self.service.toggle_activo(row)
            self._populate()

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0, bg=C["bg"], fg=C["white"])
        menu.add_command(label="Eliminar", command=lambda: self._on_delete(row))
        menu.tk_popup(event.x_root, event.y_root)

    def _on_delete(self, ruta):
        if messagebox.askyesno("Confirmar", "¿Eliminar este documento de la lista?"):
            self.service.remove_document(ruta)
            self._populate()    

    def render(self, documents=None):
        # si tu método interno ya lee del service, no necesita el argumento
        self._populate()  # reemplaza "_populate" por el nombre real de tu método interno
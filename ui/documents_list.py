import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config import C, KEYBOARD_KEYS
from utils.ui_helpers import setup_treeview_style, add_hover, lighten, setup_treeview_hover
from ui.assign_queries_dialog import AssignQueriesDialog
from datetime import date
import subprocess
import platform
import os


class EditDocumentDialog(tk.Toplevel):
    """Ventana modal para editar 'pertenece', 'descripcion' y 'fecha_documento' de un documento."""

    def __init__(self, master, doc, on_save):
        super().__init__(master)
        self.doc = doc
        self.on_save = on_save
        self.title(f"Editar: {doc.nombre_documento}")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        pad = {"padx": 10, "pady": (8, 2)}

        tk.Label(self, text="Pertenece a:", bg=C["bg"], fg=C["white"]).grid(
            row=0, column=0, sticky="w", **pad)
        self.pertenece_var = tk.StringVar(value=doc.pertenece)
        tk.Entry(self, textvariable=self.pertenece_var, width=40).grid(
            row=1, column=0, sticky="we", padx=10)

        tk.Label(self, text="Fecha (AAAA-MM-DD):", bg=C["bg"], fg=C["white"]).grid(
            row=2, column=0, sticky="w", **pad)
        self.fecha_var = tk.StringVar(value=doc.fecha_documento or date.today().isoformat())
        tk.Entry(self, textvariable=self.fecha_var, width=40).grid(
            row=3, column=0, sticky="we", padx=10)

        tk.Label(self, text="Descripción:", bg=C["bg"], fg=C["white"]).grid(
            row=4, column=0, sticky="w", **pad)
        self.descripcion_text = tk.Text(self, width=40, height=5, wrap="word")
        self.descripcion_text.insert("1.0", doc.descripcion or "")
        self.descripcion_text.grid(row=5, column=0, sticky="we", padx=10)

        btn_frame = tk.Frame(self, bg=C["bg"])
        btn_frame.grid(row=6, column=0, sticky="e", padx=10, pady=10)

        cancel_btn = tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                                bg=C["bg"], fg=C["white"], relief="flat")
        cancel_btn.pack(side="right", padx=(6, 0))

        save_btn = tk.Button(btn_frame, text="Guardar", command=self._save,
                              bg=C["button"], fg=C["white"], relief="flat")
        add_hover(save_btn, lighten(C["accent"], 0.25), C["button"])
        save_btn.pack(side="right")

    def _save(self):
        fecha = self.fecha_var.get().strip()
        if fecha:
            try:
                # valida formato AAAA-MM-DD
                y, m, d = fecha.split("-")
                date(int(y), int(m), int(d))
            except (ValueError, AttributeError):
                messagebox.showerror("Fecha inválida", "Usa el formato AAAA-MM-DD, por ejemplo 2025-01-31.")
                return

        pertenece = self.pertenece_var.get().strip()
        descripcion = self.descripcion_text.get("1.0", "end").strip()

        self.on_save(pertenece=pertenece, descripcion=descripcion, fecha_documento=fecha)
        self.destroy()


class Documents_list(ttk.Frame):
    def __init__(self, master, document_service, queries_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        self.service = document_service
        # queries_manager es opcional: si no se pasa, la columna "Queries"
        # simplemente queda vacía y el menú de asignación no aparece.
        self.queries_manager = queries_manager
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
        add_hover(add_btn, lighten(C["accent"], 0.25), C["button"])
        add_btn.pack(side="right")

        columns = ("nombre", "activo", "Fecha_update", "pertenece", "fecha_doc", "descripcion", "queries")

        style_name = setup_treeview_style()

        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", style=style_name)
        self.tree.heading("nombre", text="Documento", command=lambda: self._sort_by("nombre", False))
        self.tree.heading("activo", text="Activo", command=lambda: self._sort_by("activo", False))
        self.tree.heading("Fecha_update", text="Última modificación", command=lambda: self._sort_by("Fecha_update", False))
        self.tree.heading("pertenece", text="Pertenece", command=lambda: self._sort_by("pertenece", False))
        self.tree.heading("fecha_doc", text="Fecha", command=lambda: self._sort_by("fecha_doc", False))
        self.tree.heading("descripcion", text="Descripción", command=lambda: self._sort_by("descripcion", False))
        self.tree.heading("queries", text="Queries", command=lambda: self._sort_by("queries", False))
        self.tree.column("nombre", width=150, anchor="w")
        self.tree.column("activo", width=20, anchor="center")
        self.tree.column("Fecha_update", width=80, anchor="center")
        self.tree.column("pertenece", width=90, anchor="w")
        self.tree.column("fecha_doc", width=80, anchor="center")
        self.tree.column("descripcion", width=160, anchor="w")
        self.tree.column("queries", width=180, anchor="w")
        self._sort_state = {}
        self.tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind(KEYBOARD_KEYS["supr"], self._on_supr_click)

        # Configurar tags para colores alternos
        self.tree.tag_configure("odd", background=C["bg"])
        self.tree.tag_configure("even", background=C["row_alt"])
        self.tree.tag_configure("hover", background=C["hover"])

        setup_treeview_hover(self.tree)

    def _nombres_queries_de(self, doc) -> str:
        """Texto 'tag1, tag2' con los nombres de las queries asignadas a este documento."""
        if not self.queries_manager:
            return ""
        nombres = self.service.obtener_nombres_queries(doc.ruta_documento, self.queries_manager)
        return ", ".join(nombres)

    def _populate(self):
        i = 0
        self.tree.delete(*self.tree.get_children())
        for doc in self.service.get_all():
            i = i + 1
            estado = "☑" if doc.activo else "☐"
            self.tree.insert("", "end", tags=("even" if i % 2 == 0 else "odd",), iid=doc.ruta_documento,
                              values=(doc.nombre_documento, estado, doc.fecha_modificacion,
                                      doc.pertenece, doc.fecha_documento, doc.descripcion,
                                      self._nombres_queries_de(doc)))

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

    def _on_double_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return

        col = self.tree.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1
        col_name = self.tree["columns"][col_index]

        if col_name == "queries":
            self._open_assign_queries_dialog(row)
        else:
            self._open_edit_dialog(row)

    def _open_edit_dialog(self, ruta):
        doc = next((d for d in self.service.get_all() if d.ruta_documento == ruta), None)
        if doc is None:
            return

        def guardar(pertenece, descripcion, fecha_documento):
            self.service.edit_document(ruta, pertenece=pertenece, descripcion=descripcion,
                                        fecha_documento=fecha_documento)
            self._populate()

        EditDocumentDialog(self, doc, on_save=guardar)

    def _open_assign_queries_dialog(self, ruta):
        if not self.queries_manager:
            messagebox.showinfo(
                "Queries no disponibles",
                "Este panel no tiene acceso al gestor de queries."
            )
            return

        doc = next((d for d in self.service.get_all() if d.ruta_documento == ruta), None)
        if doc is None:
            return

        def guardar(query_ids):
            self.service.asignar_queries(ruta, query_ids)
            self._populate()

        AssignQueriesDialog(self, doc, self.queries_manager, on_save=guardar)

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0, bg=C["bg"], fg=C["white"])
        menu.add_command(label="Editar información", command=lambda: self._open_edit_dialog(row))
        menu.add_command(label="🔗 Asignar queries", command=lambda: self._open_assign_queries_dialog(row))
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

    def _sort_by(self, col, reverse, remember=True):
        items = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children("")]

        if col == "activo":
            # ordenar por booleano real, no por el símbolo ☑/☐
            items = [(self.tree.set(iid, col) == "☑", iid) for iid in self.tree.get_children("")]
        elif col == "Fecha_update":
            # si fecha_modificacion es date/datetime, mejor ordenar por el objeto original
            docs = {doc.ruta_documento: doc for doc in self.service.get_all()}
            items = [(docs[iid].fecha_modificacion, iid) for iid in self.tree.get_children("")]
        elif col == "fecha_doc":
            docs = {doc.ruta_documento: doc for doc in self.service.get_all()}
            # las fechas vacías se van al final independientemente del orden
            items = [(docs[iid].fecha_documento or "9999-99-99", iid) for iid in self.tree.get_children("")]
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
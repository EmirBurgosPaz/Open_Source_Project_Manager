"""
ui/queries_dialog.py

Diálogo modal para crear o editar una query documentada.
Sigue el mismo patrón visual que task_dialog.py / project_dialog.py.

Uso:
    QueriesDialog(parent, manager, on_saved=callback)                # crear
    QueriesDialog(parent, manager, query_id="uuid", on_saved=cb)      # editar

Novedad:
    En vez de escribir el SQL a mano, se puede pegar un link "raw" de
    GitLab (u otra URL accesible) y el contenido se descarga y se
    muestra automáticamente en el cuadro de SQL.
"""

import re
import os
import threading
import urllib.error
import urllib.request
from urllib.parse import quote

import tkinter as tk
from tkinter import ttk, messagebox

from config import C, KEYBOARD_KEYS
from pathlib import Path
from dotenv import load_dotenv


from models.querie_model import CATEGORIAS_DEFAULT
from models.querie_model import ORIGENES_DEFAULT
from storage.tags_manager import TagsManager
from ui.tags_input import TagInput
from utils.ui_helpers import add_hover, lighten

env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)

try:
    TOKEN_GIT_LAB = os.getenv("TOKEN_GIT_LAB")
except ValueError as error_file:
    print(error_file)


class QueriesDialog(tk.Toplevel):
    def __init__(self, parent, manager, tags_manager, query_id=None, on_saved=None):
        super().__init__(parent)
        self.manager = manager
        self.tags_manager = tags_manager
        self.query_id = query_id
        self.on_saved = on_saved
        self.existing = manager.obtener(query_id) if query_id else None

        self.title("Editar query" if self.existing else "Nueva query")
        self.focus()
        self.configure(bg=C["bg"])
        self.geometry("800x920")
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        if self.existing:
            self._cargar_datos(self.existing)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind(KEYBOARD_KEYS["escape"], self._on_close)

    # ---------- UI ----------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        form = tk.Frame(self, bg=C["bg"])
        form.pack(fill="both", expand=True, padx=8, pady=8)

        # Nombre
        tk.Label(form, text="Nombre", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", **pad
        )
        self.entry_nombre = tk.Entry(
            form, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat"
        )
        self.entry_nombre.pack(fill="x", padx=12)
        self.entry_nombre.focus()

        # Categoría + Origen en la misma fila
        fila = tk.Frame(form, bg=C["bg"])
        fila.pack(fill="x", padx=12, pady=(10, 0))

        col1 = tk.Frame(fila, bg=C["bg"])
        col1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Label(col1, text="Categoría", bg=C["bg"], fg=C["white"]).pack(anchor="w")
        self.combo_categoria = ttk.Combobox(
            col1, values=CATEGORIAS_DEFAULT, state="normal"
        )
        self.combo_categoria.pack(fill="x")

        col2 = tk.Frame(fila, bg=C["bg"])
        col2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(col2, text="Origen / conexión", bg=C["bg"], fg=C["white"]).pack(anchor="w")
        self.combo_origen = ttk.Combobox(
            col2, values=ORIGENES_DEFAULT, state="normal"
        )
        self.combo_origen.pack(fill="x")

        # Descripción
        tk.Label(form, text="Descripción / para qué sirve", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        self.text_desc = tk.Text(
            form, height=3, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat", wrap="word"
        )
        self.text_desc.pack(fill="x", padx=12)

        # --- Link SQL (GitLab) ---
        tk.Label(form, text="Link SQL (GitLab raw)", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        link_frame = tk.Frame(form, bg=C["bg"])
        link_frame.pack(fill="x", padx=12)

        self.entry_sql_link = tk.Entry(
            link_frame, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat"
        )
        self.entry_sql_link.pack(side="left", fill="x", expand=True)


        self.btn_cargar_sql = tk.Button(
            link_frame, text="Cargar", command=self._cargar_sql_desde_link,
            bg=C["button"], fg=C["white"], relief="flat", padx=10
        )
        add_hover(self.btn_cargar_sql, lighten(C["accent"], 0.25), C["button"])
        self.btn_cargar_sql.pack(side="left", padx=(6, 0))

        # Token opcional para repos privados de GitLab (se manda como header PRIVATE-TOKEN)
        token_frame = tk.Frame(form, bg=C["bg"])
        token_frame.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(
            token_frame, text="Token GitLab (solo si el repo es privado)",
            bg=C["bg"], fg=C["white"]
        ).pack(anchor="w")

        self.entry_sql_token = tk.Entry(
            token_frame, bg=C["panel"], fg=C["white"],
            insertbackground=C["accent_hover"], relief="flat"
        )
        self.entry_sql_token.pack(fill="x")
        self.entry_sql_token.insert(0, TOKEN_GIT_LAB)
        self.entry_sql_token.config(show="*")

        self.lbl_estado_link = tk.Label(
            form, text="", bg=C["bg"], fg=C["accent"], anchor="w"
        )
        self.lbl_estado_link.pack(fill="x", padx=12)

        # SQL (vista previa / edición del contenido descargado)
        tk.Label(form, text="SQL", bg=C["bg"], fg=C["white"]).pack(
            anchor="w", padx=12, pady=(4, 0)
        )
        sql_frame = tk.Frame(form, bg=C["bg"])
        sql_frame.pack(fill="both", expand=True, padx=12)

        scroll = tk.Scrollbar(sql_frame)
        scroll.pack(side="right", fill="y")

        self.text_sql = tk.Text(
            sql_frame, bg=C["bg_secondary"], fg=C["accent"],
            insertbackground=C["accent_hover"], relief="flat", wrap="none",
            font=("Consolas", 10), undo=False, yscrollcommand=scroll.set,
            state="disabled", cursor="arrow"
        )
        self.text_sql.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.text_sql.yview)

        # Tags
        self.tag_input = TagInput(
            form, self.tags_manager, bg=C["bg"], fg=C["white"],
            entry_bg=C["panel"], accent=C["accent"]
        )
        self.tag_input.pack(fill="x", padx=12)

        # Botones
        botones = tk.Frame(self, bg=C["bg"])
        botones.pack(fill="x", padx=12, pady=10)

        cancel_btn = tk.Button(
            botones, text="Cancelar", command=self.destroy,
            bg=C["border"], fg=C["white"], relief="flat", padx=14
        )
        add_hover(cancel_btn, lighten(C["accent"], 0.25), C["button"])
        cancel_btn.pack(side="right", padx=(6, 0))

        # Botón Guardar
        self.btn_guardar = tk.Button(
            botones, text="Guardar", command=self._guardar,
            bg=C["button"], fg=C["white"], relief="flat", padx=14
        )
        add_hover(self.btn_guardar, lighten(C["accent"], 0.25), C["button"])
        self.btn_guardar.pack(side="right")

        # Enlazar Ctrl+S para guardar
        self.bind(KEYBOARD_KEYS["save"], lambda e: self._guardar())

    # ---------- Helper para el Text de solo lectura ----------

    def _set_sql_preview(self, contenido):
        """Escribe contenido en self.text_sql aunque esté deshabilitado (solo lectura)."""
        self.text_sql.config(state="normal")
        self.text_sql.delete("1.0", "end")
        self.text_sql.insert("1.0", contenido)
        self.text_sql.config(state="disabled")

    # ---------- Conversión de link web -> endpoint de API de GitLab ----------

    def _convertir_a_api_url(self, url):
        """
        Convierte un link web de GitLab del tipo:
            https://gitlab.com/<namespace>/<proyecto>/-/raw/<rama>/<ruta/al/archivo.sql>
        al endpoint de la API REST:
            https://gitlab.com/api/v4/projects/<id-url-encoded>/repository/files/<ruta-url-encoded>/raw?ref=<rama>

        El endpoint de la API es el soportado oficialmente para autenticar con
        PRIVATE-TOKEN; el link web (/-/raw/) a veces devuelve 403 aunque el
        token sea válido, según la configuración del proyecto/instancia.
        Si el link no coincide con ese patrón, se devuelve tal cual.
        """
        m = re.match(
            r"^(https?://[^/]+)/(.+?)/-/raw/([^/]+)/([^?]+)(?:\?.*)?$",
            url
        )
        if not m:
            return url
        base, namespace_path, rama, ruta_archivo = m.groups()
        project_id = quote(namespace_path, safe="")
        ruta_enc = quote(ruta_archivo, safe="")
        rama_enc = quote(rama, safe="")
        return f"{base}/api/v4/projects/{project_id}/repository/files/{ruta_enc}/raw?ref={rama_enc}"

    # ---------- Carga de SQL desde link ----------

    def _cargar_sql_desde_link(self, auto=False):
        """Descarga el contenido del link (raw de GitLab) y lo muestra en el Text de SQL."""
        url = self.entry_sql_link.get().strip()
        if not url:
            if not auto:
                messagebox.showwarning("Falta información", "Pega primero el link del SQL.")
            return

        self.btn_cargar_sql.config(state="disabled")
        self.lbl_estado_link.config(text="Cargando SQL desde el link...", fg=C["accent"])

        token = self.entry_sql_token.get().strip()
        api_url = self._convertir_a_api_url(url)

        def _descargar(target_url):
            headers = {"User-Agent": "Mozilla/5.0 (QueriesDialog)"}
            if token:
                headers["PRIVATE-TOKEN"] = token
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="replace")

        def worker():
            try:
                try:
                    contenido = _descargar(api_url)
                except urllib.error.HTTPError:
                    # Si la API falla y el link original es distinto, se intenta con ese.
                    if api_url != url:
                        contenido = _descargar(url)
                    else:
                        raise
                self.after(0, lambda: self._on_sql_cargado(contenido, url))
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    msg = (
                        f"Error HTTP {e.code}: sin acceso al archivo. Verifica que:\n"
                        "- El token sea correcto y no haya expirado.\n"
                        "- El token tenga scope 'read_repository' o 'api'.\n"
                        "- Tu usuario tenga acceso al repositorio (Emir_Burgos/boveda_trabajo_diario).\n"
                        "- La rama y la ruta del archivo en el link sean correctas."
                    )
                elif e.code == 404:
                    msg = "Error HTTP 404: no se encontró el archivo (revisa rama y ruta en el link)."
                else:
                    msg = f"Error HTTP {e.code} al descargar el link."
                self.after(0, lambda: self._on_sql_error(msg))
            except urllib.error.URLError as e:
                self.after(0, lambda: self._on_sql_error(f"No se pudo conectar: {e.reason}"))
            except Exception as e:
                self.after(0, lambda: self._on_sql_error(f"Error inesperado: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_sql_cargado(self, contenido, url):
        self._set_sql_preview(contenido)
        self.lbl_estado_link.config(text=f"SQL cargado desde: {url}", fg=C["accent"])
        self.btn_cargar_sql.config(state="normal")

    def _on_sql_error(self, mensaje):
        self.lbl_estado_link.config(text=mensaje, fg="#e06c75")
        self.btn_cargar_sql.config(state="normal")
        messagebox.showerror("Error al cargar SQL", mensaje)

    # ---------- Datos ----------

    def _cargar_datos(self, q):
        self.entry_nombre.insert(0, q["nombre"])
        self.combo_categoria.set(q["categoria"])
        self.combo_origen.set(q.get("origen", ""))
        self.text_desc.insert("1.0", q.get("descripcion", ""))
        self.tag_input.set_tags(q.get("tags", []))

        sql_link = q.get("sql_link", "")
        self.entry_sql_link.insert(0, sql_link)

        if sql_link:
            # Si ya tiene un link guardado, se intenta refrescar el SQL automáticamente.
            self._cargar_sql_desde_link(auto=True)

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        categoria = self.combo_categoria.get().strip()
        origen = self.combo_origen.get().strip()
        descripcion = self.text_desc.get("1.0", "end").strip()
        sql = self.text_sql.get("1.0", "end").strip()
        sql_link = self.entry_sql_link.get().strip()
        tags = self.tag_input.get_tags()
        self.tags_manager.registrar_varios(tags)

        if not nombre:
            messagebox.showwarning("Falta información", "El nombre es obligatorio.")
            return
        if not sql_link:
            messagebox.showwarning(
                "Falta información",
                "Pega el link del SQL en GitLab."
            )
            return
        if not sql:
            messagebox.showwarning(
                "Falta información",
                "No se ha cargado el SQL todavía. Presiona 'Cargar' antes de guardar."
            )
            return
        if not categoria:
            messagebox.showwarning("Falta información", "Selecciona o escribe una categoría.")
            return

        if self.existing:
            self.manager.actualizar(
                self.query_id,
                nombre=nombre, categoria=categoria, origen=origen,
                descripcion=descripcion, sql_link=sql_link, tags=tags,
            )
        else:
            self.manager.agregar(nombre, categoria, origen, descripcion, sql_link, tags)

        if self.on_saved:
            self.on_saved()
        self.destroy()

    def _on_close(self, event=None):
        self.destroy()
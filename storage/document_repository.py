"""
storage/document_repository.py — Persistencia dedicada para documentos_data.json.
Repositorio independiente del JsonRepository principal (que maneja db.json).
"""

import json
import os
import tempfile


class DocumentRepository:
    """
    Maneja lectura/escritura de documentos_data.json de forma aislada.
    Escritura atómica: escribe a un archivo temporal y luego reemplaza,
    para evitar corromper el JSON si la app se cierra a mitad de escritura.
    """

    def __init__(self, filepath: str = "documentos_data.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            self._write([])

    def load(self) -> list[dict]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            # Archivo corrupto o ilegible: no truena la app, devuelve lista vacía
            return []

    def save(self, documents: list[dict]):
        self._write(documents)

    def _write(self, documents: list[dict]):
        directory = os.path.dirname(os.path.abspath(self.filepath)) or "."
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(documents, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, self.filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
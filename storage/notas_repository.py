"""
storage/notas_repository.py — Persistencia aislada para Notas.

Sigue el mismo patrón que document_repository.py: escritura atómica
vía tempfile + os.replace, en un archivo JSON independiente de db.json
(notas_data.json), para no mezclar datos ni arriesgar corrupción cruzada.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from models.nota import Nota

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "notas_data.json"


class NotaRepository:
    def __init__(self, ruta: Path = DEFAULT_PATH):
        self.ruta = Path(ruta)
        if not self.ruta.exists():
            self._escribir({"notas": []})

    # ── Lectura ──────────────────────────────────────────────────────
    def _leer(self) -> dict:
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"notas": []}

    def get_all(self) -> list:
        data = self._leer()
        return [Nota.from_dict(n) for n in data.get("notas", [])]

    def get_by_id(self, nota_id: str) -> Optional[Nota]:
        for nota in self.get_all():
            if nota.id == nota_id:
                return nota
        return None

    # ── Escritura atómica ────────────────────────────────────────────
    def _escribir(self, data: dict):
        carpeta = self.ruta.parent
        fd, tmp_path = tempfile.mkstemp(dir=carpeta, prefix=".notas_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.ruta)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def guardar_todas(self, notas: list):
        self._escribir({"notas": [n.to_dict() for n in notas]})

    # ── Operaciones CRUD ─────────────────────────────────────────────
    def guardar(self, nota: Nota):
        notas = self.get_all()
        for i, n in enumerate(notas):
            if n.id == nota.id:
                notas[i] = nota
                break
        else:
            notas.append(nota)
        self.guardar_todas(notas)

    def eliminar(self, nota_id: str):
        notas = [n for n in self.get_all() if n.id != nota_id]
        self.guardar_todas(notas)
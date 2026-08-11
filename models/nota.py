"""
models/nota.py — Modelo de datos para una Nota (texto enriquecido).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Nota:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str = ""
    # Formato: {"runs": [{"texto": "...", "tags": ["bold", "italic", ...]}, ...]}
    # Ver utils/rich_text.py para serializar/deserializar desde el widget Text.
    contenido: dict = field(default_factory=lambda: {"runs": []})
    tags: list = field(default_factory=list)
    fecha_creacion: str = field(default_factory=lambda: datetime.now().isoformat())
    fecha_modificacion: str = field(default_factory=lambda: datetime.now().isoformat())
    favorito: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "contenido": self.contenido,
            "tags": self.tags,
            "fecha_creacion": self.fecha_creacion,
            "fecha_modificacion": self.fecha_modificacion,
            "favorito": self.favorito,
        }

    @staticmethod
    def from_dict(data: dict) -> "Nota":
        return Nota(
            id=data.get("id", str(uuid.uuid4())),
            titulo=data.get("titulo", ""),
            contenido=data.get("contenido", {"runs": []}),
            tags=data.get("tags", []),
            fecha_creacion=data.get("fecha_creacion", datetime.now().isoformat()),
            fecha_modificacion=data.get("fecha_modificacion", datetime.now().isoformat()),
            favorito=data.get("favorito", False),
        )

    @property
    def texto_plano(self) -> str:
        """Texto plano del contenido (sin formato), útil para búsquedas."""
        return "".join(run.get("texto", "") for run in self.contenido.get("runs", []))

    def preview(self, largo: int = 80) -> str:
        """Fragmento de texto plano para mostrar en el Treeview."""
        plano = self.texto_plano.replace("\n", " ").strip()
        return plano[:largo] + ("…" if len(plano) > largo else "")
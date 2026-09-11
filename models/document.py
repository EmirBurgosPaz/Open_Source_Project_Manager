from dataclasses import dataclass, field
from datetime import datetime
import os


@dataclass
class Document:
    ruta_documento: str = ""
    nombre_documento: str = ""
    fecha_modificacion: str = ""
    activo: int = 1
    pertenece: str = ""
    descripcion: str = ""       # texto descriptivo del archivo
    fecha_documento: str = ""   # fecha asignada manualmente por el usuario
    query_ids: list = field(default_factory=list)  # NUEVO: IDs de Query asociadas a este documento

    def to_dict(self) -> dict:
        return {
            "Ruta_documento": self.ruta_documento,
            "Nombre_documento": self.nombre_documento,
            "Fecha_modificacion": self.fecha_modificacion,
            "Activo": self.activo,
            "Pertenece": self.pertenece,
            "Descripcion": self.descripcion,
            "Fecha_documento": self.fecha_documento,
            "Query_ids": self.query_ids,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Document":
        return cls(
            ruta_documento=d.get("Ruta_documento", ""),
            nombre_documento=d.get("Nombre_documento", ""),
            fecha_modificacion=d.get("Fecha_modificacion", ""),
            activo=int(d.get("Activo", 1)),
            pertenece=d.get("Pertenece", ""),
            descripcion=d.get("Descripcion", ""),
            fecha_documento=d.get("Fecha_documento", ""),
            query_ids=list(d.get("Query_ids", [])),
        )

    def refresh_mtime(self) -> bool:
        """Actualiza Fecha_modificacion si el archivo cambió en disco. True si cambió."""
        if not self.ruta_documento or not os.path.exists(self.ruta_documento):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(self.ruta_documento)).strftime("%Y-%m-%d %H:%M:%S")
        if mtime != self.fecha_modificacion:
            self.fecha_modificacion = mtime
            return True
        return False
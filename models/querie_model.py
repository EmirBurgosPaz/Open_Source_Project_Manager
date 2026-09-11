"""
query_model.py

Modelo de datos (entidad de dominio) para una Query documentada.
No conoce nada sobre archivos, JSON ni persistencia: solo define
la forma de una Query y las reglas propias del dato (validaciones,
normalización de tags, serialización a/desde dict).
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# Categorías detectadas en tu carpeta de Consultas.
# Puedes editar esta lista libremente o cargarla dinámicamente
# más adelante desde config.py si prefieres centralizarla ahí.
CATEGORIAS_DEFAULT = [
    "Consultas_Activas_Archivos",
    "Consultas_Activas_SAP",
    "Consultas_referencia",
    "Consultas_vistas_activas",
    "Experimentales",
    "Modelo de autorizacion",
    "Sistema_comisiones",
    "Modelo actual de ingresos",
]

ORIGENES_DEFAULT = ["SAP HANA", "Archivo plano", "Vista", "Otro"]


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _normalizar_tags(tags) -> list[str]:
    """Quita espacios y duplicados (case-insensitive) preservando el primer valor visto."""
    vistos, resultado = set(), []
    for t in tags or []:
        clave = t.strip().lower()
        if clave and clave not in vistos:
            vistos.add(clave)
            resultado.append(t.strip())
    return resultado


@dataclass
class Query:
    nombre: str
    categoria: str
    origen: str
    descripcion: str = ""
    sql: str = ""
    tags: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado: str = field(default_factory=_ahora)
    modificado: str = field(default_factory=_ahora)

    def __post_init__(self):
        self.tags = _normalizar_tags(self.tags)

    # ---------- Compatibilidad estilo dict ----------
    # Permite seguir usando q["nombre"], q.get("tags", []), etc. como si
    # fuera el dict original, sin tener que reescribir toda la UI.

    def __getitem__(self, clave):
        try:
            return getattr(self, clave)
        except AttributeError:
            raise KeyError(clave)

    def __setitem__(self, clave, valor):
        setattr(self, clave, valor)

    def __contains__(self, clave):
        return hasattr(self, clave)

    def get(self, clave, default=None):
        return getattr(self, clave, default)

    def keys(self):
        return self.to_dict().keys()

    # ---------- Operaciones propias del dato ----------

    def tocar(self):
        """Actualiza el timestamp de modificación."""
        self.modificado = _ahora()

    def actualizar_campos(self, **campos):
        """Aplica cambios validando/normalizando lo que corresponda."""
        for clave, valor in campos.items():
            if clave == "tags":
                valor = _normalizar_tags(valor)
            if hasattr(self, clave):
                setattr(self, clave, valor)
        self.tocar()

    def coincide_con_texto(self, texto: str) -> bool:
        texto = texto.lower()
        return (
            texto in self.nombre.lower()
            or texto in (self.descripcion or "").lower()
            or texto in (self.sql or "").lower()
            or any(texto in t.lower() for t in self.tags)
        )

    def tiene_tags(self, claves_filtro: set, modo: str = "AND") -> bool:
        propias = {t.strip().lower() for t in self.tags}
        if modo == "AND":
            return claves_filtro.issubset(propias)
        return bool(claves_filtro & propias)

    def clonar_como_copia(self) -> "Query":
        """Crea una nueva Query igual a esta pero con id/nombre/timestamps propios."""
        return Query(
            nombre=f"{self.nombre} (copia)",
            categoria=self.categoria,
            origen=self.origen,
            descripcion=self.descripcion,
            sql=self.sql,
            tags=list(self.tags),
        )

    # ---------- Serialización ----------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Query":
        # Permite reconstruir sin perder id/timestamps guardados
        return cls(
            nombre=data["nombre"],
            categoria=data["categoria"],
            origen=data["origen"],
            descripcion=data.get("descripcion", ""),
            sql=data.get("sql", ""),
            tags=data.get("tags", []),
            id=data.get("id", str(uuid.uuid4())),
            creado=data.get("creado", _ahora()),
            modificado=data.get("modificado", _ahora()),
        )
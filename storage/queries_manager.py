"""
queries_manager.py

Manejo de persistencia para el módulo de documentación de queries.
Sigue el mismo patrón que projects_data.json: un archivo JSON plano
en la raíz del proyecto (queries_data.json).

Cada query se guarda como un diccionario:
{
    "id": "uuid",
    "nombre": str,
    "categoria": str,          # ej: "Consultas_Activas_SAP"
    "origen": str,             # ej: "SAP HANA", "Archivo plano", "Otro"
    "descripcion": str,
    "sql": str,
    "tags": [str, ...],
    "creado": "2026-08-04T10:00:00",
    "modificado": "2026-08-04T10:00:00",
}
"""

import json
import os
import uuid
from datetime import datetime

# Ajusta esta ruta si tu app guarda los JSON en otro lugar
# (ej: junto a projects_data.json)
DATA_FILE = "queries_data.json"

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
    "Modelo_comisiones",
]

ORIGENES_DEFAULT = ["SAP HANA", "Archivo plano", "Vista", "Otro"]


class QueriesManager:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.queries = []
        self.load()

    # ---------- Persistencia ----------

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.queries = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.queries = []
        else:
            self.queries = []
        return self.queries

    def save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.queries, f, ensure_ascii=False, indent=2)

    # ---------- Operaciones CRUD ----------

    def agregar(self, nombre, categoria, origen, descripcion, sql, tags=None):
        ahora = datetime.now().isoformat(timespec="seconds")
        nueva = {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "categoria": categoria,
            "origen": origen,
            "descripcion": descripcion,
            "sql": sql,
            "tags": tags or [],
            "creado": ahora,
            "modificado": ahora,
        }
        self.queries.append(nueva)
        self.save()
        return nueva

    def actualizar(self, query_id, **campos):
        for q in self.queries:
            if q["id"] == query_id:
                q.update(campos)
                q["modificado"] = datetime.now().isoformat(timespec="seconds")
                self.save()
                return q
        return None

    def eliminar(self, query_id):
        antes = len(self.queries)
        self.queries = [q for q in self.queries if q["id"] != query_id]
        if len(self.queries) != antes:
            self.save()
            return True
        return False

    def obtener(self, query_id):
        for q in self.queries:
            if q["id"] == query_id:
                return q
        return None

    def duplicar(self, query_id):
        original = self.obtener(query_id)
        if not original:
            return None
        copia = dict(original)
        copia["nombre"] = f"{original['nombre']} (copia)"
        copia.pop("id", None)
        return self.agregar(
            copia["nombre"],
            copia["categoria"],
            copia["origen"],
            copia["descripcion"],
            copia["sql"],
            copia.get("tags", []),
        )

    # ---------- Filtros / búsqueda ----------

    def filtrar(self, categoria=None, texto=None):
        resultado = self.queries
        if categoria and categoria != "Todas":
            resultado = [q for q in resultado if q["categoria"] == categoria]
        if texto:
            texto = texto.lower()
            resultado = [
                q for q in resultado
                if texto in q["nombre"].lower()
                or texto in q.get("descripcion", "").lower()
                or texto in q.get("sql", "").lower()
                or any(texto in t.lower() for t in q.get("tags", []))
            ]
        return resultado

    def categorias_en_uso(self):
        return sorted({q["categoria"] for q in self.queries})
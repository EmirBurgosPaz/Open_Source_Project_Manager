"""
storage/queries_manager.py

Manejo de persistencia para el módulo de documentación de queries.
Sigue el mismo patrón que projects_data.json: un archivo JSON plano
en la raíz del proyecto (queries_data.json).

Este módulo NO conoce reglas del dato en sí (eso vive en
models/querie_model.py); solo se encarga de leer/escribir el archivo
y ofrecer operaciones CRUD + filtros sobre la colección de Query.
"""

import json
import os
from typing import Optional

from models.querie_model import Query

# Ajusta esta ruta si tu app guarda los JSON en otro lugar
# (ej: junto a projects_data.json)
DATA_FILE = "queries_data.json"


class QueriesManager:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.queries: list[Query] = []
        self.load()

    # ---------- Persistencia ----------

    def load(self) -> list[Query]:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    crudos = json.load(f)
                self.queries = [Query.from_dict(q) for q in crudos]
            except (json.JSONDecodeError, OSError):
                self.queries = []
        else:
            self.queries = []
        return self.queries

    def save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(
                [q.to_dict() for q in self.queries],
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ---------- Operaciones CRUD ----------

    def agregar(self, nombre, categoria, origen, descripcion, sql, tags=None) -> Query:
        nueva = Query(
            nombre=nombre,
            categoria=categoria,
            origen=origen,
            descripcion=descripcion,
            sql=sql,
            tags=tags or [],
        )
        self.queries.append(nueva)
        self.save()
        return nueva

    def actualizar(self, query_id, **campos) -> Optional[Query]:
        q = self.obtener(query_id)
        if q is None:
            return None
        q.actualizar_campos(**campos)
        self.save()
        return q

    def eliminar(self, query_id) -> bool:
        antes = len(self.queries)
        self.queries = [q for q in self.queries if q.id != query_id]
        if len(self.queries) != antes:
            self.save()
            return True
        return False

    def obtener(self, query_id) -> Optional[Query]:
        for q in self.queries:
            if q.id == query_id:
                return q
        return None

    def duplicar(self, query_id) -> Optional[Query]:
        original = self.obtener(query_id)
        if not original:
            return None
        copia = original.clonar_como_copia()
        self.queries.append(copia)
        self.save()
        return copia

    # ---------- Operaciones sobre tags en toda la colección ----------

    def reemplazar_tag_en_todas(self, tag_viejo: str, tag_nuevo: str):
        """Renombra un tag en todas las queries que lo usan (dedupe si colisiona)."""
        clave_vieja = tag_viejo.strip().lower()
        cambiado = False
        for q in self.queries:
            claves = [t.strip().lower() for t in q.tags]
            if clave_vieja not in claves:
                continue
            nuevos = [tag_nuevo if t.strip().lower() == clave_vieja else t for t in q.tags]
            q.actualizar_campos(tags=nuevos)
            cambiado = True
        if cambiado:
            self.save()

    def quitar_tag_de_todas(self, tag: str):
        """Elimina un tag de todas las queries que lo tengan."""
        clave = tag.strip().lower()
        cambiado = False
        for q in self.queries:
            originales = q.tags
            nuevos = [t for t in originales if t.strip().lower() != clave]
            if len(nuevos) != len(originales):
                q.actualizar_campos(tags=nuevos)
                cambiado = True
        if cambiado:
            self.save()

    def todos_los_tags(self) -> list[str]:
        """Lista única de tags realmente en uso (para poblar filtros/UI)."""
        tags = set()
        for q in self.queries:
            tags.update(q.tags)
        return sorted(tags, key=str.lower)

    # ---------- Filtros / búsqueda ----------

    def filtrar(self, categoria=None, texto=None, tags=None, modo_tags="AND") -> list[Query]:
        resultado = self.queries
        if categoria and categoria != "Todas":
            resultado = [q for q in resultado if q.categoria == categoria]
        if texto:
            resultado = [q for q in resultado if q.coincide_con_texto(texto)]
        if tags:
            claves_filtro = {t.strip().lower() for t in tags}
            resultado = [q for q in resultado if q.tiene_tags(claves_filtro, modo_tags)]
        return resultado
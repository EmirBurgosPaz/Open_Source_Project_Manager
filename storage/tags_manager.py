"""
storage/tags_manager.py

Registro central de tags: nombre normalizado, texto de visualización,
color y utilidades de renombrar/fusionar/eliminar propagando el cambio
a todas las queries que ya usan ese tag.

Se apoya en dos métodos que debes añadir a QueriesManager:
    - reemplazar_tag_en_todas(tag_viejo, tag_nuevo)
    - quitar_tag_de_todas(tag)
(ver ejemplos al final de este archivo, comentados)

Uso:
    tags_manager = TagsManager("tags_data.json")
    tags_manager.registrar_varios(["sap", "comisiones"])
    tags_manager.renombrar("sap", "SAP HANA", queries_manager)
"""

import json
import os
import random

COLOR_PALETTE = [
    "#4C6EF5", "#12B886", "#F59F00", "#E64980",
    "#7048E8", "#15AABF", "#FA5252", "#82C91E",
    "#FD7E14", "#5C7CFA",
]


class TagsManager:
    def __init__(self, data_file="tags_data.json"):
        self.data_file = data_file
        self._tags = {}  # clave_normalizada -> {"display": str, "color": str}
        self._cargar()

    # ---------- Persistencia ----------

    def _cargar(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                self._tags = json.load(f)
        else:
            self._tags = {}

    def _guardar(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self._tags, f, ensure_ascii=False, indent=2)

    # ---------- Normalización ----------

    @staticmethod
    def normalizar(nombre: str) -> str:
        return nombre.strip().lower()

    def existe(self, nombre: str) -> bool:
        return self.normalizar(nombre) in self._tags

    # ---------- Alta / consulta ----------

    def registrar(self, nombre: str) -> str:
        """Da de alta el tag si no existe. Devuelve su clave normalizada."""
        nombre = nombre.strip()
        if not nombre:
            return ""
        clave = self.normalizar(nombre)
        if clave not in self._tags:
            self._tags[clave] = {
                "display": nombre,
                "color": random.choice(COLOR_PALETTE),
            }
            self._guardar()
        return clave

    def registrar_varios(self, nombres):
        cambiado = False
        for n in nombres:
            n = n.strip()
            if n and self.normalizar(n) not in self._tags:
                self._tags[self.normalizar(n)] = {
                    "display": n,
                    "color": random.choice(COLOR_PALETTE),
                }
                cambiado = True
        if cambiado:
            self._guardar()

    def obtener_todos(self):
        """Lista de dicts {clave, display, color}, ordenada alfabéticamente."""
        return [
            {"clave": clave, "display": info["display"], "color": info["color"]}
            for clave, info in sorted(self._tags.items(), key=lambda x: x[1]["display"].lower())
        ]

    def color_de(self, nombre: str) -> str:
        info = self._tags.get(self.normalizar(nombre))
        return info["color"] if info else "#6c757d"

    def display_de(self, nombre: str) -> str:
        info = self._tags.get(self.normalizar(nombre))
        return info["display"] if info else nombre

    def set_color(self, nombre: str, color: str):
        clave = self.normalizar(nombre)
        if clave in self._tags:
            self._tags[clave]["color"] = color
            self._guardar()

    # ---------- Renombrar / fusionar / eliminar ----------

    def renombrar(self, nombre_viejo: str, nombre_nuevo: str, queries_manager):
        """Renombra un tag y actualiza todas las queries que lo usan."""
        clave_vieja = self.normalizar(nombre_viejo)
        clave_nueva = self.normalizar(nombre_nuevo)
        if clave_vieja not in self._tags or not nombre_nuevo.strip():
            return

        if clave_nueva == clave_vieja:
            self._tags[clave_vieja]["display"] = nombre_nuevo.strip()
            self._guardar()
            queries_manager.reemplazar_tag_en_todas(nombre_viejo, nombre_nuevo.strip())
            return

        if clave_nueva in self._tags:
            self.fusionar(nombre_viejo, nombre_nuevo, queries_manager)
            return

        self._tags[clave_nueva] = {
            "display": nombre_nuevo.strip(),
            "color": self._tags[clave_vieja]["color"],
        }
        del self._tags[clave_vieja]
        self._guardar()
        queries_manager.reemplazar_tag_en_todas(nombre_viejo, nombre_nuevo.strip())

    def fusionar(self, nombre_origen: str, nombre_destino: str, queries_manager):
        """Combina dos tags: las queries del origen pasan a usar el destino."""
        clave_origen = self.normalizar(nombre_origen)
        clave_destino = self.normalizar(nombre_destino)
        if clave_origen == clave_destino or clave_origen not in self._tags:
            return
        destino_display = self._tags.get(clave_destino, {}).get("display", nombre_destino.strip())
        queries_manager.reemplazar_tag_en_todas(nombre_origen, destino_display)
        self._tags.pop(clave_origen, None)
        self._guardar()

    def eliminar(self, nombre: str, queries_manager):
        """Borra un tag por completo: del registro y de todas las queries."""
        clave = self.normalizar(nombre)
        if clave not in self._tags:
            return
        queries_manager.quitar_tag_de_todas(nombre)
        del self._tags[clave]
        self._guardar()

    def conteo_uso(self, queries_manager):
        """{clave: cantidad_de_queries} recorriendo el manager de queries."""
        conteo = {}
        for q in queries_manager.filtrar():
            for t in q.get("tags", []):
                clave = self.normalizar(t)
                conteo[clave] = conteo.get(clave, 0) + 1
        return conteo



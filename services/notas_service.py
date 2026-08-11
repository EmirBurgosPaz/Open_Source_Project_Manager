"""
services/notas_service.py — Lógica de negocio para Notas.
Capa intermedia entre ui/ y storage/, sin conocer detalles de Tkinter
ni del formato del archivo JSON.
"""

from datetime import datetime
from typing import Optional

from models.nota import Nota
from storage.notas_repository import NotaRepository


class NotasService:
    def __init__(self, repo: NotaRepository = None):
        self.repo = repo or NotaRepository()

    def get_all(self) -> list:
        notas = self.repo.get_all()
        notas.sort(key=lambda n: n.fecha_modificacion, reverse=True)
        return notas

    def obtener(self, nota_id: str) -> Optional[Nota]:
        return self.repo.get_by_id(nota_id)

    def crear(self, titulo: str = "Nueva nota", contenido: dict = None, tags: list = None) -> Nota:
        nota = Nota(titulo=titulo, contenido=contenido or {"runs": []}, tags=tags or [])
        self.repo.guardar(nota)
        return nota

    def actualizar(self, nota: Nota):
        nota.fecha_modificacion = datetime.now().isoformat()
        self.repo.guardar(nota)

    def eliminar(self, nota_id: str):
        self.repo.eliminar(nota_id)

    def alternar_favorito(self, nota_id: str):
        nota = self.obtener(nota_id)
        if nota:
            nota.favorito = not nota.favorito
            self.actualizar(nota)

    def buscar(self, texto: str = "", tag_filtro: str = None) -> list:
        texto = (texto or "").lower().strip()
        resultado = self.get_all()
        if texto:
            resultado = [
                n for n in resultado
                if texto in n.titulo.lower() or texto in n.texto_plano.lower()
            ]
        if tag_filtro:
            resultado = [n for n in resultado if tag_filtro in n.tags]
        return resultado

    def todos_los_tags(self) -> list:
        vistos = set()
        for n in self.get_all():
            vistos.update(n.tags)
        return sorted(vistos)
import os
from datetime import datetime
from models.document import Document
from storage.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, repository: DocumentRepository | None = None):
        self._repo = repository or DocumentRepository()
        self._documents: list[Document] = []
        self._load()

    def _load(self):
        raw = self._repo.load()
        self._documents = [Document.from_dict(d) for d in raw]

    def _persist(self):
        self._repo.save([d.to_dict() for d in self._documents])

    def get_all(self) -> list[Document]:
        return list(self._documents)

    def add_document(self, ruta: str, pertenece: str = "", descripcion: str = "",
                      fecha_documento: str = "") -> Document:
        nombre = os.path.basename(ruta)
        mtime = ""
        if os.path.exists(ruta):
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M:%S")
        doc = Document(ruta_documento=ruta, nombre_documento=nombre,
                        fecha_modificacion=mtime, activo=1, pertenece=pertenece,
                        descripcion=descripcion, fecha_documento=fecha_documento)
        self._documents.append(doc)
        self._persist()
        return doc

    def toggle_activo(self, ruta_documento: str):
        for d in self._documents:
            if d.ruta_documento == ruta_documento:
                d.activo = 0 if d.activo else 1
                self._persist()
                return d
        return None

    def edit_document(self, ruta_documento: str, pertenece: str | None = None,
                       descripcion: str | None = None, fecha_documento: str | None = None):
        """Actualiza solo los campos que no sean None. Devuelve el Document actualizado o None."""
        for d in self._documents:
            if d.ruta_documento == ruta_documento:
                if pertenece is not None:
                    d.pertenece = pertenece
                if descripcion is not None:
                    d.descripcion = descripcion
                if fecha_documento is not None:
                    d.fecha_documento = fecha_documento
                self._persist()
                return d
        return None

    def remove_document(self, ruta_documento: str):
        self._documents = [d for d in self._documents if d.ruta_documento != ruta_documento]
        self._persist()

    def refresh_all_mtimes(self) -> list[Document]:
        cambiados = [d for d in self._documents if d.refresh_mtime()]
        if cambiados:
            self._persist()
        return cambiados

    # ---------- Relación Documento <-> Queries ----------

    def asignar_queries(self, ruta_documento: str, query_ids: list[str]):
        """Reemplaza el conjunto de queries asociadas a un documento."""
        for d in self._documents:
            if d.ruta_documento == ruta_documento:
                # dedupe preservando orden
                vistos, limpio = set(), []
                for qid in query_ids or []:
                    if qid not in vistos:
                        vistos.add(qid)
                        limpio.append(qid)
                d.query_ids = limpio
                self._persist()
                return d
        return None

    def obtener_nombres_queries(self, ruta_documento: str, queries_manager) -> list[str]:
        """
        Resuelve los IDs guardados en el documento a nombres legibles,
        usando el QueriesManager ya existente. IDs de queries eliminadas
        se ignoran silenciosamente (no rompen la UI).
        """
        doc = next((d for d in self._documents if d.ruta_documento == ruta_documento), None)
        if doc is None:
            return []
        nombres = []
        for qid in doc.query_ids:
            q = queries_manager.obtener(qid)
            if q is not None:
                nombres.append(q["nombre"])
        return nombres

    def limpiar_queries_inexistentes(self, queries_manager):
        """
        Quita de todos los documentos los query_ids que ya no existen en
        queries_manager (por ejemplo, tras eliminar una query). Llamar
        opcionalmente después de eliminar una query desde la UI.
        """
        ids_validos = {q["id"] for q in queries_manager.queries}
        cambiado = False
        for d in self._documents:
            nuevos = [qid for qid in d.query_ids if qid in ids_validos]
            if len(nuevos) != len(d.query_ids):
                d.query_ids = nuevos
                cambiado = True
        if cambiado:
            self._persist()
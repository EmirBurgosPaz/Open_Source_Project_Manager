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

    def add_document(self, ruta: str, pertenece: str = "") -> Document:
        nombre = os.path.basename(ruta)
        mtime = ""
        if os.path.exists(ruta):
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M:%S")
        doc = Document(ruta_documento=ruta, nombre_documento=nombre,
                        fecha_modificacion=mtime, activo=1, pertenece=pertenece)
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

    def remove_document(self, ruta_documento: str):
        self._documents = [d for d in self._documents if d.ruta_documento != ruta_documento]
        self._persist()

    def refresh_all_mtimes(self) -> list[Document]:
        cambiados = [d for d in self._documents if d.refresh_mtime()]
        if cambiados:
            self._persist()
        return cambiados
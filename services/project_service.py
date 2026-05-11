"""
services/project_service.py — Lógica de negocio para proyectos.
"""

from models.project import Project
from storage.json_repository import JsonRepository


class ProjectService:
    def __init__(self, repo: JsonRepository, task_service):
        self.repo         = repo
        self.task_service = task_service  # necesario para reasignar tareas al borrar

    @property
    def projects(self) -> list[Project]:
        return self.task_service.projects

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get_all(self) -> list[Project]:
        return self.projects

    def get_by_id(self, project_id: str) -> Project | None:
        return next((p for p in self.projects if p.id == project_id), None)

    def next_project_id(self) -> str:
        existing = [int(p.id[1:]) for p in self.projects if p.id.startswith("p") and p.id[1:].isdigit()]
        n = max(existing, default=0) + 1
        return f"p{n}"

    # ── Mutaciones ────────────────────────────────────────────────────────────

    def create(self, name: str, color: str) -> Project:
        if not name.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        project = Project(id=self.next_project_id(), name=name, color=color)
        self.task_service.projects.append(project)
        self._persist()
        return project

    def update(self, project_id: str, name: str, color: str) -> Project:
        if not name.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        project = self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Proyecto {project_id} no encontrado.")
        project.name  = name
        project.color = color
        self._persist()
        return project

    def delete(self, project_id: str):
        """Elimina el proyecto y reasigna sus tareas al primer proyecto restante."""
        self.task_service.projects = [p for p in self.projects if p.id != project_id]
        fallback_id = self.projects[0].id if self.projects else ""
        for task in self.task_service.tasks:
            if task.project_id == project_id:
                task.project_id = fallback_id
        self._persist()

    # ── Persistencia ──────────────────────────────────────────────────────────

    def _persist(self):
        self.repo.save(
            self.task_service.projects,
            self.task_service.tasks,
            self.task_service.next_id,
            self.task_service.members,
        )

"""
services/task_service.py — Lógica de negocio para tareas.
Aquí viven las reglas: qué se valida, cómo se crea/edita/elimina.
No sabe nada de JSON ni de tkinter.
"""

from datetime import datetime
from models.project import Project
from models.task import Task
from storage.json_repository import JsonRepository


class TaskService:
    def __init__(self, repo: JsonRepository):
        self.repo = repo
        projects, tasks, self.next_id, self.members  = repo.load()
        self.projects = list(projects)
        self.tasks    = list(tasks)

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get_all(self) -> list[Task]:
        return self.tasks

    def get_by_project(self, project_id: str) -> list[Task]:
        return [t for t in self.tasks if t.project_id == project_id]

    def get_by_id(self, task_id: int) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    # ── Estadísticas ──────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total    = len(self.tasks)
        done     = sum(1 for t in self.tasks if t.status == "done")
        progress = sum(1 for t in self.tasks if t.status == "progress")
        high     = sum(1 for t in self.tasks if t.priority == "Alta" and t.status != "done")
        return {"total": total, "done": done, "progress": progress, "high_priority": high}

    def get_report_lines(self) -> list[str]:
        stats = self.get_stats()
        total = stats["total"]
        done  = stats["done"]
        pct   = int(done / total * 100) if total else 0
        lines = [
            f"Total de tareas:             {total}",
            f"Completadas:                 {done}  ({pct}%)",
            f"Alta prioridad (pendientes): {stats['high_priority']}",
            "",
            "Por proyecto:",
        ]
        for p in self.projects:
            pt = [t for t in self.tasks if t.project_id == p.id]
            pd = [t for t in pt if t.status == "done"]
            lines.append(f"  {p.name}: {len(pd)}/{len(pt)} completadas")
        return lines

    # ── Mutaciones ────────────────────────────────────────────────────────────

    def create(self, data: dict) -> Task:
        self._validate(data)
        task = Task(
            id          = self.next_id,
            title       = data["title"],
            project_id  = data["project"],
            status      = data["status"],
            priority    = data["priority"],
            assign      = data["assign"],
            due         = data["due"],
            description = data.get("description", ""),
            client = data.get("client", ""),
            created     = data.get("created", ""),
        )
        self.next_id += 1
        self.tasks.append(task)
        self._persist()
        return task

    def update(self, task_id: int, data: dict) -> Task:
        self._validate(data)
        task = self.get_by_id(task_id)
        if not task:
            raise ValueError(f"Tarea {task_id} no encontrada")
        task.title       = data["title"]
        task.project_id  = data["project"]
        task.status      = data["status"]
        task.priority    = data["priority"]
        task.assign      = data["assign"]
        task.due         = data["due"]
        task.description = data.get("description", "")
        task.client = data.get("client", "")
        self._persist()
        return task

    def delete(self, task_id: int):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self._persist()
    
    def duplicate(self, task_id: int) -> Task:
        original = self.get_by_id(task_id)
        if not original:
            raise ValueError(f"Tarea {task_id} no encontrada")
        task = Task(
            id              = self.next_id,
            title           = f"{original.title} (copia)",
            project_id      = original.project_id,
            status          = original.status,
            priority        = original.priority,
            assign          = original.assign,
            due             = original.due,
            description     = original.description,
            client = original.client,
            created         = original.created,
        )
        self.next_id += 1
        self.tasks.append(task)
        self._persist()
        return task

    # ── Validación ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(data: dict):
        if not data.get("title", "").strip():
            raise ValueError("El título no puede estar vacío.")
        try:
            datetime.strptime(data["due"].strip(), "%Y-%m-%d")
        except (ValueError, KeyError):
            raise ValueError("Fecha inválida. Usa el formato AAAA-MM-DD.")

    # ── Persistencia ──────────────────────────────────────────────────────────

    def _persist(self):
        self.repo.save(self.projects, self.tasks, self.next_id, self.members)

    def save_members(self, members: list[str]):
        self.members = members
        self._persist()
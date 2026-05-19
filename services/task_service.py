"""
services/task_service.py — Lógica de negocio para tareas.
Aquí viven las reglas: qué se valida, cómo se crea/edita/elimina.
No sabe nada de JSON ni de tkinter.
"""

from datetime import datetime
from models.project import Project
from models.task import Task
from storage.json_repository import JsonRepository
from services.recurring_task_service import RecurringTaskService
from config import COLUMNS_STATUS


class TaskService:
    def __init__(self, repo: JsonRepository):
        self.repo = repo
        self.projects, self.tasks, self.next_id, self.members, rec_data, rec_next = repo.load()
        self.projects = list(self.projects)
        self.tasks    = list(self.tasks)
        self.recurring = RecurringTaskService(repo)
        self.recurring.load(rec_data, rec_next) 
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

        # --- NUEVA LÓGICA DE FECHA DE FINALIZACIÓN ---
        # Verificamos si el nuevo estado es "done" y antes NO era "done"
        if data["status"] == "done" and task.status != "done":
            task.completed_at = datetime.now().strftime("%Y-%m-%d")
        # Opcional: si la regresan a progreso, limpiamos la fecha
        elif data["status"] != "done":
            task.completed_at = None
        # ---------------------------------------------

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
    
    def reorder(self, src_id: int, tgt_id: int):
        src_idx = next(i for i, t in enumerate(self.tasks) if t.id == src_id)
        tgt_idx = next(i for i, t in enumerate(self.tasks) if t.id == tgt_id)
        self.tasks[src_idx], self.tasks[tgt_idx] = self.tasks[tgt_idx], self.tasks[src_idx]
        self._persist()

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
        self.repo.save(self.projects, self.tasks, self.next_id, self.members,self.recurring.to_dict_list(), self.recurring.next_id,)

    def save_members(self, members: list[str]):
        self.members = members
        self._persist()
    
    def filter(self, tasks: list, filters: dict) -> list:
        result = tasks
        

        if filters.get("client"):
            result = [t for t in result if filters["client"] in t.title.lower()]

        if filters.get("search"):
            result = [t for t in result if filters["search"] in t.title.lower()]

        if filters.get("status") and filters["status"] != "Todos":
            if filters["status"] == "Activas":
                # Buscamos los IDs internos de las tareas que no están terminadas
                # (Ajusta "Por hacer" y "En progreso" si tus textos en COLUMNS_STATUS son diferentes)
                active_ids = [c[0] for c in COLUMNS_STATUS if c[1] in ["Por hacer", "En progreso"]]
                result = [t for t in result if t.status in active_ids]
            else:
                # Lógica normal para un estado individual (Ej. "Completado")
                status_id = next((c[0] for c in COLUMNS_STATUS if c[1] == filters["status"]), None)
                if status_id:
                    result = [t for t in result if t.status == status_id]

        if filters.get("priority") and filters["priority"] != "Todas":
            result = [t for t in result if t.priority == filters["priority"]]

        if filters.get("assign") and filters["assign"] != "Todos":
            result = [t for t in result if t.assign == filters["assign"]]

        return result
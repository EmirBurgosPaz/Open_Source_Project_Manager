from models.recurring_task import RecurringTask
from storage.json_repository import JsonRepository


class RecurringTaskService:
    def __init__(self, repo: JsonRepository):
        self.repo           = repo
        self.tasks: list    = []
        self.next_id: int   = 1

    def load(self, data: list, next_id: int):
        self.tasks   = [RecurringTask.from_dict(t) for t in data]
        self.next_id = next_id

    def get_all(self) -> list:
        return self.tasks

    def create(self, data: dict) -> RecurringTask:
        task = RecurringTask(
            id        = self.next_id,
            title     = data["title"],
            category  = data.get("category", ""),
            frequency = data.get("frequency", "Semanal"),
            status    = data.get("status", "To do"),
            priority  = data.get("priority", 1),
        )
        self.next_id += 1
        self.tasks.append(task)
        return task

    def update(self, task_id: int, data: dict) -> RecurringTask:
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            raise ValueError(f"Tarea {task_id} no encontrada")
        task.title     = data["title"]
        task.category  = data.get("category", "")
        task.frequency = data.get("frequency", "Semanal")
        task.status    = data.get("status", "To do")
        task.priority  = data.get("priority", 1)
        return task

    def delete(self, task_id: int):
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def to_dict_list(self) -> list:
        return [t.to_dict() for t in self.tasks]
    
    def reorder(self, src_id: int, tgt_id: int):
        src_idx = next(i for i, t in enumerate(self.tasks) if t.id == src_id)
        tgt_idx = next(i for i, t in enumerate(self.tasks) if t.id == tgt_id)
        self.tasks[src_idx], self.tasks[tgt_idx] = self.tasks[tgt_idx], self.tasks[src_idx]
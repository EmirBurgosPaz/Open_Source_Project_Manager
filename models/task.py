"""
models/task.py — Definición de la entidad Task.
Solo describe QUÉ es una tarea, sin lógica de negocio ni persistencia.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    id: int
    title: str
    project_id: str
    status: str       = "todo"       # backlog | todo | progress | review | done
    priority: str     = "Media"      # Alta | Media | Baja
    assign: str       = ""
    due: str          = ""           # "YYYY-MM-DD"
    description: str  = ""
    client: str  = ""
    created: str      = field(default_factory=lambda: str(date.today()))

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "title":       self.title,
            "project":     self.project_id,
            "status":      self.status,
            "priority":    self.priority,
            "assign":      self.assign,
            "due":         self.due,
            "description": self.description,
            "client": self.client,
            "created":     self.created,
        }

    @staticmethod
    def from_dict(d: dict) -> "Task":
        return Task(
            id          = d["id"],
            title       = d["title"],
            project_id  = d.get("project", ""),
            status      = d.get("status", "todo"),
            priority    = d.get("priority", "Media"),
            assign      = d.get("assign", ""),
            due         = d.get("due", ""),
            description = d.get("description", ""),
            client = d.get("client", ""),
            created     = d.get("created", str(date.today())),
        )

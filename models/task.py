"""
models/task.py — Definición de la entidad Task.
Solo describe QUÉ es una tarea, sin lógica de negocio ni persistencia.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    project_id: str
    status: str       = "todo"       # backlog | todo | progress | review | done
    priority: str     = "Media"      # Alta | Media | Baja
    assign: str       = ""
    due: str          = ""           # "YYYY-MM-DD"
    requester: str  = ""
    client: str  = ""
    position: str = ""
    authorization: str = ""
    type_request: str = ""
    created: str      = field(default_factory=lambda: str(date.today()))
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "title":       self.title,
            "project":     self.project_id,
            "status":      self.status,
            "priority":    self.priority,
            "assign":      self.assign,
            "due":         self.due,
            "requester": self.requester,
            "client": self.client,
            "created":     self.created,
            "completed_at":     self.completed_at,
            "position" : self.position,
            "authorization": self.authorization,
            "type_request": self.type_request,
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
            requester = d.get("requester", ""),
            client = d.get("client", ""),
            created     = d.get("created", str(date.today())),
            completed_at     = d.get("completed_at", None),
            position = d.get("position", ""),
            authorization = d.get("authorization", ""),
            type_request = d.get("type_request", ""),

        )

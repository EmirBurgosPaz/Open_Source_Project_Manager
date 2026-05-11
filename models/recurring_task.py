from dataclasses import dataclass, field
from datetime import date

@dataclass
class RecurringTask:
    id: int
    title: str
    category: str  = ""
    frequency: str = "Semanal"
    status: str    = "To do"
    priority: int  = 1          # 1, 2, 3
    created: str   = field(default_factory=lambda: str(date.today()))

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "title":     self.title,
            "category":  self.category,
            "frequency": self.frequency,
            "status":    self.status,
            "priority":  self.priority,
            "created":   self.created,
        }

    @staticmethod
    def from_dict(d: dict) -> "RecurringTask":
        return RecurringTask(
            id        = d["id"],
            title     = d["title"],
            category  = d.get("category", ""),
            frequency = d.get("frequency", "Semanal"),
            status    = d.get("status", "To do"),
            priority  = d.get("priority", 1),
            created   = d.get("created", str(date.today())),
        )
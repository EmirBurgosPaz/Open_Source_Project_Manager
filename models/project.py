"""
models/project.py — Definición de la entidad Project.
Solo describe QUÉ es un proyecto.
"""

from dataclasses import dataclass


@dataclass
class Project:
    id: str
    name: str
    color: str = "#7C6FE0"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "color": self.color}

    @staticmethod
    def from_dict(d: dict) -> "Project":
        return Project(id=d["id"], name=d["name"], color=d.get("color", "#7C6FE0"))

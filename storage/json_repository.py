"""
storage/json_repository.py — Persistencia en JSON.
Toda lectura/escritura de disco vive aquí.
Si mañana migras a SQLite, solo reescribes este archivo.
"""

import json
import os
from config import DATA_FILE, DEFAULT_PROJECTS, DEFAULT_TASKS, DEFAULT_MEMBERS
from models.project import Project
from models.task import Task


class JsonRepository:
    """Lee y escribe el archivo JSON. Devuelve objetos del dominio."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath

    # ── Carga ─────────────────────────────────────────────────────────────────

    def load(self) -> tuple[list[Project], list[Task], int]:
        if not os.path.exists(self.filepath):
            projects = [Project.from_dict(p) for p in DEFAULT_PROJECTS]
            tasks    = [Task.from_dict(t)    for t in DEFAULT_TASKS]
            return projects, tasks, 10, DEFAULT_MEMBERS.copy(), [], 1

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        projects = [Project.from_dict(p) for p in data.get("projects", DEFAULT_PROJECTS)]
        tasks    = [Task.from_dict(t)    for t in data.get("tasks",    DEFAULT_TASKS)]
        next_id  = data.get("next_id", 10)
        members  = data.get("members", DEFAULT_MEMBERS.copy())
        recurring  = data.get("recurring_tasks", [])
        next_rec   = data.get("next_recurring_id", 1)
        return projects, tasks, next_id, members, recurring, next_rec

    # ── Guardado ──────────────────────────────────────────────────────────────

    def save(self, projects: list[Project], tasks: list[Task], next_id: int, members: list[str], recurring: list[Task], next_rec_id: int):
        data = {
            "projects": [p.to_dict() for p in projects],
            "tasks":    [t.to_dict() for t in tasks],
            "next_id":  next_id,
            "members":  members,
            "recurring_tasks":    recurring,
            "next_recurring_id":  next_rec_id,
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

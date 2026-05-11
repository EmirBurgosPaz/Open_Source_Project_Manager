"""
main.py — Punto de entrada de Project Manager.
Solo orquesta: conecta servicios con la UI.
No contiene lógica de negocio ni widgets complejos.

Ejecutar: python main.py
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import messagebox
from config import C, MEMBERS
from storage.json_repository import JsonRepository
from services.task_service import TaskService 
from services.project_service import ProjectService 
from ui.project_dialog import  ProjectDialog
from ui.task_dialog import TaskDialog
from ui.sidebar import  Sidebar
from ui.task_list import  TaskList
from ui.members_dialog import MembersDialog

class ProjectManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Manager")
        self.geometry("1050x660")
        self.configure(bg=C["bg"])
        self.minsize(800, 500)

        # ── Servicios (toda la lógica vive aquí) ─────────────────────────────
        repo                 = JsonRepository()
        self.task_service    = TaskService(repo)
        self.project_service = ProjectService(repo, self.task_service)
        MEMBERS[:] = self.task_service.members

        self.filter_project: str | None = None

        self._build_layout()
        self.refresh()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_filter       = self._on_filter,
            on_new_project  = self._new_project,
            on_edit_project = self._edit_project,
            on_report       = self._show_report,
            on_members      = self._manage_members,
        )
        self.sidebar.pack(side="left", fill="y")

        # Panel principal
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        # Stats bar
        self.stats_frame = tk.Frame(main, bg=C["panel"])
        self.stats_frame.pack(fill="x")
        tk.Frame(main, bg=C["border"], height=1).pack(fill="x")

        # Topbar
        topbar = tk.Frame(main, bg=C["panel"], pady=10)
        topbar.pack(fill="x")
        tk.Frame(main, bg=C["border"], height=1).pack(fill="x")

        self.lbl_title = tk.Label(topbar, text="Todas las tareas",
                                   bg=C["panel"], fg=C["text"],
                                   font=("Helvetica", 13, "bold"))
        self.lbl_title.pack(side="left", padx=16)

        tk.Button(topbar, text="+ Nueva tarea",
                  bg=C["accent"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=self._new_task).pack(side="right", padx=16)

        # Lista de tareas
        self.task_list = TaskList(    main,
                                    on_edit_task      = self._edit_task,
                                    on_duplicate_task = self._duplicate_task,
                                    on_delete_task    = self._delete_task,
                                    )
        self.task_list.pack(fill="both", expand=True)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        projects = self.project_service.get_all()
        tasks    = self.task_service.get_all()
        visible  = (tasks if not self.filter_project
                    else self.task_service.get_by_project(self.filter_project))

        self.sidebar.rebuild(projects, tasks)
        self._render_stats()
        self.task_list.render(visible, projects)

    def _render_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        s = self.task_service.get_stats()
        for label, val, color in [
            ("Total",          s["total"],        C["text"]),
            ("Completadas",    s["done"],          "#2ECC71"),
            ("En progreso",    s["progress"],      "#E6A817"),
            ("Alta prioridad", s["high_priority"], "#E05555"),
        ]:
            f = tk.Frame(self.stats_frame, bg=C["panel"])
            f.pack(side="left", padx=14, pady=10)
            tk.Label(f, text=str(val), bg=C["panel"], fg=color,
                     font=("Helvetica", 20, "bold")).pack()
            tk.Label(f, text=label, bg=C["panel"], fg=C["muted"],
                     font=("Helvetica", 9)).pack()
        tk.Frame(self.stats_frame, bg=C["border"], width=1).pack(side="left", fill="y", pady=6)

    # ── Acciones: Tareas ─────────────────────────────────────────────────────

    def _new_task(self):
        projects = [p.__dict__ for p in self.project_service.get_all()]
        # TaskDialog espera dicts con "id" y "name"
        projects_dicts = [{"id": p.id, "name": p.name} for p in self.project_service.get_all()]
        dlg = TaskDialog(self, projects_dicts)
        self.wait_window(dlg)
        if dlg.result and not dlg.result.get("deleted"):
            try:
                self.task_service.create(dlg.result)
                self.refresh()
            except ValueError as e:
                messagebox.showwarning("Error", str(e))

    def _edit_task(self, task_id: int):
        task = self.task_service.get_by_id(task_id)
        if not task:
            return
        projects_dicts = [{"id": p.id, "name": p.name} for p in self.project_service.get_all()]
        dlg = TaskDialog(self, projects_dicts, task=task.to_dict())
        self.wait_window(dlg)
        if not dlg.result:
            return
        if dlg.result.get("deleted"):
            self.task_service.delete(task_id)
        else:
            try:
                self.task_service.update(task_id, dlg.result)
            except ValueError as e:
                messagebox.showwarning("Error", str(e))
        self.refresh()

    def _duplicate_task(self, task_id: int):
        self.task_service.duplicate(task_id)
        self.refresh()

    def _delete_task(self, task_id: int):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta tarea?"):
            self.task_service.delete(task_id)
            self.refresh()

    # ── Acciones: Proyectos ───────────────────────────────────────────────────

    def _new_project(self):
        dlg = ProjectDialog(self)
        self.wait_window(dlg)
        if dlg.result and not dlg.result.get("deleted"):
            try:
                self.project_service.create(dlg.result["name"], dlg.result["color"])
                self.refresh()
            except ValueError as e:
                messagebox.showwarning("Error", str(e))

    def _edit_project(self, project_id: str):
        proj = self.project_service.get_by_id(project_id)
        if not proj:
            return
        dlg = ProjectDialog(self, project=proj.__dict__)
        self.wait_window(dlg)
        if not dlg.result:
            return
        if dlg.result.get("deleted"):
            if not messagebox.askyesno("Eliminar proyecto",
                    f"¿Eliminar '{proj.name}'? Las tareas asociadas quedarán sin proyecto.",
                    parent=self):
                return
            self.project_service.delete(project_id)
            if self.filter_project == project_id:
                self.filter_project = None
                self.lbl_title.config(text="Todas las tareas")
        else:
            try:
                self.project_service.update(project_id, dlg.result["name"], dlg.result["color"])
            except ValueError as e:
                messagebox.showwarning("Error", str(e))
        self.refresh()

    # ── Acciones: Reporte ─────────────────────────────────────────────────────

    def _show_report(self):
        lines = self.task_service.get_report_lines()
        messagebox.showinfo("Reporte", "\n".join(lines))

    # ── Filtro ────────────────────────────────────────────────────────────────

    def _on_filter(self, project_id: str, name: str = "Todas las tareas"):
        self.filter_project = None if project_id == "all" else project_id
        self.lbl_title.config(text="Todas las tareas" if project_id == "all" else name)
        self.refresh()

    def _manage_members(self):
        dlg = MembersDialog(self, self.task_service.members)
        self.wait_window(dlg)
        self.task_service.save_members(dlg.members)
        MEMBERS[:] = dlg.members

# ── Punto de entrada ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ProjectManagerApp()
    app.mainloop()

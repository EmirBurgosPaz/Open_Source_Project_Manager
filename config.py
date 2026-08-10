"""
config.py — Constantes globales, paleta de colores y datos por defecto.
Todo lo que no cambia con la lógica va aquí.
"""

import os



# ── Persistencia ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "projects_data.json")

#-----------------------------Colores -------------------------

C = {
    "bg":        "#1A1A1E",
    "bg_secondary": "#181825",
    "sidebar":   "#141417",
    "panel":     "#22222A",
    "button":     "#333333",
    "border":    "#2E2E38",
    "grid": "#1F1F26",
    "text":      "#E8E8EC",
    "muted":     "#7A7A8A",
    "accent":    "#7C6FE0",
    "delete":    "#FF4040",
    "accent_dk": "#5A4FBA",
    "accent_hover" : "#5599ff" ,
    "hover":     "#2A2A36",
    "row_alt":   "#1F1F26",
    "dlg_bg":    "#1E1E26",
    "dlg_input": "#2A2A36",
    "dlg_border":"#3A3A4A",
    "over_bg" : "#2A1A1A",
    "over_fg" : "#E05555",
    "today_bg" : "#2A2010",
    "today_fg" : "#E6A817",
    "done_bg":   "#14291E",
    "done_fg":   "#4ADE80",
    "info_bg":   "#142336",
    "info_fg":   "#60A5FA",
    "disabled_fg": "#4D4D5C",
    "tag_teal":  "#2DD4BF",
    "tag_pink":  "#F472B6",
    "todo_bg": "#162B43",
    "todo_fg": "#38BDF8",
    "high_bg": "#331E18",
    "high_fg": "#FF6B6B",
    "selected_bg": "#2a2a3a",
    "white" : "#FFFFFF",
    "done_tasks" :  "#2ECC71",
    "progress_tasks" : "#E6A817",
    "priority_tasks" : "#E05555",
    "splash_bg" : "#1F1F26",
    "medium_bg": "#241F10",
      "medium_fg": "#E8B33D",
"low_bg":    "#16232B",
 "low_fg":    "#5599FF",
"over_bg_1": "#241616",
 "over_fg_1": "#E28080",
"over_bg_2": "#2A1A1A",
 "over_fg_2": "#E05555",
"over_bg_3": "#3A0F0F",
 "over_fg_3": "#FF4040",
"soon_bg":   "#241F10", 
"soon_fg":   "#D8B23A",
}

# ── Datos iniciales (solo se usan si no existe el JSON) ───────────────────────

DEFAULT_PROJECTS = [
    {"id": "p1", "name": "App Móvil",   "color": "#7C6FE0"},
    {"id": "p2", "name": "Sitio Web",   "color": "#1D9E75"},
    {"id": "p3", "name": "API Backend", "color": "#EF9F27"},
]

DEFAULT_TASKS = [
    {"id": 1,  "title": "Diseño de pantallas de onboarding", "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Ana R.",    "due": "2026-05-15", "requester": ""},
    {"id": 2,  "title": "Integración con Firebase Auth",      "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Carlos M.", "due": "2026-05-18", "requester": ""},
    {"id": 3,  "title": "Componente de búsqueda global",      "status": "todo",     "project": "p2", "priority": "Media", "assign": "Laura P.",  "due": "2026-05-20", "requester": ""},
    {"id": 4,  "title": "Optimización de imágenes WebP",      "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-10", "requester": ""},
    {"id": 5,  "title": "Endpoint de pagos con Stripe",       "status": "review",   "project": "p3", "priority": "Alta",  "assign": "Jorge G.",  "due": "2026-05-14", "requester": ""},
    {"id": 6,  "title": "Tests de integración en CI/CD",      "status": "todo",     "project": "p3", "priority": "Media", "assign": "Carlos M.", "due": "2026-05-22", "requester": ""},
    {"id": 7,  "title": "Documentación de la API REST",       "status": "backlog",  "project": "p3", "priority": "Baja",  "assign": "Laura P.",  "due": "2026-05-30", "requester": ""},
    {"id": 8,  "title": "Push notifications iOS",             "status": "backlog",  "project": "p1", "priority": "Media", "assign": "Jorge G.",  "due": "2026-05-28", "requester": ""},
    {"id": 9,  "title": "Rediseño del footer",                "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-08", "requester": "", "client":""},
]

# ── Kanban columns ────────────────────────────────────────────────────────────

COLUMNS_STATUS = [
    ("todo",     "Por hacer"),
    ("progress", "En progreso"),
    ("review",   "En revisión"),
    ("done",     "Completado"),
    ("denied",     "Denegado"),
    ("backlog",  "Backlog"),
]

COLUMNS_STATUS_DEFAULT = [
    ("todo",     "Por hacer",   ),
]


# ── Opciones de formularios ───────────────────────────────────────────────────

PRIORITY_OPTIONS = ["Alta", "Media", "Baja"]
DEFAULT_MEMBERS = [{"name": "User inicial", "pos": "", "team": ""}]
MEMBERS = []
PROJECT_COLORS   = [
    "#7C6FE0", "#1D9E75", "#EF9F27", "#E05555", "#4A90D9",
    "#E8678A", "#2ECC71", "#F39C12", "#1ABC9C", "#9B59B6",
    "#E67E22", "#3498DB", "#E91E8C", "#00BCD4", "#8BC34A",
]

# ── Paleta de colores (tema oscuro) ───────────────────────────────────────────

PRIORITY_STYLE = {
    "Alta":  {"bg": C["high_bg"], "fg": C["high_fg"],
              "bold": True,  "icon": "!!!"},
    "Media": {"bg": C["medium_bg"], "fg": C["medium_fg"],
              "bold": False, "icon": "!!"},
    "Baja":  {"bg": C["low_bg"], "fg": C["low_fg"],
              "bold": False, "icon": "!"},
}
DEFAULT_PRIORITY_STYLE = {"bg": C["todo_bg"], "fg": C["todo_fg"], "bold": False, "icon": "!"}

# (días mínimos de atraso, bg, fg) — de más grave a más leve
OVERDUE_LEVELS = [
    (7, C["over_bg_3"], C["over_fg_3"]),
    (3, C["over_bg_2"], C["over_fg_2"]),
    (1, C["over_bg_1"], C["over_fg_1"]),
]
SOON_BG, SOON_FG = C["soon_bg"], C["soon_fg"]

PRIORITY_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}


FREQUENCY_OPTIONS = ["Diario", "Semanal", "Quincenal", "Mensual", "Trimestral"]

STATUS_OPTIONS = ["Direccion", "Lideres", "Proyectos", "CFM", "Gerentes", "Area", "informacion"]

POSITIONS_OPTIONS = [("Dueños", "Todo"),
                      ("Direccion" , "Todo"),
                        ("Subdireccion" , "Todo") ,
                          ("Gerencias" , "Area"),
                     ("Lideres" , "Area"),
                     ("Auditorias", "Area"),
                     ("Empleados" , "Puntual"),
                     ("Externos" , "Autorizacion"),]

CATEGORY_OPTIONS = ["Automatico", "Manual"]

KEYBOARD_KEYS = {
    "enter": "<Return>", 
    "escape": "<Escape>", 
    "space": "<space>", # ignorar
    "tab" : "<KeyPress-Tab>", # Ignorar 
    "supr" : "<Delete>",
    "new_task" : "<KeyPress-n>",  #Nueva tarea
    "new_project" : "<KeyPress-p>", # Nuevo proyecto
    "new_recurring" : "<KeyPress-r>", # Nueva tarea recurrente
    "members" : "<KeyPress-E>", # pestaña miembros
    "report" : "<KeyPress-R>", # Pestaña reportes
    "recurring" : "<KeyPress-M>", # Pestaña recurrentes
    "task" : "<KeyPress-T>", # pestaña Tareas
    "save" : "<Control-s>", # pestaña Tareas
    "New_Querrie" : "<q>",
    "querries" : "<KeyPress-Q>",
}

KEYBIND_REQUESTERS = {
    "new_task":      "Nueva tarea",
    "new_project":   "Nuevo proyecto",
    "new_recurring": "Nueva tarea recurrente",
    "members":       "Gestionar miembros",
    "report":        "Ver reportes",
    "recurring":     "Vista recurrentes",
    "task":          "Vista tareas",
    "escape":        "Cerrar ventana",
}

STATUS_COLORS = {
    "todo":     "#38BDF8",
    "progress": "#E6A817",
    "review":   "#9B59B6",
    "done":     "#2ECC71",
    "denied":   "#E05555",
    "backlog":  "#7A7A8A",
}
PRIORITY_COLORS = {
    "Alta":  "#FF6B6B",
    "Media": "#E6A817",
    "Baja":  "#38BDF8",
}




STATUS_FILL = {
    "done":     "2ECC71",
    "progress": "E6A817",
    "review":   "9B59B6",
    "todo":     "38BDF8",
    "denied":   "E05555",
    "backlog":  "7A7A8A",
}
PRIORITY_FILL = {"Alta": "FF6B6B", "Media": "E6A817", "Baja": "38BDF8"}



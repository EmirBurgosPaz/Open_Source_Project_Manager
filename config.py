"""
config.py — Constantes globales, paleta de colores y datos por defecto.
Todo lo que no cambia con la lógica va aquí.
"""

import os

# ── Persistencia ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "projects_data.json")

# ── Datos iniciales (solo se usan si no existe el JSON) ───────────────────────

DEFAULT_PROJECTS = [
    {"id": "p1", "name": "App Móvil",   "color": "#7C6FE0"},
    {"id": "p2", "name": "Sitio Web",   "color": "#1D9E75"},
    {"id": "p3", "name": "API Backend", "color": "#EF9F27"},
]

DEFAULT_TASKS = [
    {"id": 1,  "title": "Diseño de pantallas de onboarding", "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Ana R.",    "due": "2026-05-15", "description": ""},
    {"id": 2,  "title": "Integración con Firebase Auth",      "status": "progress", "project": "p1", "priority": "Alta",  "assign": "Carlos M.", "due": "2026-05-18", "description": ""},
    {"id": 3,  "title": "Componente de búsqueda global",      "status": "todo",     "project": "p2", "priority": "Media", "assign": "Laura P.",  "due": "2026-05-20", "description": ""},
    {"id": 4,  "title": "Optimización de imágenes WebP",      "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-10", "description": ""},
    {"id": 5,  "title": "Endpoint de pagos con Stripe",       "status": "review",   "project": "p3", "priority": "Alta",  "assign": "Jorge G.",  "due": "2026-05-14", "description": ""},
    {"id": 6,  "title": "Tests de integración en CI/CD",      "status": "todo",     "project": "p3", "priority": "Media", "assign": "Carlos M.", "due": "2026-05-22", "description": ""},
    {"id": 7,  "title": "Documentación de la API REST",       "status": "backlog",  "project": "p3", "priority": "Baja",  "assign": "Laura P.",  "due": "2026-05-30", "description": ""},
    {"id": 8,  "title": "Push notifications iOS",             "status": "backlog",  "project": "p1", "priority": "Media", "assign": "Jorge G.",  "due": "2026-05-28", "description": ""},
    {"id": 9,  "title": "Rediseño del footer",                "status": "done",     "project": "p2", "priority": "Baja",  "assign": "Ana R.",    "due": "2026-05-08", "description": "", "client":""},
]

# ── Kanban columns ────────────────────────────────────────────────────────────

COLUMNS = [
    ("backlog",  "Backlog",     "#6B6A66"),
    ("todo",     "Por hacer",   "#4A90D9"),
    ("progress", "En progreso", "#E6A817"),
    ("review",   "En revisión", "#9B8FE8"),
    ("done",     "Completado",  "#2ECC71"),
]

# ── Opciones de formularios ───────────────────────────────────────────────────

PRIORITY_OPTIONS = ["Alta", "Media", "Baja"]
PRIORITY_COLORS  = {"Alta": "#E05555", "Media": "#E6A817", "Baja": "#2ECC71"}
DEFAULT_MEMBERS = [{"name": "User inicial", "pos": "", "team": ""}]
MEMBERS = []
PROJECT_COLORS   = [
    "#7C6FE0", "#1D9E75", "#EF9F27", "#E05555", "#4A90D9",
    "#E8678A", "#2ECC71", "#F39C12", "#1ABC9C", "#9B59B6",
    "#E67E22", "#3498DB", "#E91E8C", "#00BCD4", "#8BC34A",
]

# ── Paleta de colores (tema oscuro) ───────────────────────────────────────────

C = {
    "bg":        "#1A1A1E",
    "sidebar":   "#141417",
    "panel":     "#22222A",
    "border":    "#2E2E38",
    "text":      "#E8E8EC",
    "muted":     "#7A7A8A",
    "accent":    "#7C6FE0",
    "accent_dk": "#5A4FBA",
    "hover":     "#2A2A36",
    "row_alt":   "#1F1F26",
    "dlg_bg":    "#1E1E26",
    "dlg_input": "#2A2A36",
    "dlg_border":"#3A3A4A",
}

FREQUENCY_OPTIONS = ["Diario", "Semanal", "Quincenal", "Mensual", "Trimestral", "Único"]

STATUS_OPTIONS = ["Direccion", "Lideres", "Proyectos", "CFM", "Gerentes", "Area", "informacion"]

CATEGORY_OPTIONS = ["Automatico", "Manual"]
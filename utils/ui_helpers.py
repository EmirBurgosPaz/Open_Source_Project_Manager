"""
utils/ui_helpers.py — Funciones de UI reutilizables y sin estado.
Widgets genéricos que no dependen de la lógica de negocio.
"""

import tkinter as tk
from tkinter import ttk
from config import C


def make_dark_combobox(parent, values: list, default: str) -> tuple[tk.StringVar, ttk.Combobox]:
    """Crea un Combobox con el tema oscuro. Devuelve (variable, widget)."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TCombobox",
                    fieldbackground=C["dlg_input"],
                    background=C["dlg_input"],
                    foreground=C["text"],
                    arrowcolor=C["muted"],
                    bordercolor=C["dlg_border"],
                    lightcolor=C["dlg_input"],
                    darkcolor=C["dlg_input"])
    style.map("Dark.TCombobox",
              fieldbackground=[("readonly", C["dlg_input"])],
              foreground=[("readonly", C["text"])])
    var = tk.StringVar(value=default)
    cb  = ttk.Combobox(parent, textvariable=var, values=values,
                       state="readonly", font=("Helvetica", 11),
                       style="Dark.TCombobox")
    return var, cb


def make_label(parent, text: str, bg: str = None) -> tk.Label:
    """Label de sección (estilo 'muted')."""
    return tk.Label(parent, text=text,
                    bg=bg or C["dlg_bg"], fg=C["muted"],
                    font=("Helvetica", 10))


def make_entry(parent, value: str = "", disabled: bool = False) -> tk.Entry:
    """Entry con el estilo oscuro del diálogo."""
    e = tk.Entry(parent, font=("Helvetica", 11),
                 bg=C["dlg_input"], fg=C["text"],
                 insertbackground=C["text"],
                 relief="flat", bd=0,
                 highlightthickness=1,
                 highlightbackground=C["dlg_border"],
                 highlightcolor=C["accent"])
    if value:
        e.insert(0, value)
    if disabled:
        e.config(state="disabled",
                 disabledbackground=C["hover"],
                 disabledforeground=C["text"])
    return e


def center_window(window: tk.Toplevel, parent: tk.Tk):
    """Centra un Toplevel sobre su ventana padre."""
    window.update_idletasks()
    pw = parent.winfo_rootx() + parent.winfo_width()  // 2
    ph = parent.winfo_rooty() + parent.winfo_height() // 2
    w, h = window.winfo_width(), window.winfo_height()
    window.geometry(f"+{pw - w//2}+{ph - h//2}")


def bind_hover(widgets: list, bg_normal: str, bg_hover: str,
               fg_normal: str, fg_hover: str):
    """Aplica efectos hover a una lista de widgets."""
    def on_enter(e):
        for w in widgets:
            try:
                w.config(bg=bg_hover, fg=fg_hover)
            except tk.TclError:
                w.config(bg=bg_hover)

    def on_leave(e):
        for w in widgets:
            try:
                w.config(bg=bg_normal, fg=fg_normal)
            except tk.TclError:
                w.config(bg=bg_normal)

    for w in widgets:
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)

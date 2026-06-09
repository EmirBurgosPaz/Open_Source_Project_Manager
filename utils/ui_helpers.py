"""
utils/ui_helpers.py — Funciones de UI reutilizables y sin estado.
Widgets genéricos que no dependen de la lógica de negocio.
"""

import tkinter as tk
from tkinter import ttk
from config import C, KEYBOARD_KEYS, KEYBIND_DESCRIPTIONS  

_SKIP = {"enter", "space", "tab"}

def _parse_key(tk_binding: str) -> str:
    s = tk_binding.strip("<>")
    s = s.replace("KeyPress-", "")
    aliases = {
        "Escape": "Esc",
        "Return": "Enter",
        "space":  "Space",
        "Tab":    "Tab",
    }
    return aliases.get(s, s)


def _build_keybind_rows() -> list[tuple[str, str]]:
    """Devuelve lista de (tecla_legible, descripción) para las acciones con descripción."""
    rows = []
    for action, desc in KEYBIND_DESCRIPTIONS.items():
        if action in _SKIP:
            continue
        binding = KEYBOARD_KEYS.get(action)
        if binding:
            rows.append((_parse_key(binding), desc))
    return rows

def make_dark_combobox(parent, values: list, default: str) -> tuple[tk.StringVar, ttk.Combobox]:
    """Crea un Combobox con el tema oscuro. Devuelve (variable, widget)."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TCombobox",
                fieldbackground=C["dlg_input"],
                background=C["border"],
                foreground=C["text"],
                arrowcolor=C["muted"],
                bordercolor=C["border"],
                lightcolor=C["dlg_input"],
                darkcolor=C["dlg_input"],
                selectbackground=C["dlg_input"],   # ← mismo color que el campo
                selectforeground=C["text"],         # ← texto visible
                insertcolor=C["text"])

    style.map("Dark.TCombobox",
          fieldbackground=[
              ("readonly", C["border"]),
              ("focus",    C["dlg_input"]),         # ← evita fondo negro al enfocar
              ("active",   C["dlg_input"]),
          ],
          foreground=[
              ("readonly", C["text"]),
              ("active",   C["text"]),
              ("disabled", C["disabled_fg"]),
          ],
          selectbackground=[
              ("readonly", C["border"]),            # ← coincide con fieldbackground readonly
              ("focus",    C["dlg_input"]),
          ],
          selectforeground=[
              ("readonly", C["text"]),
              ("focus",    C["text"]),
          ],
          bordercolor=[
              ("focus",  C["accent"]),
              ("!focus", C["border"]),
          ])

    var = tk.StringVar(value=default)
    cb  = ttk.Combobox(parent, textvariable=var, values=values,
                       state="readonly", font=("Helvetica", 11),
                       style="Dark.TCombobox")

    def _on_tab(event):
        event.widget.tk_focusNext().focus()
        return "break"
    
    cb.bind(KEYBOARD_KEYS["tab"],_on_tab)

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

class Tooltip:
    def __init__(self, widget, text: str, trigger_widgets: list = None):
        self.widget          = widget
        self.text            = text
        self.tip             = None
        # Si se pasan widgets externos (como el frame padre), escuchar en ellos
        targets = trigger_widgets if trigger_widgets else [widget]
        for w in targets:
            w.bind("<Enter>", self._show, add="+")
            w.bind("<Leave>", self._hide, add="+")

    def _show(self, e):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 4
        y = self.widget.winfo_rooty()
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text,
                 bg=C["panel"], fg=C["text"],
                 font=("Helvetica", 9),
                 relief="flat", bd=0,
                 padx=8, pady=4).pack()

    def _hide(self, e):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class KeybindsHelp:
    """
    Botón circular '?' que muestra un panel flotante con todos los keybinds.
    Uso:
        help_btn = KeybindsHelp(parent_frame)
        help_btn.pack(side="right", padx=8)
    """

    def __init__(self, parent):
        self.parent = parent
        self._panel = None

        # Botón circular azul con '?'
        self.btn = tk.Label(
            parent,
            text="?",
            bg=C["grid"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            width=2,
            height=1,
            relief="flat",
            cursor="hand2",
        )
        # Hacerlo lucir circular con un poco de padding
        self.btn.configure(padx=4, pady=2)

        self.btn.bind("<Button-1>", self._toggle)
        self.btn.bind("<Enter>",    self._on_enter)
        self.btn.bind("<Leave>",    self._on_leave)

    def pack(self, **kwargs):
        self.btn.pack(**kwargs)

    def grid(self, **kwargs):
        self.btn.grid(**kwargs)

    # ── Hover visual ──────────────────────────────────────────────────────────

    def _on_enter(self, e):
        self.btn.config(bg=C["accent"])

    def _on_leave(self, e):
        self.btn.config(bg=C["grid"])

    # ── Panel flotante ────────────────────────────────────────────────────────

    def _toggle(self, e=None):
        if self._panel and self._panel.winfo_exists():
            self._panel.destroy()
            self._panel = None
            return
        self._show_panel()

    def _show_panel(self):
        # Posición: justo debajo del botón
        x = self.btn.winfo_rootx() - 220   # alineado a la izquierda del botón
        y = self.btn.winfo_rooty() + self.btn.winfo_height() + 6

        panel = tk.Toplevel(self.btn)
        panel.wm_overrideredirect(True)
        panel.wm_geometry(f"+{x}+{y}")
        panel.config(bg=C["border"])          # borde fino de 1px via padding
        self._panel = panel

        # Cerrar si se hace clic fuera
        panel.bind("<FocusOut>", lambda e: self._close_panel())
        panel.focus_set()

        inner = tk.Frame(panel, bg=C["panel"], padx=14, pady=10)
        inner.pack(padx=1, pady=1)

        # Título
        tk.Label(
            inner,
            text="Atajos de teclado",
            bg=C["panel"],
            fg=C["text"],
            font=("Helvetica", 11, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Separador
        tk.Frame(inner, bg=C["border"], height=1).grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8)
        )

        # Filas de keybinds
        for i, (shortcut, desc) in enumerate(_build_keybind_rows(), start=2):
    # ... mismo código de grid que antes
            # Tecla con estilo "badge"
            key_lbl = tk.Label(
                inner,
                text=shortcut,
                bg=C.get("bg", "#2a2a2a"),
                fg=C["text"],
                font=("Courier", 10, "bold"),
                relief="flat",
                padx=6, pady=2,
            )
            key_lbl.grid(row=i, column=0, sticky="w", pady=2, padx=(0, 10))

            # Flecha separadora
            tk.Label(
                inner,
                text="→",
                bg=C["panel"],
                fg=C.get("muted", "#888"),
                font=("Helvetica", 10),
            ).grid(row=i, column=1, padx=(0, 8))

            # Descripción
            tk.Label(
                inner,
                text=desc,
                bg=C["panel"],
                fg=C["text"],
                font=("Helvetica", 10),
                anchor="w",
            ).grid(row=i, column=2, sticky="w", pady=2)

    def _close_panel(self):
        if self._panel and self._panel.winfo_exists():
            self._panel.destroy()
            self._panel = None
    


TEXT_WIDGETS = (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox)

def guard_typing(callback):
    """
    Decorador/wrapper para keybinds.
    El callback solo se ejecuta si el foco NO está en un widget de texto.
    """
    def wrapper(event=None):
        focused = event.widget.winfo_toplevel().focus_get() if event else None
        if isinstance(focused, TEXT_WIDGETS):
            return  # no interceptar — dejar comportamiento default del widget
        return callback(event)
    return wrapper
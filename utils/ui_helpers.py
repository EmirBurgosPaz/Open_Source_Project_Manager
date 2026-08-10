"""
utils/ui_helpers.py — Funciones de UI reutilizables y sin estado.
Widgets genéricos que no dependen de la lógica de negocio.
"""

import tkinter as tk
from tkinter import ttk
from config import C, KEYBOARD_KEYS, KEYBIND_REQUESTERS  

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
    for action, desc in KEYBIND_REQUESTERS.items():
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
                 insertbackground=C["accent_hover"],
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



def setup_treeview_style(
    style_name: str = "Dark.Treeview",
    rowheight: int = 36,
    font: tuple = ("Helvetica", 10),
    heading_font: tuple = ("Helvetica", 9, "bold"),
    colors: dict = C,
) -> str:
    """
    Configura (o reutiliza) un estilo ttk oscuro para Treeview.
    Devuelve el nombre del estilo para usarlo directamente en:
        ttk.Treeview(parent, style=setup_treeview_style())
    """
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        style_name,
        background=colors["bg"], foreground=colors["text"],
        fieldbackground=colors["bg"], bordercolor=colors["border"],
        rowheight=rowheight, font=font,
    )
    style.configure(
        f"{style_name}.Heading",
        background=colors["panel"], foreground=colors["muted"],
        bordercolor=colors["border"], relief="flat",
        font=heading_font,
    )
    style.map(f"{style_name}.Heading",
              background=[("active", colors["hover"])])
    style.map(style_name,
              background=[("selected", colors["accent_dk"])],
              foreground=[("selected", colors["white"])])

    return style_name

def add_hover(widget, hover_bg=None, base_bg=None, hover_fg=None, base_fg=None):
    """
    Agrega efecto hover (cambio de color al pasar el mouse) a cualquier widget
    que soporte los atributos 'bg'/'fg' (tk.Button, tk.Label, tk.Frame, etc).

    - base_bg / base_fg: si no se pasan, se toman del estado actual del widget.
    - hover_bg / hover_fg: colores al pasar el mouse. Si hover_fg no se da,
      el fg no cambia.
    """
    base_bg = base_bg or widget.cget("bg")
    base_fg = base_fg if base_fg is not None else widget.cget("fg")

    def _on_enter(e):
        cfg = {}
        if hover_bg:
            cfg["bg"] = hover_bg
        if hover_fg:
            cfg["fg"] = hover_fg
        widget.configure(**cfg)

    def _on_leave(e):
        cfg = {"bg": base_bg}
        if hover_fg:
            cfg["fg"] = base_fg
        widget.configure(**cfg)

    widget.configure(bg=base_bg)
    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)

def lighten(hex_color: str, amount: float = 0.15) -> str:
    """Aclara un color hex un poco, para usarlo en estados hover."""
    try:
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def setup_treeview_hover(tree, hover_tag="hover", get_base_tag=None,
                          on_motion_extra=None, on_leave_extra=None):
    """
    Añade efecto hover genérico a un Treeview con filas alternadas.

    get_base_tag: función (iid) -> tags a restaurar. Si no se pasa,
    se calcula automáticamente ("odd"/"even") según posición.

    on_motion_extra: función opcional (event, row) llamada al final de
    cada <Motion>, útil para lógica adicional (ej. tooltips por columna).

    on_leave_extra: función opcional (event) llamada al final de <Leave>.
    """
    state = {"last_hovered": None}

    def _default_get_base_tag(iid):
        children = tree.get_children()
        idx = children.index(iid) if iid in children else 0
        return ("even",) if idx % 2 else ("odd",)

    base_tag_fn = get_base_tag or _default_get_base_tag

    def _restore(iid):
        if iid and iid in tree.get_children():
            tree.item(iid, tags=base_tag_fn(iid))

    def _on_motion(e):
        row = tree.identify_row(e.y)
        if row != state["last_hovered"]:
            _restore(state["last_hovered"])
            if row:
                tree.item(row, tags=(hover_tag,))
            state["last_hovered"] = row
        if on_motion_extra:
            on_motion_extra(e, row)

    def _on_leave(e):
        _restore(state["last_hovered"])
        state["last_hovered"] = None
        if on_leave_extra:
            on_leave_extra(e)

    tree.bind("<Motion>", _on_motion, add="+")
    tree.bind("<Leave>", _on_leave, add="+")
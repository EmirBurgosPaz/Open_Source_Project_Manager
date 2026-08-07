"""
Widget de tags con chips (pastillas de color) + autocompletado,
para reemplazar el Entry de texto libre "separado por comas" en
queries_dialog.py.
"""

import tkinter as tk


class TagInput(tk.Frame):
    def __init__(self, parent, tags_manager, bg="#1e1e1e", fg="#ffffff",
                 entry_bg="#2a2a2a", accent="#4C6EF5", **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.tags_manager = tags_manager
        self.bg = bg
        self.fg = fg
        self.entry_bg = entry_bg
        self.accent = accent
        self._tags = []  # nombres tal cual (forma "display")

        # ---- Chips (flow layout dentro de un Canvas para poder envolver) ----
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, height=32)
        self.canvas.pack(fill="x", side="top")
        self.chips_frame = tk.Frame(self.canvas, bg=bg)
        self._chips_window = self.canvas.create_window((0, 0), window=self.chips_frame, anchor="nw")
        self.chips_frame.bind("<Configure>", self._on_chips_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # ---- Entry + autocompletado ----
        entry_row = tk.Frame(self, bg=bg)
        entry_row.pack(fill="x", side="top", pady=(4, 0))

        self.entry = tk.Entry(
            entry_row, bg=entry_bg, fg=fg, insertbackground=accent, relief="flat"
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<comma>", self._on_comma)
        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<BackSpace>", self._on_backspace)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Escape>", lambda e: self._hide_suggestions())

        self._suggestion_box = None
        self._canvas_width = 0

        self._redraw_chips()

    # ---------- Layout ----------

    def _on_canvas_configure(self, event):
        self._canvas_width = event.width
        self.canvas.itemconfig(self._chips_window, width=event.width)
        self._redraw_chips()

    def _on_chips_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        h = self.chips_frame.winfo_reqheight()
        self.canvas.configure(height=max(32, h))

    def _redraw_chips(self):
        for w in self.chips_frame.winfo_children():
            w.destroy()

        row = tk.Frame(self.chips_frame, bg=self.bg)
        row.pack(fill="x", anchor="w")
        used_width = 0
        max_width = self._canvas_width or 400

        for tag in self._tags:
            color = self.tags_manager.color_de(tag)
            chip_width_est = 24 + len(tag) * 7

            if used_width + chip_width_est > max_width and used_width > 0:
                row = tk.Frame(self.chips_frame, bg=self.bg)
                row.pack(fill="x", anchor="w")
                used_width = 0

            chip = tk.Frame(row, bg=color)
            lbl = tk.Label(chip, text=tag, bg=color, fg="white",
                            font=("Segoe UI", 9), padx=6, pady=2)
            lbl.pack(side="left")
            close = tk.Label(chip, text="✕", bg=color, fg="white",
                              font=("Segoe UI", 8), padx=4, cursor="hand2")
            close.pack(side="left")
            close.bind("<Button-1>", lambda e, t=tag: self._remove_tag(t))

            chip.pack(side="left", padx=(0, 4), pady=2)
            used_width += chip_width_est + 4

    # ---------- Tags ----------

    def get_tags(self):
        return list(self._tags)

    def set_tags(self, tags):
        self._tags = []
        seen = set()
        for t in tags:
            t = t.strip()
            key = self.tags_manager.normalizar(t)
            if t and key not in seen:
                seen.add(key)
                self._tags.append(t)
        self._redraw_chips()

    def _add_tag(self, texto):
        texto = texto.strip().strip(",")
        if not texto:
            return
        key = self.tags_manager.normalizar(texto)
        if key in {self.tags_manager.normalizar(t) for t in self._tags}:
            return
        display = self.tags_manager.display_de(texto) if self.tags_manager.existe(texto) else texto
        self._tags.append(display)
        self._redraw_chips()

    def _remove_tag(self, tag):
        self._tags = [t for t in self._tags if t != tag]
        self._redraw_chips()

    # ---------- Teclado ----------

    def _on_return(self, event):
        self._commit_entry()
        return "break"

    def _on_comma(self, event):
        self._commit_entry()
        return "break"

    def _commit_entry(self):
        texto = self.entry.get()
        self.entry.delete(0, "end")
        self._add_tag(texto)
        self._hide_suggestions()

    def _on_backspace(self, event):
        if self.entry.get() == "" and self._tags:
            self._tags.pop()
            self._redraw_chips()

    def _on_keyrelease(self, event):
        if event.keysym in ("Return", "BackSpace", "Down", "Up", "Escape"):
            return
        texto = self.entry.get().strip()
        if not texto:
            self._hide_suggestions()
            return
        candidatos = [
            d["display"] for d in self.tags_manager.obtener_todos()
            if texto.lower() in d["display"].lower()
        ]
        if candidatos:
            self._show_suggestions(candidatos)
        else:
            self._hide_suggestions()

    def _on_arrow_down(self, event):
        if self._suggestion_box:
            self._suggestion_box.focus_set()
            self._suggestion_box.selection_set(0)
        return "break"

    # ---------- Autocompletado ----------

    def _show_suggestions(self, candidatos):
        if self._suggestion_box is None:
            self._suggestion_box = tk.Listbox(
                self, bg=self.entry_bg, fg=self.fg, relief="flat",
                highlightthickness=0
            )
            self._suggestion_box.bind("<<ListboxSelect>>", self._on_suggestion_pick)
            self._suggestion_box.bind("<Return>", self._on_suggestion_pick)
        self._suggestion_box.configure(height=min(5, len(candidatos)))
        self._suggestion_box.delete(0, "end")
        for c in candidatos[:8]:
            self._suggestion_box.insert("end", c)
        y = self.canvas.winfo_height() + self.entry.winfo_height() + 8
        self._suggestion_box.place(x=0, y=y, relwidth=1)

    def _hide_suggestions(self):
        if self._suggestion_box:
            self._suggestion_box.place_forget()

    def _on_suggestion_pick(self, event):
        if not self._suggestion_box or not self._suggestion_box.curselection():
            return
        idx = self._suggestion_box.curselection()[0]
        texto = self._suggestion_box.get(idx)
        self.entry.delete(0, "end")
        self._add_tag(texto)
        self._hide_suggestions()
        self.entry.focus_set()
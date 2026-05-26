# splash_screen.py
"""Splash screen modular con efecto plexus."""
from __future__ import annotations
import tkinter as tk
from typing import List
from dataclasses import dataclass
from models.splash_config  import SplashConfig
from utils.fragment_splash import FragmentSplash

@dataclass
class AnimationState:
    """Estado actual de la animación."""
    frame: int
    active_centers: List[tuple]
    progress: float

class TechPlexusSplash(tk.Toplevel):
    """Splash screen con animación de fragmentos convergentes."""
    
    def __init__(
        self, 
        parent: tk.Tk,
        config: SplashConfig,
        colors: dict,
        app_name: str,
        version: str,
        author: str
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.colors = colors
        self.app_name = app_name
        self.version = version
        self.author = author
        
        self._setup_window()
        self._create_background()
        self._create_core_visual()
        self._create_fragments()
        self._create_text_elements()
        self._start_animation()
        
        self.after(config.duration_ms, self.destroy)
    
    def _setup_window(self) -> None:
        """Configura las propiedades de la ventana."""
        self.overrideredirect(True)
        self.configure(bg=self.colors["bg"])
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self.config.width) // 2
        y = (screen_h - self.config.height) // 2
        self.geometry(f"{self.config.width}x{self.config.height}+{x}+{y}")
        self.attributes("-topmost", True)
    
    def _create_background(self) -> None:
        """Crea el patrón de fondo cuadriculado."""
        self.canvas = tk.Canvas(
            self,
            width=self.config.width,
            height=self.config.height,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Grid pattern
        spacing = 40
        for i in range(0, self.config.width, spacing):
            self.canvas.create_line(i, 0, i, self.config.height, 
                                   fill=self.colors["splash_bg"])
        for i in range(0, self.config.height, spacing):
            self.canvas.create_line(0, i, self.config.width, i,
                                   fill=self.colors["splash_bg"])
    
    def _create_core_visual(self) -> None:
        """Crea los elementos visuales del núcleo central."""
        cx, cy = self.config.center
        
        # Círculos concéntricos
        self.canvas.create_oval(
            cx-130, cy-130, cx+130, cy+130,
            outline=self.colors["border"],
            dash=(4, 4)
        )
        self.canvas.create_oval(
            cx-80, cy-80, cx+80, cy+80,
            outline=self.colors["accent_dk"],
            width=2
        )
    
    def _create_fragments(self) -> None:
        """Inicializa los fragmentos de la animación."""
        self.fragments: List[FragmentSplash] = []
        cx, cy = self.config.center
        
        for _ in range(self.config.num_fragments):
            frag = FragmentSplash(self.canvas, self.config, cx, cy)
            self.fragments.append(frag)
    
    def _create_text_elements(self) -> None:
        """Crea los elementos de texto."""
        x, y = self.config.content_x, self.config.content_y
        
        self.canvas.create_text(
            x, y,
            text=f"{self.app_name} {self.version}",
            fill=self.colors["text"],
            font=("Helvetica", 42, "bold"),
            anchor="w"
        )
        self.canvas.create_text(
            x, y + 50,
            text=f"by: {self.author}",
            fill=self.colors["text"],
            font=("Helvetica", 20, "bold"),
            anchor="w"
        )
        
        # Barra de progreso
        self.loading_bar = self.canvas.create_rectangle(
            x, y + 80, x, y + 95,
            fill=self.colors["accent"],
            outline=""
        )
        self.loading_text = self.canvas.create_text(
            x, y + 110,
            text="Iniciando módulos... 0%",
            fill=self.colors["muted"],
            font=("Helvetica", 11),
            anchor="w"
        )
    
    def _start_animation(self) -> None:
        """Inicia el loop de animación."""
        self.animation_state = AnimationState(
            frame=0,
            active_centers=[],
            progress=0.0
        )
        self._animate()
    
    def _animate(self) -> None:
        """Bucle principal de animación."""
        self.animation_state.frame += 1
        frame = self.animation_state.frame
        self.canvas.delete("plexus_line")
        
        active_centers: List[tuple] = []
        
        # Mover fragmentos
        for frag in self.fragments:
            if frag.finished or frame <= frag.delay:
                continue
            
            coords = self.canvas.coords(frag.id)
            cur_x = (coords[0] + coords[4]) / 2
            cur_y = (coords[1] + coords[5]) / 2
            
            dx = frag.target_x - cur_x
            dy = frag.target_y - cur_y
            move_x = dx * frag.speed
            move_y = dy * frag.speed
            
            self.canvas.move(frag.id, move_x, move_y)
            active_centers.append((cur_x + move_x, cur_y + move_y))
            
            if abs(dx) < 2 and abs(dy) < 2:
                frag.finished = True
        
        # Dibujar líneas plexus
        limit = min(self.config.max_line_connections, len(active_centers))
        threshold = self.config.line_distance_threshold
        
        for i in range(limit):
            x1, y1 = active_centers[i]
            for j in range(i + 1, limit):
                x2, y2 = active_centers[j]
                dist_sq = (x2 - x1)**2 + (y2 - y1)**2
                if dist_sq < threshold:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors["accent_dk"],
                        tags="plexus_line"
                    )
        
        # Actualizar barra de progreso
        progress = min(1.0, frame / self.config.max_frames)
        self.animation_state.progress = progress
        
        bar_width = (self.config.content_x + (self.config.content_x * 2 * progress))
        self.canvas.coords(
            self.loading_bar,
            self.config.content_x,
            self.config.content_y + 80,
            bar_width,
            self.config.content_y + 95
        )
        
        pct = int(progress * 100)
        self.canvas.itemconfig(
            self.loading_text,
            text=f"Construyendo interfaz... {pct}%"
        )
        
        # Continuar o finalizar
        if frame < self.config.max_frames:
            self.after(self.config.frame_delay_ms, self._animate)
        else:
            self._on_animation_complete()
    
    def _on_animation_complete(self) -> None:
        """Callback cuando la animación termina."""
        self.canvas.itemconfig(
            self.loading_text,
            text="¡Iniciando sistema! 100%"
        )
        cx, cy = self.config.center
        self.canvas.create_oval(
            cx-120, cy-120, cx+120, cy+120,
            fill="",
            outline=self.colors["accent"],
            width=4
        )

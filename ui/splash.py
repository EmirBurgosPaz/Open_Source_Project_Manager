import tkinter as tk
import random
import math

# Importamos tu diccionario de colores desde tu archivo de configuración
from config import C 

class TechPlexusSplash(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.overrideredirect(True)
        self.configure(bg=C["bg"])
        
        self.w, self.h = 1000, 450 
        x = (self.winfo_screenwidth() - self.w) // 2
        y = (self.winfo_screenheight() - self.h) // 2
        self.geometry(f"{self.w}x{self.h}+{x}+{y}")
        
        self.canvas = tk.Canvas(self, width=self.w, height=self.h, bg=C["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # --- Dibujo del fondo ---
        for i in range(0, self.w, 40):
            self.canvas.create_line(i, 0, i, self.h, fill="#1F1F26")
        for i in range(0, self.h, 40):
            self.canvas.create_line(0, i, self.w, i, fill="#1F1F26")
            
        self.core_x, self.core_y = 250, 225
        self.canvas.create_oval(self.core_x-130, self.core_y-130, self.core_x+130, self.core_y+130, outline=C["border"], dash=(4, 4))
        self.canvas.create_oval(self.core_x-80, self.core_y-80, self.core_x+80, self.core_y+80, outline=C["accent_dk"], width=2)
        
        # --- Fragmentos ---
        self.num_fragments = 70
        self.fragments = []
        for i in range(self.num_fragments):
            size = random.randint(4, 12)
            vertices = [0, -size, size, 0, 0, size, -size, 0] 
            
            start_angle = random.uniform(0, 2 * math.pi)
            start_dist = random.uniform(400, 800)
            start_x = self.core_x + start_dist * math.cos(start_angle)
            start_y = self.core_y + start_dist * math.sin(start_angle)
            
            color = random.choice([C["accent"], C["accent_dk"], C["muted"], C["text"]])
            shape_id = self.canvas.create_polygon(vertices, fill=color, outline="")
            self.canvas.move(shape_id, start_x, start_y)
            
            target_angle = random.uniform(0, 2 * math.pi)
            target_dist = random.uniform(10, 150)
            target_x = self.core_x + target_dist * math.cos(target_angle)
            target_y = self.core_y + target_dist * math.sin(target_angle)
            
            self.fragments.append({
                "id": shape_id, "target_x": target_x, "target_y": target_y,
                "delay": random.randint(0, 50), "speed_multiplier": random.uniform(0.04, 0.09),
                "finished": False
            })
            
        # --- Textos ---
        self.canvas.create_text(550, 230, text="Gestor de tareas", fill=C["text"], font=("Helvetica", 42, "bold"), anchor="w")
        
        self.loading_bar = self.canvas.create_rectangle(550, 280, 550, 283, fill=C["accent"], outline="")
        self.loading_text = self.canvas.create_text(550, 310, text="Iniciando módulos... 0%", fill=C["muted"], font=("Helvetica", 11), anchor="w")
        
        self.frame = 0
        self.max_frames = 200 
        
        self.attributes("-topmost", True)
        
        # Iniciar animación
        self.animate()
        
        # Destruir esta ventana después de 3500ms
        self.after(3500, self.destroy)
        
    def animate(self):
        self.frame += 1
        self.canvas.delete("plexus_line")
        active_centers = []
        
        for frag in self.fragments:
            if frag["finished"]:
                continue
            if self.frame > frag["delay"]:
                coords = self.canvas.coords(frag["id"])
                cur_x = (coords[0] + coords[4]) / 2
                cur_y = (coords[1] + coords[5]) / 2
                dx = frag["target_x"] - cur_x
                dy = frag["target_y"] - cur_y
                move_x, move_y = dx * frag["speed_multiplier"], dy * frag["speed_multiplier"]
                
                self.canvas.move(frag["id"], move_x, move_y)
                active_centers.append((cur_x + move_x, cur_y + move_y))
                
                if abs(dx) < 2 and abs(dy) < 2:
                    frag["finished"] = True

        limit = min(25, len(active_centers))
        for i in range(limit):
            x1, y1 = active_centers[i]
            for j in range(i + 1, limit):
                x2, y2 = active_centers[j]
                if (x2 - x1)**2 + (y2 - y1)**2 < 4900: 
                    self.canvas.create_line(x1, y1, x2, y2, fill=C["accent_dk"], tags="plexus_line")

        porcentaje = min(100, int((self.frame / self.max_frames) * 100))
        self.canvas.coords(self.loading_bar, 550, 280, 550 + (porcentaje * 2), 283)
        self.canvas.itemconfig(self.loading_text, text=f"Construyendo interfaz... {porcentaje}%")
        
        if self.frame < self.max_frames:
            self.after(16, self.animate)
        else:
            self.canvas.itemconfig(self.loading_text, text="¡Iniciando sistema! 100%")
            self.canvas.create_oval(self.core_x-120, self.core_y-120, self.core_x+120, self.core_y+120, fill="", outline=C["accent"], width=4)
# fragment.py
"""Clase para manejar los fragmentos individuales."""
import random
import math
from config import C 


class FragmentSplash:
    """Representa un fragmento animado en la splash screen."""
    
    def __init__(self, canvas, config, core_x: int, core_y: int):
        self.config = config
        self._setup_position(core_x, core_y)
        self._create_shape(canvas)
        self.finished = False
        
    def _setup_position(self, core_x: int, core_y: int) -> None:
        """Calcula posición inicial y objetivo."""
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(self.config.start_distance_min, 
                            self.config.start_distance_max)
        self.start_x = core_x + dist * math.cos(angle)
        self.start_y = core_y + dist * math.sin(angle)
        
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(self.config.target_distance_min,
                            self.config.target_distance_max)
        self.target_x = core_x + dist * math.cos(angle)
        self.target_y = core_y + dist * math.sin(angle)
        
        self.delay = random.randint(0, 50)
        self.speed = random.uniform(self.config.speed_min, 
                                   self.config.speed_max)
    
    def _create_shape(self, canvas) -> None:
        """Crea la forma del fragmento."""
        size = random.randint(self.config.min_fragment_size,
                             self.config.max_fragment_size)
        vertices = [0, -size, size, 0, 0, size, -size, 0]
        colors = [C["accent"], C["accent_dk"], C["muted"], C["text"]]
        self.id = canvas.create_polygon(vertices, fill=random.choice(colors), outline="")
        canvas.move(self.id, self.start_x, self.start_y)

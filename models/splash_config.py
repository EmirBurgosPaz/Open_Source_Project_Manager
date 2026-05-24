# splash_config.py
"""Configuración centralizada para la splash screen."""
from dataclasses import dataclass
from config import C
from typing import Tuple

@dataclass(frozen=True)
class SplashConfig:
    """Configuración para la splash screen."""
    # Ventana
    width: int = 1000
    height: int = 450
    
    # Animación
    max_frames: int = 250
    frame_delay_ms: int = 16
    duration_ms: int = 3000
    
    # Efecto plexus
    num_fragments: int = 200
    min_fragment_size: int = 2
    max_fragment_size: int = 12
    start_distance_min: int = 400
    start_distance_max: int = 800
    target_distance_min: int = 10
    target_distance_max: int = 150
    
    # Líneas plexus
    max_line_connections: int = 50
    line_distance_threshold: int = 5000
    
    # Posición del contenido
    content_x: int = 400
    content_y: int = 230
    
    # Velocidades
    speed_min: float = 0.04
    speed_max: float = 0.09

    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.width // 4, self.height // 2)

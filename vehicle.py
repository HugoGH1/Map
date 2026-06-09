import pygame
import config

class Vehiculo:
    def __init__(self, color, ruta):
        self.color = color
        self.ruta = list(ruta) if ruta else []
        self.indice_tramo = 0
        self.progreso_tramo = 0.0
        self.activo = False
        self.px = 0.0
        self.py = 0.0
        
    def reiniciar(self, ruta):
        self.ruta = list(ruta) if ruta else []
        self.indice_tramo = 0
        self.progreso_tramo = 0.0
        self.activo = len(self.ruta) > 1
        if self.activo:
            self.px, self.py = config.obtener_coordenadas_pixel(self.ruta[0][0], self.ruta[0][1])
            
    def actualizar(self, dt, grafo):
        if not self.activo or len(self.ruta) <= 1:
            return
            
        if self.indice_tramo >= len(self.ruta) - 1:
            self.activo = False
            return
            
        u = self.ruta[self.indice_tramo]
        v = self.ruta[self.indice_tramo + 1]
        
        # Obtener el peso del tramo en el grafo para la velocidad
        peso = 1.0
        for vecino, p in grafo.get(u, []):
            if vecino == v:
                peso = p
                break
                
        if peso >= 999.0:
            # Calle bloqueada, el vehículo no puede avanzar
            return
            
        # Velocidad de simulación: 1.0 minuto de peso toma 0.8 segundos de tiempo real
        duracion_tramo = peso * 0.8
        
        self.progreso_tramo += dt / duracion_tramo
        if self.progreso_tramo >= 1.0:
            self.indice_tramo += 1
            self.progreso_tramo = 0.0
            
            if self.indice_tramo >= len(self.ruta) - 1:
                self.activo = False
                # Posicionar exactamente en el último nodo
                self.px, self.py = config.obtener_coordenadas_pixel(self.ruta[-1][0], self.ruta[-1][1])
                return
                
        # Calcular coordenadas interpoladas
        u_actual = self.ruta[self.indice_tramo]
        v_actual = self.ruta[self.indice_tramo + 1]
        x1, y1 = config.obtener_coordenadas_pixel(u_actual[0], u_actual[1])
        x2, y2 = config.obtener_coordenadas_pixel(v_actual[0], v_actual[1])
        
        self.px = x1 + (x2 - x1) * self.progreso_tramo
        self.py = y1 + (y2 - y1) * self.progreso_tramo
        
    def dibujar(self, superficie):
        if not self.activo:
            return
        # Dibujar sombra
        pygame.draw.circle(superficie, (180, 180, 180), (int(self.px) + 2, int(self.py) + 2), 7)
        # Dibujar chasis del coche
        pygame.draw.circle(superficie, (44, 62, 80), (int(self.px), int(self.py)), 7)
        pygame.draw.circle(superficie, self.color, (int(self.px), int(self.py)), 5)
        # Dibujar luz/brillo
        pygame.draw.circle(superficie, (255, 255, 255), (int(self.px) - 1, int(self.py) - 1), 2)

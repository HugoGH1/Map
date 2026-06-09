import pygame
import sys
import heapq
import math
import random

# --- CONFIGURACIÓN DE LA PANTALLA Y MAPA ---
ANCHO, ALTO = 950, 850
DIM_MANZANAS = 10  # 10x10 manzanas
NODOS_LINEA = DIM_MANZANAS + 1  # 11x11 esquinas
TAM_CUADRA = 60  
MARGEN = 120  

# Colores (RGB)
COLOR_BG = (245, 245, 245)
COLOR_CALLE = (180, 180, 180)
COLOR_TEXTO = (44, 62, 80)
COLOR_MANZANA_NORMAL = (220, 220, 220)

# Colores de las Incidencias 
COLOR_TRAFICO = (241, 196, 15)   # Amarillo
COLOR_BLOQUEO = (231, 76, 60)    # Rojo
COLOR_RADAR = (155, 89, 182)     # Morado

# Colores de las Rutas 
COLOR_RUTA1 = (46, 204, 113)     # Verde (Opción 1) 
COLOR_RUTA2 = (52, 152, 219)     # Azul (Opción 2) 

# Colores de la Interfaz Sidebar
COLOR_PANEL = (235, 240, 245)
COLOR_BORDE_PANEL = (200, 205, 210)
COLOR_BOTON_NORMAL = (52, 152, 219)
COLOR_BOTON_HOVER = (41, 128, 185)
COLOR_BOTON_ACCION = (46, 204, 113)
COLOR_BOTON_ACCION_HOVER = (39, 174, 96)
COLOR_BOTON_PELIGRO = (231, 76, 60)
COLOR_BOTON_PELIGRO_HOVER = (192, 57, 43)

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Proyecto IA: 2 Alternativas de Ruta Inteligente + Simulación")
fuente = pygame.font.SysFont("Arial", 13)
fuente_negrita = pygame.font.SysFont("Arial", 14, bold=True)

# --- CONFIGURACIÓN DE LOS BOTONES ---
rect_btn_anim = pygame.Rect(755, 380, 160, 35)
rect_btn_limpiar = pygame.Rect(755, 430, 160, 35)
rect_btn_random = pygame.Rect(755, 480, 160, 35)
rect_btn_reset = pygame.Rect(755, 530, 160, 35)

# --- CLASE VEHÍCULO PARA LA SIMULACIÓN ---
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
            self.px, self.py = obtener_coordenadas_pixel(self.ruta[0][0], self.ruta[0][1])
            
    def actualizar(self, dt):
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
                self.px, self.py = obtener_coordenadas_pixel(self.ruta[-1][0], self.ruta[-1][1])
                return
                
        # Calcular coordenadas interpoladas
        u_actual = self.ruta[self.indice_tramo]
        v_actual = self.ruta[self.indice_tramo + 1]
        x1, y1 = obtener_coordenadas_pixel(u_actual[0], u_actual[1])
        x2, y2 = obtener_coordenadas_pixel(v_actual[0], v_actual[1])
        
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

# --- ESTRUCTURAS DE DATOS ---
grafo = {}
manzanas_incidencias = {}

# Puntos de navegación establecidos por el usuario 
nodo_inicio = None
nodo_fin = None

# Rutas calculadas finales
camino_ruta1 = []
camino_ruta2 = []
tiempo_ruta1 = 0
tiempo_ruta2 = 0

# Vehículos para la animación
vehiculo1 = Vehiculo(COLOR_RUTA1, [])
vehiculo2 = Vehiculo(COLOR_RUTA2, [])

def inicializar_estructuras():
    global grafo, manzanas_incidencias, nodo_inicio, nodo_fin, camino_ruta1, camino_ruta2, tiempo_ruta1, tiempo_ruta2
    grafo = {}
    manzanas_incidencias = {}
    nodo_inicio = None
    nodo_fin = None
    camino_ruta1 = []
    camino_ruta2 = []
    tiempo_ruta1 = 0
    tiempo_ruta2 = 0
    
    for x in range(NODOS_LINEA):
        for y in range(NODOS_LINEA):
            grafo[(x, y)] = []
            
    for mx in range(DIM_MANZANAS):
        for my in range(DIM_MANZANAS):
            manzanas_incidencias[(mx, my)] = "NORMAL"
            
    actualizar_pesos_mapa()
    
    if vehiculo1:
        vehiculo1.reiniciar([])
    if vehiculo2:
        vehiculo2.reiniciar([])

def actualizar_pesos_mapa():
    """Reconstruye el grafo con las penalizaciones dinámicas de las manzanas [cite: 10]"""
    for esquina in grafo:
        grafo[esquina] = []
        
    for x in range(NODOS_LINEA):
        for y in range(NODOS_LINEA):
            # --- Calles Horizontales (Filas) --- [cite: 4]
            if x < DIM_MANZANAS:
                peso = calcular_peso_tramo(x, y, x + 1, y)
                if y % 2 == 0:  # Fila par: Este (Derecha) [cite: 4]
                    grafo[(x, y)].append(((x + 1, y), peso))
                else:          # Fila impar: Oeste (Izquierda) [cite: 4]
                    grafo[(x + 1, y)].append(((x, y), peso))
            
            # --- Calles Verticales (Columnas) --- [cite: 4]
            if y < DIM_MANZANAS:
                peso = calcular_peso_tramo(x, y, x, y + 1)
                if x % 2 == 0:  # Columna par: Sur (Abajo) [cite: 4]
                    grafo[(x, y)].append(((x, y + 1), peso))
                else:          # Columna impar: Norte (Arriba) [cite: 4]
                    grafo[(x, y + 1)].append(((x, y), peso))

def calcular_peso_tramo(x1, y1, x2, y2):
    """Obtiene los minutos que toma transitar una cuadra según su entorno """
    manzanas_vecinas = []
    
    if y1 == y2: # Tramo horizontal
        my_arriba = y1 - 1
        my_abajo = y1
        mx = min(x1, x2)
        if my_arriba >= 0: manzanas_vecinas.append(manzanas_incidencias[(mx, my_arriba)])
        if my_abajo < DIM_MANZANAS: manzanas_vecinas.append(manzanas_incidencias[(mx, my_abajo)])
    else: # Tramo vertical
        mx_izquierda = x1 - 1
        mx_derecha = x1
        my = min(y1, y2)
        if mx_izquierda >= 0: manzanas_vecinas.append(manzanas_incidencias[(mx_izquierda, my)])
        if mx_derecha < DIM_MANZANAS: manzanas_vecinas.append(manzanas_incidencias[(mx_derecha, my)])
        
    if "BLOQUEO" in manzanas_vecinas:
        return 999.0  # Calle cerrada (Costo inaccesible) [cite: 7]
    if "TRAFICO" in manzanas_vecinas:
        return 3.0    # Tráfico intenso = 3 minutos [cite: 8, 12]
    if "RADAR" in manzanas_vecinas:
        return 2.0    # Radar de policía frena el flujo = 2 minutos [cite: 9]
        
    return 1.0        # Tiempo normal = 1 minuto [cite: 12]

# --- 🧠 ALGORITMO INTELIGENTE A* (A-ESTRELLA) ---
def heuristica(a, b):
    # Distancia Manhattan (ideal para calles cuadradas tipo cuadrículas)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def algoritmo_a_estrella(inicio, fin, aristas_penalizadas=None):
    """Encuentra la ruta óptima considerando costos dinámicos y penalizaciones externas"""
    if aristas_penalizadas is None:
        aristas_penalizadas = set()
        
    queue = [(0, inicio)]
    costos = {inicio: 0}
    padres = {inicio: None}
    
    while queue:
        costo_actual, actual = heapq.heappop(queue)
        
        if actual == fin:
            # Reconstruir el camino de fin a inicio
            camino = []
            curr = fin
            while curr is not None:
                camino.append(curr)
                curr = padres[curr]
            return camino[::-1], costos[fin]
            
        for vecino, peso in grafo.get(actual, []):
            # Si esta cuadra fue bloqueada por incidencia, el algoritmo la ignora [cite: 7]
            if peso >= 999.0:
                continue
                
            # Si es la segunda opción, castigamos los tramos que tomó la primera ruta 
            costo_tramo = peso
            if (actual, vecino) in aristas_penalizadas:
                costo_tramo += 15.0  # Penalización alta para forzar una alternativa real 
                
            nuevo_costo = costos[actual] + costo_tramo
            
            if vecino not in costos or nuevo_costo < costos[vecino]:
                costos[vecino] = nuevo_costo
                prioridad = nuevo_costo + heuristica(vecino, fin)
                padres[vecino] = actual
                heapq.heappush(queue, (prioridad, vecino))
                
    return [], 0

def calcular_ambas_rutas():
    """Calcula la mejor ruta y la alternativa basándose en la petición del profe """
    global camino_ruta1, camino_ruta2, tiempo_ruta1, tiempo_ruta2
    if not nodo_inicio or not nodo_fin:
        camino_ruta1, camino_ruta2 = [], []
        tiempo_ruta1, tiempo_ruta2 = 0, 0
        vehiculo1.reiniciar([])
        vehiculo2.reiniciar([])
        return
        
    # 1. Obtener la Primera Opción (La más óptima) 
    camino_ruta1, tiempo_ruta1 = algoritmo_a_estrella(nodo_inicio, nodo_fin)
    
    # 2. Generar la Segunda Opción (Ruta Alternativa) 
    if camino_ruta1:
        tramos_utilizados = set()
        for i in range(len(camino_ruta1) - 1):
            tramos_utilizados.add((camino_ruta1[i], camino_ruta1[i+1]))
            
        # Corremos A* penalizando los tramos de la primera ruta 
        camino_ruta2, tiempo_total_penalizado = algoritmo_a_estrella(nodo_inicio, nodo_fin, tramos_utilizados)
        
        # Calcular el tiempo real de la Ruta 2 (sin la penalización artificial) [cite: 12]
        if camino_ruta2:
            tiempo_real = 0
            for i in range(len(camino_ruta2) - 1):
                u, v = camino_ruta2[i], camino_ruta2[i+1]
                for vecino, peso in grafo[u]:
                    if vecino == v:
                        tiempo_real += peso
            tiempo_ruta2 = tiempo_real
        else:
            tiempo_ruta2 = 0
    else:
        camino_ruta2, tiempo_ruta2 = [], 0

    # Reiniciar vehículos con las nuevas rutas
    vehiculo1.reiniciar(camino_ruta1)
    vehiculo2.reiniciar(camino_ruta2)

# --- AUXILIARES COORDENADAS ---
def obtener_coordenadas_pixel(x, y):
    return MARGEN + x * TAM_CUADRA, MARGEN + y * TAM_CUADRA

def detectar_clic_manzana(px, py):
    for mx in range(DIM_MANZANAS):
        for my in range(DIM_MANZANAS):
            x_ini = MARGEN + mx * TAM_CUADRA + 5
            y_ini = MARGEN + my * TAM_CUADRA + 5
            if x_ini <= px <= x_ini + TAM_CUADRA - 10 and y_ini <= py <= y_ini + TAM_CUADRA - 10:
                return mx, my
    return None

def detectar_clic_esquina(px, py):
    """Detecta a qué esquina (nodo) le dio clic el usuario"""
    for x in range(NODOS_LINEA):
        for y in range(NODOS_LINEA):
            cx, cy = obtener_coordenadas_pixel(x, y)
            # Margen de error por el clic del mouse de 15 píxeles alrededor del nodo
            if math.hypot(px - cx, py - cy) < 15:
                return x, y
    return None

# --- AUXILIAR DE INTERFAZ: DIBUJAR BOTÓN ---
def dibujar_boton(superficie, rect, texto, color_base, color_hover, pos_raton):
    hover = rect.collidepoint(pos_raton)
    color = color_hover if hover else color_base
    pygame.draw.rect(superficie, color, rect, border_radius=6)
    pygame.draw.rect(superficie, COLOR_TEXTO, rect, width=1, border_radius=6)
    
    # Texto centrado
    color_texto = (255, 255, 255)
    if color_base == COLOR_TRAFICO:
        color_texto = COLOR_TEXTO
        
    lbl = fuente_negrita.render(texto, True, color_texto)
    lbl_rect = lbl.get_rect(center=rect.center)
    superficie.blit(lbl, lbl_rect)

# --- RENDERIZADO VISUAL ---
def dibujar_sistema():
    pantalla.fill(COLOR_BG)
    pos_raton = pygame.mouse.get_pos()
    
    # 1. Dibujar Manzanas (Cuerpo) [cite: 3]
    for mx in range(DIM_MANZANAS):
        for my in range(DIM_MANZANAS):
            px = MARGEN + mx * TAM_CUADRA + 6
            py = MARGEN + my * TAM_CUADRA + 6
            tam = TAM_CUADRA - 12
            
            estado = manzanas_incidencias[(mx, my)]
            color = COLOR_MANZANA_NORMAL
            if estado == "TRAFICO": color = COLOR_TRAFICO
            elif estado == "BLOQUEO": color = COLOR_BLOQUEO
            elif estado == "RADAR": color = COLOR_RADAR
            
            pygame.draw.rect(pantalla, color, (px, py, tam, tam), border_radius=4)
            if estado != "NORMAL":
                texto_m = fuente.render(estado[0], True, (255, 255, 255) if estado != "TRAFICO" else COLOR_TEXTO)
                pantalla.blit(texto_m, (px + tam//2 - 4, py + tam//2 - 6))

    # 2. Dibujar Calles de un solo sentido [cite: 4]
    for origen, destinos in grafo.items():
        x1, y1 = obtener_coordenadas_pixel(origen[0], origen[1])
        for destino, peso in destinos:
            x2, y2 = obtener_coordenadas_pixel(destino[0], destino[1])
            color_c = COLOR_CALLE
            grosor = 2
            if peso == 999.0: color_c = COLOR_BLOQUEO; grosor = 3
            elif peso == 3.0: color_c = COLOR_TRAFICO; grosor = 3
            elif peso == 2.0: color_c = COLOR_RADAR; grosor = 3
            
            pygame.draw.line(pantalla, color_c, (x1, y1), (x2, y2), grosor)
            
            # Flechas de tránsito [cite: 4]
            mx_f, my_f = (x1 + x2) / 2, (y1 + y2) / 2
            color_fl = (110, 110, 110) if peso == 1.0 else (255, 255, 255)
            if x1 < x2: pygame.draw.polygon(pantalla, color_fl, [(mx_f+5, my_f), (mx_f-4, my_f-3), (mx_f-4, my_f+3)])
            elif x1 > x2: pygame.draw.polygon(pantalla, color_fl, [(mx_f-5, my_f), (mx_f+4, my_f-3), (mx_f+4, my_f+3)])
            elif y1 < y2: pygame.draw.polygon(pantalla, color_fl, [(mx_f, my_f+5), (mx_f-3, my_f-4), (mx_f+3, my_f-4)])
            elif y1 > y2: pygame.draw.polygon(pantalla, color_fl, [(mx_f, my_f-5), (mx_f-3, my_f+4), (mx_f+3, my_f+4)])

    # 3. PINTAR LAS DOS OPCIONES DE RECORRIDO (Líneas gruesas superpuestas) 
    # Dibujar la Opción 2 primero (Azul) 
    if len(camino_ruta2) > 1:
        for i in range(len(camino_ruta2) - 1):
            xa, ya = obtener_coordenadas_pixel(camino_ruta2[i][0], camino_ruta2[i][1])
            xb, yb = obtener_coordenadas_pixel(camino_ruta2[i+1][0], camino_ruta2[i+1][1])
            pygame.draw.line(pantalla, COLOR_RUTA2, (xa+2, ya+2), (xb+2, yb+2), 5)

    # Dibujar la Opción 1 (Verde) 
    if len(camino_ruta1) > 1:
        for i in range(len(camino_ruta1) - 1):
            xa, ya = obtener_coordenadas_pixel(camino_ruta1[i][0], camino_ruta1[i][1])
            xb, yb = obtener_coordenadas_pixel(camino_ruta1[i+1][0], camino_ruta1[i+1][1])
            pygame.draw.line(pantalla, COLOR_RUTA1, (xa-2, ya-2), (xb-2, yb-2), 5)

    # 4. Dibujar Esquinas (Nodos)
    for x in range(NODOS_LINEA):
        for y in range(NODOS_LINEA):
            px, py = obtener_coordenadas_pixel(x, y)
            pygame.draw.circle(pantalla, (44, 62, 80), (px, py), 4)

    # 4.5 Dibujar Vehículos Animados
    vehiculo1.dibujar(pantalla)
    vehiculo2.dibujar(pantalla)

    # Marcar visualmente los marcadores de Inicio y Fin 
    if nodo_inicio:
        ix, iy = obtener_coordenadas_pixel(nodo_inicio[0], nodo_inicio[1])
        pygame.draw.circle(pantalla, COLOR_RUTA1, (ix, iy), 10)
        pygame.draw.circle(pantalla, (255, 255, 255), (ix, iy), 4)
    if nodo_fin:
        fx, fy = obtener_coordenadas_pixel(nodo_fin[0], nodo_fin[1])
        pygame.draw.circle(pantalla, COLOR_RUTA2, (fx, fy), 10)
        pygame.draw.circle(pantalla, (255, 255, 255), (fx, fy), 4)

    # 5. Texto Informativo del Panel Superior 
    cont_incidencias = sum(1 for v in manzanas_incidencias.values() if v != "NORMAL")
    
    t1 = fuente_negrita.render("CONTROLES DE LA SIMULACIÓN:", True, COLOR_TEXTO)
    t2 = fuente.render("• Clic Izquierdo en las manzanas del mapa para alternar Incidencias (Máx 3 en pantalla).", True, COLOR_TEXTO)
    t3 = fuente.render("• Clic Derecho en esquinas para colocar/mover: 1er Clic = INICIO, 2do Clic = FIN.", True, COLOR_TEXTO)
    t4 = fuente.render(f"• Incidencias en manzanas: {cont_incidencias} / 3", True, COLOR_TEXTO if cont_incidencias <= 3 else COLOR_BLOQUEO)
    
    pantalla.blit(t1, (20, 15))
    pantalla.blit(t2, (20, 35))
    pantalla.blit(t3, (20, 55))
    pantalla.blit(t4, (20, 75))

    # 6. DIBUJAR PANEL LATERAL (Estadísticas y Botones)
    pygame.draw.rect(pantalla, COLOR_PANEL, (740, 120, 190, 600), border_radius=10)
    pygame.draw.rect(pantalla, COLOR_BORDE_PANEL, (740, 120, 190, 600), width=2, border_radius=10)
    
    # Título Estadísticas
    lbl_titulo = fuente_negrita.render("ESTADÍSTICAS", True, COLOR_TEXTO)
    pantalla.blit(lbl_titulo, (755, 140))
    pygame.draw.line(pantalla, COLOR_BORDE_PANEL, (750, 165), (920, 165), 1)
    
    # Ruta 1 (Verde)
    lbl_r1_title = fuente_negrita.render("Ruta 1 (Verde)", True, COLOR_RUTA1)
    pantalla.blit(lbl_r1_title, (755, 175))
    if camino_ruta1:
        txt_t1 = fuente.render(f"Tiempo: {tiempo_ruta1:.1f} min", True, COLOR_TEXTO)
        txt_d1 = fuente.render(f"Dist: {len(camino_ruta1) - 1} cuadras", True, COLOR_TEXTO)
    else:
        txt_t1 = fuente.render("Sin ruta disponible", True, COLOR_TEXTO)
        txt_d1 = fuente.render("-", True, COLOR_TEXTO)
    pantalla.blit(txt_t1, (755, 195))
    pantalla.blit(txt_d1, (755, 212))
    
    # Ruta 2 (Azul)
    lbl_r2_title = fuente_negrita.render("Ruta 2 (Azul)", True, COLOR_RUTA2)
    pantalla.blit(lbl_r2_title, (755, 240))
    if camino_ruta2:
        txt_t2 = fuente.render(f"Tiempo: {tiempo_ruta2:.1f} min", True, COLOR_TEXTO)
        txt_d2 = fuente.render(f"Dist: {len(camino_ruta2) - 1} cuadras", True, COLOR_TEXTO)
    else:
        txt_t2 = fuente.render("Sin ruta alternativa", True, COLOR_TEXTO)
        txt_d2 = fuente.render("-", True, COLOR_TEXTO)
    pantalla.blit(txt_t2, (755, 260))
    pantalla.blit(txt_d2, (755, 277))
    
    # Comparativa de tiempos
    pygame.draw.line(pantalla, COLOR_BORDE_PANEL, (750, 305), (920, 305), 1)
    if camino_ruta1 and camino_ruta2:
        if tiempo_ruta1 > 0:
            diff = ((tiempo_ruta2 - tiempo_ruta1) / tiempo_ruta1) * 100
            if diff > 0:
                txt_comp = fuente.render(f"R2 es {diff:.1f}% +lenta", True, COLOR_TEXTO)
            else:
                txt_comp = fuente.render("Mismo tiempo", True, COLOR_TEXTO)
        else:
            txt_comp = fuente.render("-", True, COLOR_TEXTO)
    else:
        txt_comp = fuente.render("N/A", True, COLOR_TEXTO)
    pantalla.blit(txt_comp, (755, 315))
    
    # Separador Acciones
    pygame.draw.line(pantalla, COLOR_BORDE_PANEL, (750, 345), (920, 345), 1)
    lbl_acciones = fuente_negrita.render("ACCIONES", True, COLOR_TEXTO)
    pantalla.blit(lbl_acciones, (755, 355))
    
    # Dibujar los Botones
    dibujar_boton(pantalla, rect_btn_anim, "▶ Simular", COLOR_BOTON_ACCION, COLOR_BOTON_ACCION_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_limpiar, "Limpiar Mapa", COLOR_BOTON_NORMAL, COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_random, "Incidencias Rnd", COLOR_BOTON_NORMAL, COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_reset, "Reiniciar Todo", COLOR_BOTON_PELIGRO, COLOR_BOTON_PELIGRO_HOVER, pos_raton)

    # 7. Barra Inferior de Acotaciones (SECCIÓN CORREGIDA Y LIMPIA)
    pygame.draw.rect(pantalla, COLOR_TRAFICO, (40, 790, 15, 15))
    pantalla.blit(fuente.render("Tráfico (3 min)", True, COLOR_TEXTO), (65, 790))
    
    pygame.draw.rect(pantalla, COLOR_BLOQUEO, (200, 790, 15, 15))
    pantalla.blit(fuente.render("Bloqueo (Cerrada)", True, COLOR_TEXTO), (225, 790))
    
    pygame.draw.rect(pantalla, COLOR_RADAR, (400, 790, 15, 15))
    pantalla.blit(fuente.render("Radar (2 min)", True, COLOR_TEXTO), (425, 790))

inicializar_estructuras()

# --- BUCLE PRINCIPAL DE INTERACCIÓN (SECCIÓN CORREGIDA Y LIMPIA) ---
ejecutando = True
clock = pygame.time.Clock()

while ejecutando:
    # dt es la cantidad de segundos transcurridos desde el último frame
    dt = clock.tick(60) / 1000.0
    
    # Actualizar posiciones de los vehículos
    vehiculo1.actualizar(dt)
    vehiculo2.actualizar(dt)
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
            
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            pos_raton = pygame.mouse.get_pos()
            
            # --- CLIC IZQUIERDO: CONFIGURAR INCIDENCIAS O PULSAR BOTONES ---
            if evento.button == 1: 
                # Comprobar clics en botones de la barra lateral primero
                if rect_btn_anim.collidepoint(pos_raton):
                    vehiculo1.reiniciar(camino_ruta1)
                    vehiculo2.reiniciar(camino_ruta2)
                elif rect_btn_limpiar.collidepoint(pos_raton):
                    for mx in range(DIM_MANZANAS):
                        for my in range(DIM_MANZANAS):
                            manzanas_incidencias[(mx, my)] = "NORMAL"
                    actualizar_pesos_mapa()
                    calcular_ambas_rutas()
                elif rect_btn_random.collidepoint(pos_raton):
                    # Limpiar incidencias previas
                    for mx in range(DIM_MANZANAS):
                        for my in range(DIM_MANZANAS):
                            manzanas_incidencias[(mx, my)] = "NORMAL"
                    
                    # Generar exactamente 3 incidencias aleatorias en el mapa
                    todas = [(mx, my) for mx in range(DIM_MANZANAS) for my in range(DIM_MANZANAS)]
                    seleccionadas = random.sample(todas, 3)
                    tipos = ["TRAFICO", "BLOQUEO", "RADAR"]
                    for idx, pos in enumerate(seleccionadas):
                        manzanas_incidencias[pos] = tipos[idx]
                        
                    actualizar_pesos_mapa()
                    calcular_ambas_rutas()
                elif rect_btn_reset.collidepoint(pos_raton):
                    inicializar_estructuras()
                else:
                    # Si no se clica un botón, se asume clic sobre una manzana del mapa
                    casilla = detectar_clic_manzana(pos_raton[0], pos_raton[1])
                    if casilla:
                        mx, my = casilla
                        estado_actual = manzanas_incidencias[(mx, my)]
                        
                        if estado_actual == "NORMAL": 
                            manzanas_incidencias[(mx, my)] = "TRAFICO"
                        elif estado_actual == "TRAFICO": 
                            manzanas_incidencias[(mx, my)] = "BLOQUEO"
                        elif estado_actual == "BLOQUEO": 
                            manzanas_incidencias[(mx, my)] = "RADAR"
                        else: 
                            manzanas_incidencias[(mx, my)] = "NORMAL"
                            
                        actualizar_pesos_mapa()
                        calcular_ambas_rutas()
            
            # --- CLIC DERECHO: PONER INICIO Y FIN ---
            elif evento.button == 3: 
                esquina = detectar_clic_esquina(pos_raton[0], pos_raton[1])
                if esquina:
                    if not nodo_inicio:
                        nodo_inicio = esquina
                    elif not nodo_fin:
                        nodo_fin = esquina
                        calcular_ambas_rutas()
                    else:
                        nodo_inicio = esquina
                        nodo_fin = None
                        camino_ruta1, camino_ruta2 = [], []
                        vehiculo1.reiniciar([])
                        vehiculo2.reiniciar([])
            
    dibujar_sistema()
    pygame.display.flip()

pygame.quit()
sys.exit()
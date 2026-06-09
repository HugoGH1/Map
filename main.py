import pygame
import sys
import math
import random

# Importar los módulos del proyecto
import config
from pathfinding import algoritmo_pathfinding
from vehicle import Vehiculo

# Inicializar Pygame y crear la ventana
pygame.init()
pantalla = pygame.display.set_mode((config.ANCHO, config.ALTO))
pygame.display.set_caption("Proyecto IA: A* vs Dijkstra + Simulación Completa")
fuente = pygame.font.SysFont("Arial", 13)
fuente_negrita = pygame.font.SysFont("Arial", 14, bold=True)

# --- CONFIGURACIÓN DE LOS BOTONES DE LA UI ---
rect_btn_algo = pygame.Rect(755, 405, 160, 24)
rect_btn_exploracion = pygame.Rect(755, 437, 160, 24)
rect_btn_vel = pygame.Rect(755, 469, 160, 24)
rect_btn_tema = pygame.Rect(755, 501, 160, 24)
rect_btn_anim = pygame.Rect(755, 533, 160, 24)
rect_btn_limpiar = pygame.Rect(755, 565, 160, 24)
rect_btn_random = pygame.Rect(755, 597, 160, 24)
rect_btn_reset = pygame.Rect(755, 629, 160, 24)

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

# Configuración de los Algoritmos de IA
algoritmo_activo = "A*"
nodos_a_estrella = 0
nodos_dijkstra = 0
arbol_exploracion = []
historial_pasos = []
ver_exploracion = True

# Estado y velocidad de la animación
animando_busqueda = False
progreso_animacion = 0.0
velocidad_animacion = 45.0  # Nodos/aristas por segundo

def inicializar_estructuras():
    global grafo, manzanas_incidencias, nodo_inicio, nodo_fin, camino_ruta1, camino_ruta2, tiempo_ruta1, tiempo_ruta2, algoritmo_activo, nodos_a_estrella, nodos_dijkstra, arbol_exploracion, historial_pasos, ver_exploracion, animando_busqueda, progreso_animacion, velocidad_animacion
    grafo = {}
    manzanas_incidencias = {}
    nodo_inicio = None
    nodo_fin = None
    camino_ruta1 = []
    camino_ruta2 = []
    tiempo_ruta1 = 0
    tiempo_ruta2 = 0
    algoritmo_activo = "A*"
    nodos_a_estrella = 0
    nodos_dijkstra = 0
    arbol_exploracion = []
    historial_pasos = []
    ver_exploracion = True
    animando_busqueda = False
    progreso_animacion = 0.0
    velocidad_animacion = 45.0
    config.modo_oscuro = True
    config.aplicar_tema()
    
    for x in range(config.NODOS_LINEA):
        for y in range(config.NODOS_LINEA):
            grafo[(x, y)] = []
            
    for mx in range(config.DIM_MANZANAS):
        for my in range(config.DIM_MANZANAS):
            manzanas_incidencias[(mx, my)] = "NORMAL"
            
    actualizar_pesos_mapa()
    
    if 'vehiculo1' in globals() and vehiculo1:
        vehiculo1.reiniciar([])
    if 'vehiculo2' in globals() and vehiculo2:
        vehiculo2.reiniciar([])

def actualizar_pesos_mapa():
    """Reconstruye el grafo con las penalizaciones dinámicas de las manzanas [cite: 10]"""
    for esquina in grafo:
        grafo[esquina] = []
        
    for x in range(config.NODOS_LINEA):
        for y in range(config.NODOS_LINEA):
            # --- Calles Horizontales (Filas) --- [cite: 4]
            if x < config.DIM_MANZANAS:
                peso = calcular_peso_tramo(x, y, x + 1, y)
                if y % 2 == 0:  # Fila par: Este (Derecha) [cite: 4]
                    grafo[(x, y)].append(((x + 1, y), peso))
                else:          # Fila impar: Oeste (Izquierda) [cite: 4]
                    grafo[(x + 1, y)].append(((x, y), peso))
            
            # --- Calles Verticales (Columnas) --- [cite: 4]
            if y < config.DIM_MANZANAS:
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
        if my_abajo < config.DIM_MANZANAS: manzanas_vecinas.append(manzanas_incidencias[(mx, my_abajo)])
    else: # Tramo vertical
        mx_izquierda = x1 - 1
        mx_derecha = x1
        my = min(y1, y2)
        if mx_izquierda >= 0: manzanas_vecinas.append(manzanas_incidencias[(mx_izquierda, my)])
        if mx_derecha < config.DIM_MANZANAS: manzanas_vecinas.append(manzanas_incidencias[(mx_derecha, my)])
        
    if "BLOQUEO" in manzanas_vecinas:
        return 999.0  # Calle cerrada (Costo inaccesible) [cite: 7]
    if "TRAFICO" in manzanas_vecinas:
        return 3.0    # Tráfico intenso = 3 minutos [cite: 8, 12]
    if "RADAR" in manzanas_vecinas:
        return 2.0    # Radar de policía frena el flujo = 2 minutos [cite: 9]
        
    return 1.0        # Tiempo normal = 1 minuto [cite: 12]

def calcular_ambas_rutas():
    """Calcula la mejor ruta y la alternativa basándose en la configuración activa"""
    global camino_ruta1, camino_ruta2, tiempo_ruta1, tiempo_ruta2, nodos_a_estrella, nodos_dijkstra, arbol_exploracion, historial_pasos, animando_busqueda, progreso_animacion
    if not nodo_inicio or not nodo_fin:
        camino_ruta1, camino_ruta2 = [], []
        tiempo_ruta1, tiempo_ruta2 = 0, 0
        nodos_a_estrella, nodos_dijkstra = 0, 0
        arbol_exploracion = []
        historial_pasos = []
        animando_busqueda = False
        progreso_animacion = 0.0
        vehiculo1.reiniciar([])
        vehiculo2.reiniciar([])
        return
        
    usar_h = (algoritmo_activo == "A*")
    
    # 1. Obtener la Primera Opción (La más óptima)
    camino_ruta1, tiempo_ruta1, nodos_eval_ruta1, arbol_ruta1, historial_ruta1 = algoritmo_pathfinding(nodo_inicio, nodo_fin, grafo, usar_heuristica=usar_h)
    arbol_exploracion = arbol_ruta1
    historial_pasos = historial_ruta1
    
    # Calcular comparativas del número de nodos evaluados para la misma ruta óptima
    if usar_h:
        nodos_a_estrella = nodos_eval_ruta1
        _, _, nodos_dijkstra, _, _ = algoritmo_pathfinding(nodo_inicio, nodo_fin, grafo, usar_heuristica=False)
    else:
        nodos_dijkstra = nodos_eval_ruta1
        _, _, nodos_a_estrella, _, _ = algoritmo_pathfinding(nodo_inicio, nodo_fin, grafo, usar_heuristica=True)
    
    # 2. Generar la Segunda Opción (Ruta Alternativa) 
    if camino_ruta1:
        tramos_utilizados = set()
        for i in range(len(camino_ruta1) - 1):
            tramos_utilizados.add((camino_ruta1[i], camino_ruta1[i+1]))
            
        camino_ruta2, tiempo_total_penalizado, _, _, _ = algoritmo_pathfinding(nodo_inicio, nodo_fin, grafo, usar_heuristica=usar_h, aristas_penalizadas=tramos_utilizados)
        
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

    # Iniciar la animación de la búsqueda paso a paso
    animando_busqueda = True
    progreso_animacion = 0.0
    vehiculo1.reiniciar([])
    vehiculo2.reiniciar([])

# --- AUXILIARES COORDENADAS ---
def detectar_clic_manzana(px, py):
    for mx in range(config.DIM_MANZANAS):
        for my in range(config.DIM_MANZANAS):
            x_ini = config.MARGEN + mx * config.TAM_CUADRA + 5
            y_ini = config.MARGEN + my * config.TAM_CUADRA + 5
            if x_ini <= px <= x_ini + config.TAM_CUADRA - 10 and y_ini <= py <= y_ini + config.TAM_CUADRA - 10:
                return mx, my
    return None

def detectar_clic_esquina(px, py):
    """Detecta a qué esquina (nodo) le dio clic el usuario"""
    for x in range(config.NODOS_LINEA):
        for y in range(config.NODOS_LINEA):
            cx, cy = config.obtener_coordenadas_pixel(x, y)
            if math.hypot(px - cx, py - cy) < 15:
                return x, y
    return None

# --- AUXILIAR DE INTERFAZ: DIBUJAR BOTÓN ---
def dibujar_boton(superficie, rect, texto, color_base, color_hover, pos_raton):
    hover = rect.collidepoint(pos_raton)
    color = color_hover if hover else color_base
    pygame.draw.rect(superficie, color, rect, border_radius=6)
    pygame.draw.rect(superficie, config.COLOR_TEXTO, rect, width=1, border_radius=6)
    
    # Texto centrado
    color_texto = (255, 255, 255)
    if color_base == config.COLOR_TRAFICO:
        color_texto = (44, 62, 80)
        
    lbl = fuente_negrita.render(texto, True, color_texto)
    lbl_rect = lbl.get_rect(center=rect.center)
    superficie.blit(lbl, lbl_rect)

# --- RENDERIZADO VISUAL ---
def dibujar_sistema():
    pantalla.fill(config.COLOR_BG)
    pos_raton = pygame.mouse.get_pos()
    
    # 1. Dibujar Manzanas (Cuerpo)
    for mx in range(config.DIM_MANZANAS):
        for my in range(config.DIM_MANZANAS):
            px = config.MARGEN + mx * config.TAM_CUADRA + 6
            py = config.MARGEN + my * config.TAM_CUADRA + 6
            tam = config.TAM_CUADRA - 12
            
            estado = manzanas_incidencias[(mx, my)]
            color = config.COLOR_MANZANA_NORMAL
            if estado == "TRAFICO": color = config.COLOR_TRAFICO
            elif estado == "BLOQUEO": color = config.COLOR_BLOQUEO
            elif estado == "RADAR": color = config.COLOR_RADAR
            
            pygame.draw.rect(pantalla, color, (px, py, tam, tam), border_radius=4)
            if estado != "NORMAL":
                texto_m = fuente.render(estado[0], True, (255, 255, 255) if estado != "TRAFICO" else (44, 62, 80))
                pantalla.blit(texto_m, (px + tam//2 - 4, py + tam//2 - 6))

    # 2. Dibujar Calles de un solo sentido
    for origen, destinos in grafo.items():
        x1, y1 = config.obtener_coordenadas_pixel(origen[0], origen[1])
        for destino, peso in destinos:
            x2, y2 = config.obtener_coordenadas_pixel(destino[0], destino[1])
            color_c = config.COLOR_CALLE
            grosor = 2
            if peso == 999.0: color_c = config.COLOR_BLOQUEO; grosor = 3
            elif peso == 3.0: color_c = config.COLOR_TRAFICO; grosor = 3
            elif peso == 2.0: color_c = config.COLOR_RADAR; grosor = 3
            
            pygame.draw.line(pantalla, color_c, (x1, y1), (x2, y2), grosor)
            
            # Flechas de tránsito
            mx_f, my_f = (x1 + x2) / 2, (y1 + y2) / 2
            color_fl = (148, 163, 184) if peso == 1.0 else (255, 255, 255)
            if x1 < x2: pygame.draw.polygon(pantalla, color_fl, [(mx_f+5, my_f), (mx_f-4, my_f-3), (mx_f-4, my_f+3)])
            elif x1 > x2: pygame.draw.polygon(pantalla, color_fl, [(mx_f-5, my_f), (mx_f+4, my_f-3), (mx_f+4, my_f+3)])
            elif y1 < y2: pygame.draw.polygon(pantalla, color_fl, [(mx_f, my_f+5), (mx_f-3, my_f-4), (mx_f+3, my_f-4)])
            elif y1 > y2: pygame.draw.polygon(pantalla, color_fl, [(mx_f, my_f-5), (mx_f-3, my_f+4), (mx_f+3, my_f+4)])

    # 2.5 Dibujar Árbol de Exploración (Nodos Abiertos en Celeste vs Cerrados en color del Algoritmo)
    if ver_exploracion and historial_pasos and len(historial_pasos) > 0:
        if animando_busqueda:
            idx = min(int(progreso_animacion), len(historial_pasos) - 1)
            estado = historial_pasos[idx]
            
            # 1. Dibujar aristas exploradas hasta este paso
            color_arbol_base = (142, 68, 173) if algoritmo_activo == "Dijkstra" else (230, 126, 34)
            for u, v in estado["arbol"]:
                x1, y1 = config.obtener_coordenadas_pixel(u[0], u[1])
                x2, y2 = config.obtener_coordenadas_pixel(v[0], v[1])
                pygame.draw.line(pantalla, color_arbol_base, (x1, y1), (x2, y2), 2)
                
            # 2. Dibujar nodos evaluados/cerrados (Closed Set)
            for n in estado["visitados"]:
                x, y = config.obtener_coordenadas_pixel(n[0], n[1])
                pygame.draw.circle(pantalla, color_arbol_base, (x, y), 4)
                
            # 3. Dibujar nodos en la frontera (Open Set) en Celeste Neón
            color_abierto = (0, 240, 255)
            for n in estado["frontera"]:
                x, y = config.obtener_coordenadas_pixel(n[0], n[1])
                pygame.draw.circle(pantalla, color_abierto, (x, y), 5)
                
            # 4. Dibujar el nodo actual en Blanco
            x_act, y_act = config.obtener_coordenadas_pixel(estado["actual"][0], estado["actual"][1])
            pygame.draw.circle(pantalla, (255, 255, 255), (x_act, y_act), 7)
            pygame.draw.circle(pantalla, color_arbol_base, (x_act, y_act), 7, width=2)
            
        else:
            # Una vez completado, el árbol completo se ve tenue para no interferir
            color_arbol = (71, 85, 105) if config.modo_oscuro else (210, 215, 220)
            for u, v in arbol_exploracion:
                x1, y1 = config.obtener_coordenadas_pixel(u[0], u[1])
                x2, y2 = config.obtener_coordenadas_pixel(v[0], v[1])
                pygame.draw.line(pantalla, color_arbol, (x1, y1), (x2, y2), 1)
                pygame.draw.circle(pantalla, color_arbol, (x2, y2), 2)

    # 3. PINTAR LAS DOS OPCIONES DE RECORRIDO (solo cuando la animación de búsqueda concluye)
    if not animando_busqueda:
        # Dibujar la Opción 2 primero (Azul) 
        if len(camino_ruta2) > 1:
            for i in range(len(camino_ruta2) - 1):
                xa, ya = config.obtener_coordenadas_pixel(camino_ruta2[i][0], camino_ruta2[i][1])
                xb, yb = config.obtener_coordenadas_pixel(camino_ruta2[i+1][0], camino_ruta2[i+1][1])
                pygame.draw.line(pantalla, config.COLOR_RUTA2, (xa+2, ya+2), (xb+2, yb+2), 5)

        # Dibujar la Opción 1 (Verde) 
        if len(camino_ruta1) > 1:
            for i in range(len(camino_ruta1) - 1):
                xa, ya = config.obtener_coordenadas_pixel(camino_ruta1[i][0], camino_ruta1[i][1])
                xb, yb = config.obtener_coordenadas_pixel(camino_ruta1[i+1][0], camino_ruta1[i+1][1])
                pygame.draw.line(pantalla, config.COLOR_RUTA1, (xa-2, ya-2), (xb-2, yb-2), 5)

        # Dibujar Vehículos Animados
        vehiculo1.dibujar(pantalla)
        vehiculo2.dibujar(pantalla)

    # 4. Dibujar Esquinas (Nodos)
    for x in range(config.NODOS_LINEA):
        for y in range(config.NODOS_LINEA):
            px, py = config.obtener_coordenadas_pixel(x, y)
            pygame.draw.circle(pantalla, (44, 62, 80) if not config.modo_oscuro else (71, 85, 105), (px, py), 4)

    # Marcar visualmente los marcadores de Inicio y Fin 
    if nodo_inicio:
        ix, iy = config.obtener_coordenadas_pixel(nodo_inicio[0], nodo_inicio[1])
        pygame.draw.circle(pantalla, config.COLOR_RUTA1, (ix, iy), 10)
        pygame.draw.circle(pantalla, (255, 255, 255), (ix, iy), 4)
    if nodo_fin:
        fx, fy = config.obtener_coordenadas_pixel(nodo_fin[0], nodo_fin[1])
        pygame.draw.circle(pantalla, config.COLOR_RUTA2, (fx, fy), 10)
        pygame.draw.circle(pantalla, (255, 255, 255), (fx, fy), 4)

    # 5. Texto Informativo del Panel Superior 
    cont_incidencias = sum(1 for v in manzanas_incidencias.values() if v != "NORMAL")
    
    t1 = fuente_negrita.render("CONTROLES DE LA SIMULACIÓN:", True, config.COLOR_TEXTO)
    t2 = fuente.render("• Clic Izquierdo en las manzanas del mapa para alternar Incidencias (Máx 3 en pantalla).", True, config.COLOR_TEXTO)
    t3 = fuente.render("• Clic Derecho en esquinas para colocar/mover: 1er Clic = INICIO, 2do Clic = FIN.", True, config.COLOR_TEXTO)
    t4 = fuente.render(f"• Incidencias en manzanas: {cont_incidencias} / 3", True, config.COLOR_TEXTO if cont_incidencias <= 3 else config.COLOR_BLOQUEO)
    
    pantalla.blit(t1, (20, 15))
    pantalla.blit(t2, (20, 35))
    pantalla.blit(t3, (20, 55))
    pantalla.blit(t4, (20, 75))

    # 6. DIBUJAR PANEL LATERAL (Estadísticas y Botones)
    pygame.draw.rect(pantalla, config.COLOR_PANEL, (740, 120, 190, 600), border_radius=10)
    pygame.draw.rect(pantalla, config.COLOR_BORDE_PANEL, (740, 120, 190, 600), width=2, border_radius=10)
    
    # Título Estadísticas
    lbl_titulo = fuente_negrita.render("ESTADÍSTICAS", True, config.COLOR_TEXTO)
    pantalla.blit(lbl_titulo, (755, 140))
    pygame.draw.line(pantalla, config.COLOR_BORDE_PANEL, (750, 165), (920, 165), 1)
    
    # Ruta 1 (Verde)
    lbl_r1_title = fuente_negrita.render("Ruta 1 (Verde)", True, config.COLOR_RUTA1)
    pantalla.blit(lbl_r1_title, (755, 175))
    if camino_ruta1:
        txt_t1 = fuente.render(f"Tiempo: {tiempo_ruta1:.1f} min", True, config.COLOR_TEXTO)
        txt_d1 = fuente.render(f"Dist: {len(camino_ruta1) - 1} cuadras", True, config.COLOR_TEXTO)
    else:
        txt_t1 = fuente.render("Sin ruta disponible", True, config.COLOR_TEXTO)
        txt_d1 = fuente.render("-", True, config.COLOR_TEXTO)
    pantalla.blit(txt_t1, (755, 195))
    pantalla.blit(txt_d1, (755, 212))
    
    # Ruta 2 (Azul)
    lbl_r2_title = fuente_negrita.render("Ruta 2 (Azul)", True, config.COLOR_RUTA2)
    pantalla.blit(lbl_r2_title, (755, 240))
    if camino_ruta2:
        txt_t2 = fuente.render(f"Tiempo: {tiempo_ruta2:.1f} min", True, config.COLOR_TEXTO)
        txt_d2 = fuente.render(f"Dist: {len(camino_ruta2) - 1} cuadras", True, config.COLOR_TEXTO)
    else:
        txt_t2 = fuente.render("Sin ruta alternativa", True, config.COLOR_TEXTO)
        txt_d2 = fuente.render("-", True, config.COLOR_TEXTO)
    pantalla.blit(txt_t2, (755, 260))
    pantalla.blit(txt_d2, (755, 277))
    
    # Comparativa de tiempos
    pygame.draw.line(pantalla, config.COLOR_BORDE_PANEL, (750, 305), (920, 305), 1)
    if camino_ruta1 and camino_ruta2:
        if tiempo_ruta1 > 0:
            diff = ((tiempo_ruta2 - tiempo_ruta1) / tiempo_ruta1) * 100
            if diff > 0:
                txt_comp = fuente.render(f"R2 es {diff:.1f}% +lenta", True, config.COLOR_TEXTO)
            else:
                txt_comp = fuente.render("Mismo tiempo", True, config.COLOR_TEXTO)
        else:
            txt_comp = fuente.render("-", True, config.COLOR_TEXTO)
    else:
        txt_comp = fuente.render("N/A", True, config.COLOR_TEXTO)
    pantalla.blit(txt_comp, (755, 312))
    
    # Comparativa de rendimiento (nodos evaluados)
    txt_nodos_a = fuente.render(f"Nodos A*: {nodos_a_estrella}", True, config.COLOR_TEXTO)
    txt_nodos_d = fuente.render(f"Nodos Dijkstra: {nodos_dijkstra}", True, config.COLOR_TEXTO)
    pantalla.blit(txt_nodos_a, (755, 332))
    pantalla.blit(txt_nodos_d, (755, 349))
    
    # Separador Acciones
    pygame.draw.line(pantalla, config.COLOR_BORDE_PANEL, (750, 375), (920, 375), 1)
    lbl_acciones = fuente_negrita.render("ACCIONES", True, config.COLOR_TEXTO)
    pantalla.blit(lbl_acciones, (755, 385))
    
    # Dibujar los Botones de la UI
    texto_algo = f"Modo: {algoritmo_activo}"
    texto_exp = f"Ver Expl: {'SÍ' if ver_exploracion else 'NO'}"
    
    if velocidad_animacion == 15.0:
        texto_vel = "Vel: Lento"
    elif velocidad_animacion == 45.0:
        texto_vel = "Vel: Normal"
    else:
        texto_vel = "Vel: Rápido"
        
    texto_tema = f"Tema: {'Oscuro' if config.modo_oscuro else 'Claro'}"
    
    dibujar_boton(pantalla, rect_btn_algo, texto_algo, config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_exploracion, texto_exp, config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_vel, texto_vel, config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_tema, texto_tema, config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_anim, "▶ Simular", config.COLOR_BOTON_ACCION, config.COLOR_BOTON_ACCION_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_limpiar, "Limpiar Mapa", config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_random, "Incidencias Rnd", config.COLOR_BOTON_NORMAL, config.COLOR_BOTON_HOVER, pos_raton)
    dibujar_boton(pantalla, rect_btn_reset, "Reiniciar Todo", config.COLOR_BOTON_PELIGRO, config.COLOR_BOTON_PELIGRO_HOVER, pos_raton)

    # 7. Barra Inferior de Acotaciones (Con soporte para temas)
    pygame.draw.rect(pantalla, config.COLOR_TRAFICO, (40, 790, 15, 15))
    pantalla.blit(fuente.render("Tráfico (3 min)", True, config.COLOR_TEXTO), (65, 790))
    
    pygame.draw.rect(pantalla, config.COLOR_BLOQUEO, (200, 790, 15, 15))
    pantalla.blit(fuente.render("Bloqueo (Cerrada)", True, config.COLOR_TEXTO), (225, 790))
    
    pygame.draw.rect(pantalla, config.COLOR_RADAR, (400, 790, 15, 15))
    pantalla.blit(fuente.render("Radar (2 min)", True, config.COLOR_TEXTO), (425, 790))
    
    # Leyenda académica de nodos de exploración (solo visible cuando está activo)
    if ver_exploracion:
        pygame.draw.circle(pantalla, (0, 240, 255), (570, 797), 5)
        pantalla.blit(fuente.render("Frontera (Abiertos)", True, config.COLOR_TEXTO), (585, 790))
        
        # Color del cerrado según el algoritmo activo
        color_c = (142, 68, 173) if algoritmo_activo == "Dijkstra" else (230, 126, 34)
        pygame.draw.circle(pantalla, color_c, (740, 797), 4)
        pantalla.blit(fuente.render("Evaluados (Cerrados)", True, config.COLOR_TEXTO), (755, 790))

# Crear instancias globales de vehículos
vehiculo1 = Vehiculo(config.COLOR_RUTA1, [])
vehiculo2 = Vehiculo(config.COLOR_RUTA2, [])

# Inicializar mapa y variables por primera vez
inicializar_estructuras()

# --- BUCLE PRINCIPAL DE INTERACCIÓN ---
ejecutando = True
clock = pygame.time.Clock()

while ejecutando:
    dt = clock.tick(60) / 1000.0
    
    # Actualizar la animación de exploración o los vehículos
    if animando_busqueda:
        # Avance dinámico basado en la velocidad seleccionada
        progreso_animacion += dt * velocidad_animacion
        if progreso_animacion >= len(historial_pasos):
            animando_busqueda = False
            progreso_animacion = len(historial_pasos)
            # Iniciar vehículos cuando la exploración concluye
            vehiculo1.reiniciar(camino_ruta1)
            vehiculo2.reiniciar(camino_ruta2)
    else:
        # Actualizar posiciones de los vehículos
        vehiculo1.actualizar(dt, grafo)
        vehiculo2.actualizar(dt, grafo)
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
            
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            pos_raton = pygame.mouse.get_pos()
            
            # --- CLIC IZQUIERDO: CONFIGURAR INCIDENCIAS O PULSAR BOTONES ---
            if evento.button == 1: 
                # Comprobar clics en botones de la barra lateral primero
                if rect_btn_algo.collidepoint(pos_raton):
                    if algoritmo_activo == "A*":
                        algoritmo_activo = "Dijkstra"
                    else:
                        algoritmo_activo = "A*"
                    calcular_ambas_rutas()
                elif rect_btn_exploracion.collidepoint(pos_raton):
                    ver_exploracion = not ver_exploracion
                elif rect_btn_vel.collidepoint(pos_raton):
                    if velocidad_animacion == 15.0:
                        velocidad_animacion = 45.0
                    elif velocidad_animacion == 45.0:
                        velocidad_animacion = 90.0
                    else:
                        velocidad_animacion = 15.0
                elif rect_btn_tema.collidepoint(pos_raton):
                    config.modo_oscuro = not config.modo_oscuro
                    config.aplicar_tema()
                elif rect_btn_anim.collidepoint(pos_raton):
                    # Reinicia la animación de exploración
                    if camino_ruta1:
                        animando_busqueda = True
                        progreso_animacion = 0.0
                        vehiculo1.reiniciar([])
                        vehiculo2.reiniciar([])
                elif rect_btn_limpiar.collidepoint(pos_raton):
                    for mx in range(config.DIM_MANZANAS):
                        for my in range(config.DIM_MANZANAS):
                            manzanas_incidencias[(mx, my)] = "NORMAL"
                    actualizar_pesos_mapa()
                    calcular_ambas_rutas()
                elif rect_btn_random.collidepoint(pos_raton):
                    # Limpiar incidencias previas
                    for mx in range(config.DIM_MANZANAS):
                        for my in range(config.DIM_MANZANAS):
                            manzanas_incidencias[(mx, my)] = "NORMAL"
                    
                    # Generar exactamente 3 incidencias aleatorias en el mapa
                    todas = [(mx, my) for mx in range(config.DIM_MANZANAS) for my in range(config.DIM_MANZANAS)]
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
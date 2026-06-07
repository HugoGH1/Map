import pygame
import sys
import heapq
import math

# --- CONFIGURACIÓN DE LA PANTALLA Y MAPA ---
ANCHO, ALTO = 950, 850
DIM_MANZANAS = 10  # 10x10 manzanas [cite: 3]
NODOS_LINEA = DIM_MANZANAS + 1  # 11x11 esquinas
TAM_CUADRA = 60  
MARGEN = 120  

# Colores (RGB)
COLOR_BG = (245, 245, 245)
COLOR_CALLE = (180, 180, 180)
COLOR_TEXTO = (44, 62, 80)
COLOR_MANZANA_NORMAL = (220, 220, 220)

# Colores de las Incidencias 
COLOR_TRAFICO = (241, 196, 15)   # Amarillo [cite: 8]
COLOR_BLOQUEO = (231, 76, 60)    # Rojo [cite: 7]
COLOR_RADAR = (155, 89, 182)     # Morado [cite: 9]

# Colores de las Rutas 
COLOR_RUTA1 = (46, 204, 113)     # Verde (Opción 1) 
COLOR_RUTA2 = (52, 152, 219)     # Azul (Opción 2) 

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Proyecto IA: 2 Alternativas de Ruta Inteligente")
fuente = pygame.font.SysFont("Arial", 13)
fuente_negrita = pygame.font.SysFont("Arial", 14, bold=True)

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

def inicializar_estructuras():
    global grafo, manzanas_incidencias, nodo_inicio, nodo_fin, camino_ruta1, camino_ruta2
    grafo = {}
    manzanas_incidencias = {}
    nodo_inicio = None
    nodo_fin = None
    camino_ruta1 = []
    camino_ruta2 = []
    
    for x in range(NODOS_LINEA):
        for y in range(NODOS_LINEA):
            grafo[(x, y)] = []
            
    for mx in range(DIM_MANZANAS):
        for my in range(DIM_MANZANAS):
            manzanas_incidencias[(mx, my)] = "NORMAL"
            
    actualizar_pesos_mapa()

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

# --- 🧠 ALGORITMO INTELEGENTE A* (A-ESTRELLA) ---
def heuristica(a, b):
    # Distancia Manhattan (ideal para calles cuadradas tipo New York / cuadrículas)
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
            
        for vecino, peso in grafo[actual]:
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
        camino_ruta2, tiempo_ruta2 = [], 0

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

# --- RENDERIZADO VISUAL ---
def dibujar_sistema():
    pantalla.fill(COLOR_BG)
    
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
            # Desplazamos un pixel la línea para que si se enciman, se noten ambas
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

    # Marcar visualmente los marcadores de Inicio y Fin 
    if nodo_inicio:
        ix, iy = obtener_coordenadas_pixel(nodo_inicio[0], nodo_inicio[1])
        pygame.draw.circle(pantalla, COLOR_RUTA1, (ix, iy), 10)
        pygame.draw.circle(pantballa:=pantalla, (255,255,255), (ix, iy), 4)
    if nodo_fin:
        fx, fy = obtener_coordenadas_pixel(nodo_fin[0], nodo_fin[1])
        pygame.draw.circle(pantalla, COLOR_RUTA2, (fx, fy), 10)
        pygame.draw.circle(pantalla, (255,255,255), (fx, fy), 4)

    # 5. Texto Informativo y Resultados del Panel Superior 
    cont_incidencias = sum(1 for v in manzanas_incidencias.values() if v != "NORMAL")
    
    t1 = fuente_negrita.render("CONTROLES:", True, COLOR_TEXTO)
    t2 = fuente.render("• Clic Izquierdo en manzanas para ciclar Incidencias (Máx 3 manzanas).", True, COLOR_TEXTO)
    t3 = fuente.render("• Clic Derecho en las esquinas para colocar/mover: 1er Clic = INICIO, 2do Clic = FIN.", True, COLOR_TEXTO)
    t4 = fuente.render(f"• Incidencias en manzanas: {cont_incidencias} / 3", True, COLOR_TEXTO if cont_incidencias <= 3 else COLOR_BLOQUEO)
    
    pantalla.blit(t1, (20, 15))
    pantalla.blit(t2, (20, 35))
    pantalla.blit(t3, (20, 55))
    pantalla.blit(t4, (20, 75))

    # Tiempos calculados para el Profe 
    lbl_r1 = fuente_negrita.render(f"OPCIÓN 1 (Verde): {f'{tiempo_ruta1:.1f} minutos' if camino_ruta1 else 'Sin ruta disponible'}", True, COLOR_RUTA1)
    lbl_r2 = fuente_negrita.render(f"OPCIÓN 2 (Azul): {f'{tiempo_ruta2:.1f} minutos' if camino_ruta2 else 'Sin ruta alternativa'}", True, COLOR_RUTA2)
    pantalla.blit(lbl_r1, (620, 25))
    pantalla.blit(lbl_r2, (620, 50))

    # Barra Inferior de Acotaciones (SECCIÓN CORREGIDA Y LIMPIA)
    pygame.draw.rect(pantalla, COLOR_TRAFICO, (40, 790, 15, 15))
    pantalla.blit(fuente.render("Tráfico (3 min)", True, COLOR_TEXTO), (65, 790))
    
    pygame.draw.rect(pantalla, COLOR_BLOQUEO, (200, 790, 15, 15))
    pantalla.blit(fuente.render("Bloqueo (Cerrada)", True, COLOR_TEXTO), (225, 790))
    
    pygame.draw.rect(pantalla, COLOR_RADAR, (400, 790, 15, 15))
    pantalla.blit(fuente.render("Radar (2 min)", True, COLOR_TEXTO), (425, 790))

inicializar_estructuras()

# --- BUCLE PRINCIPAL DE INTERACCIÓN ---
# --- BUCLE PRINCIPAL DE INTERACCIÓN (SECCIÓN CORREGIDA Y LIMPIA) ---
ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
            
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            pos_raton = pygame.mouse.get_pos()
            
            # --- CLIC IZQUIERDO: CONFIGURAR INCIDENCIAS EN MANZANAS ---
            if evento.button == 1: 
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
            
    dibujar_sistema()
    pygame.display.flip()

pygame.quit()
sys.exit()
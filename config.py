# --- CONFIGURACIÓN DE LA PANTALLA Y MAPA ---
ANCHO, ALTO = 950, 850
DIM_MANZANAS = 10  # 10x10 manzanas
NODOS_LINEA = DIM_MANZANAS + 1  # 11x11 esquinas
TAM_CUADRA = 60  
MARGEN = 120  

# Colores por defecto (Iniciados en Modo Oscuro Slate/Neon)
modo_oscuro = True
COLOR_BG = (15, 23, 42)
COLOR_CALLE = (30, 41, 59)
COLOR_TEXTO = (241, 245, 249)
COLOR_MANZANA_NORMAL = (22, 30, 49)
COLOR_PANEL = (30, 41, 59)
COLOR_BORDE_PANEL = (71, 85, 105)

# Colores de las Incidencias 
COLOR_TRAFICO = (241, 196, 15)   # Amarillo
COLOR_BLOQUEO = (231, 76, 60)    # Rojo
COLOR_RADAR = (155, 89, 182)     # Morado

# Colores de las Rutas 
COLOR_RUTA1 = (46, 204, 113)     # Verde (Opción 1) 
COLOR_RUTA2 = (52, 152, 219)     # Azul (Opción 2) 

# Colores de la Interfaz Sidebar
COLOR_BOTON_NORMAL = (52, 152, 219)
COLOR_BOTON_HOVER = (41, 128, 185)
COLOR_BOTON_ACCION = (46, 204, 113)
COLOR_BOTON_ACCION_HOVER = (39, 174, 96)
COLOR_BOTON_PELIGRO = (231, 76, 60)
COLOR_BOTON_PELIGRO_HOVER = (192, 57, 43)

def aplicar_tema():
    global COLOR_BG, COLOR_CALLE, COLOR_TEXTO, COLOR_MANZANA_NORMAL, COLOR_PANEL, COLOR_BORDE_PANEL, modo_oscuro
    if modo_oscuro:
        COLOR_BG = (15, 23, 42)           # Azul pizarra oscuro
        COLOR_CALLE = (30, 41, 59)        # Gris azulado oscuro
        COLOR_TEXTO = (241, 245, 249)     # Blanco pizarra
        COLOR_MANZANA_NORMAL = (22, 30, 49)
        COLOR_PANEL = (30, 41, 59)
        COLOR_BORDE_PANEL = (71, 85, 105)
    else:
        COLOR_BG = (245, 245, 245)        # Gris muy claro
        COLOR_CALLE = (180, 180, 180)     # Gris calle estándar
        COLOR_TEXTO = (44, 62, 80)        # Azul oscuro
        COLOR_MANZANA_NORMAL = (220, 220, 220)
        COLOR_PANEL = (235, 240, 245)
        COLOR_BORDE_PANEL = (200, 205, 210)

def obtener_coordenadas_pixel(x, y):
    return MARGEN + x * TAM_CUADRA, MARGEN + y * TAM_CUADRA

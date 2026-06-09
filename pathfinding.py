import heapq

def heuristica(a, b):
    # Distancia Manhattan (ideal para calles cuadradas tipo cuadrículas)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def algoritmo_pathfinding(inicio, fin, grafo, usar_heuristica=True, aristas_penalizadas=None):
    """Encuentra la ruta óptima considerando costos dinámicos, penalizaciones, heurística y devuelve árbol de exploración"""
    if aristas_penalizadas is None:
        aristas_penalizadas = set()
        
    queue = [(0, inicio)]
    costos = {inicio: 0}
    padres = {inicio: None}
    nodos_evaluados = 0
    visitados = set()
    arbol_busqueda = []
    historial_pasos = []
    
    while queue:
        costo_actual, actual = heapq.heappop(queue)
        
        if actual in visitados:
            continue
            
        # Nodos en la frontera (Open Set): alcanzados (en padres) pero aún no procesados/visitados
        frontera_actual = set()
        for v in padres:
            if padres[v] is not None and v not in visitados and v != actual:
                frontera_actual.add(v)
                
        # Guardamos el estado instantáneo antes de procesar los vecinos
        historial_pasos.append({
            "actual": actual,
            "visitados": set(visitados),
            "frontera": frontera_actual,
            "arbol": list(arbol_busqueda)
        })
        
        visitados.add(actual)
        nodos_evaluados += 1
        
        if padres[actual] is not None:
            arbol_busqueda.append((padres[actual], actual))
        
        if actual == fin:
            # Reconstruir camino de fin a inicio
            camino = []
            curr = fin
            while curr is not None:
                camino.append(curr)
                curr = padres[curr]
            return camino[::-1], costos[fin], nodos_evaluados, arbol_busqueda, historial_pasos
            
        for vecino, peso in grafo.get(actual, []):
            if peso >= 999.0:
                continue
                
            costo_tramo = peso
            if (actual, vecino) in aristas_penalizadas:
                costo_tramo += 15.0  # Penalización para forzar alternativa
                
            nuevo_costo = costos[actual] + costo_tramo
            
            if vecino not in costos or nuevo_costo < costos[vecino]:
                costos[vecino] = nuevo_costo
                h_val = heuristica(vecino, fin) if usar_heuristica else 0
                prioridad = nuevo_costo + h_val
                padres[vecino] = actual
                heapq.heappush(queue, (prioridad, vecino))
                
    return [], 0, nodos_evaluados, arbol_busqueda, historial_pasos

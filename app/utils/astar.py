# PoeBackEnd/app/utils/astar.py
from typing import Tuple, List, Set, Dict, Optional

def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    walkable: Set[Tuple[int, int]],
) -> Optional[List[Tuple[int, int]]]:
    from heapq import heappush, heappop

    print(f"[DEBUG] [astar] Inicio: {start}, Meta: {goal}")
    print(f"[DEBUG] [astar] Total coordenadas caminables: {len(walkable)}")
    
    # Verificar que inicio y meta están en walkable
    if start not in walkable:
        print(f"[ERROR] [astar] El punto de inicio {start} NO está en coordenadas caminables")
        return None
    
    if goal not in walkable:
        print(f"[ERROR] [astar] El punto meta {goal} NO está en coordenadas caminables")
        return None

    open_set = []
    heappush(open_set, (0 + manhattan(start, goal), 0, start, [start]))
    closed_set = set()
    
    iterations = 0
    max_iterations = 10000  # Prevenir bucles infinitos

    while open_set and iterations < max_iterations:
        iterations += 1
        _, cost, current, path = heappop(open_set)
        
        if current == goal:
            print(f"[DEBUG] [astar] ✓ Ruta encontrada en {iterations} iteraciones, longitud: {len(path)}")
            return path
            
        if current in closed_set:
            continue
            
        closed_set.add(current)
        
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            neighbor = (current[0]+dx, current[1]+dy)
            if neighbor in walkable and neighbor not in closed_set:
                heappush(open_set, (cost+1+manhattan(neighbor, goal), cost+1, neighbor, path+[neighbor]))
    
    print(f"[ERROR] [astar] No se encontró ruta después de {iterations} iteraciones")
    print(f"[DEBUG] [astar] Open set final: {len(open_set)} elementos")
    print(f"[DEBUG] [astar] Closed set final: {len(closed_set)} elementos")
    return None

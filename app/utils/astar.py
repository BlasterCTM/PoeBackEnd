from typing import Tuple, List, Set, Dict, Optional

def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    walkable: Set[Tuple[int, int]],
) -> Optional[List[Tuple[int, int]]]:
    from heapq import heappush, heappop

    open_set = []
    heappush(open_set, (0 + manhattan(start, goal), 0, start, [start]))
    closed_set = set()

    while open_set:
        _, cost, current, path = heappop(open_set)
        if current == goal:
            return path
        if current in closed_set:
            continue
        closed_set.add(current)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            neighbor = (current[0]+dx, current[1]+dy)
            if neighbor in walkable and neighbor not in closed_set:
                heappush(open_set, (cost+1+manhattan(neighbor, goal), cost+1, neighbor, path+[neighbor]))
    return None
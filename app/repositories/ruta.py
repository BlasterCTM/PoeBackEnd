# File: app/repositories/ruta.py
from sqlalchemy.orm import Session
from typing import Set, Tuple, List, Optional
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.utils.astar import astar

def generar_grafo(db: Session, mapa_id: int) -> Set[Tuple[int, int]]:
    ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa_id).all()
    walkable = set()
    for ubic in ubicaciones:
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == ubic.id_objeto).first()
        if not objeto:
            continue
        tipo = db.query(ObjetoTipo).filter(ObjetoTipo.id_tipo == objeto.id_tipo).first()
        if tipo and tipo.caminable:
            walkable.add((ubic.x, ubic.y))
    print(f"[DEBUG] [generar_grafo] Nodos caminables generados: {len(walkable)}")
    # Log de nodos específicos de interés
    for coord in [(4,2), (17,7), (17,8)]:
        print(f"[DEBUG] [generar_grafo] ¿Nodo {coord} está en caminables?: {coord in walkable}")
    return walkable

def calcular_ruta(
    db: Session,
    mapa_id: int,
    inicio: Tuple[int, int],
    fin: Tuple[int, int]
) -> Optional[List[Tuple[int, int]]]:
    walkable = generar_grafo(db, mapa_id)
    return astar(inicio, fin, walkable)

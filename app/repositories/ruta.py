# File: app/repositories/ruta.py
from sqlalchemy.orm import Session
from typing import Set, Tuple, List, Optional
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.utils.astar import astar

# En app/repositories/ruta.py

def generar_grafo(db: Session, mapa_id: int) -> Set[Tuple[int, int]]:
    """
    Genera el set de coordenadas caminables (grafo) soportando dos estrategias:
    1. Implícita: id_objeto es NULL (Suelo vacío).
    2. Explícita: id_objeto apunta a un ObjetoTipo marcado como 'caminable' (ej. Pasillo).
    """
    # Traemos todas las ubicaciones del mapa
    ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa_id).all()
    
    walkable = set()
    
    for ubic in ubicaciones:
        # null es suelo
        if ubic.id_objeto is None:
            walkable.add((ubic.x, ubic.y))
            continue # ¡Listo! Pasamos a la siguiente coordenada.

        #hay suelo
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == ubic.id_objeto).first()
        
        if not objeto:
            continue 
            
        tipo = db.query(ObjetoTipo).filter(ObjetoTipo.id_tipo == objeto.id_tipo).first()
        
        #Si es "Pasillo" (caminable=True), lo agrega.
        #Si es "Mueble" (caminable=False), lo ignora.
        if tipo and tipo.caminable:
            walkable.add((ubic.x, ubic.y))
            
    print(f"[DEBUG] [generar_grafo] Nodos caminables generados: {len(walkable)}")
    return walkable

def calcular_ruta(
    db: Session,
    mapa_id: int,
    inicio: Tuple[int, int],
    fin: Tuple[int, int]
) -> Optional[List[Tuple[int, int]]]:
    walkable = generar_grafo(db, mapa_id)
    return astar(inicio, fin, walkable)

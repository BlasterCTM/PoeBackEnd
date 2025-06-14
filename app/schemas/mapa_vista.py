from pydantic import BaseModel
from typing import List, Optional

class ObjetoTipoOut(BaseModel):
    nombre_tipo: str
    caminable: Optional[bool]
    destino: Optional[bool]

class PuntoReposicionVistaOut(BaseModel):
    id_punto: int
    nivel: int
    estanteria: int

class MuebleVistaOut(BaseModel):
    filas: int
    columnas: int
    puntos_reposicion: List[PuntoReposicionVistaOut]

class ObjetoMapaVistaOut(BaseModel):
    id: int
    nombre: str
    tipo: ObjetoTipoOut

class ObjetoUbicacionOut(BaseModel):
    x: int
    y: int
    objeto: ObjetoMapaVistaOut
    mueble: Optional[MuebleVistaOut]

class MapaVistaOut(BaseModel):
    id: int
    nombre: str
    ancho: int
    alto: int

class MapaVistaGraficaResponse(BaseModel):
    mapa: MapaVistaOut
    objetos: List[ObjetoUbicacionOut]
    mensaje: Optional[str] = None

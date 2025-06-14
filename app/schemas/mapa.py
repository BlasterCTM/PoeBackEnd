from pydantic import BaseModel
from typing import List, Optional

class ProductoAsociado(BaseModel):
    nombre: str
    categoria: str
    unidad_tipo: str
    unidad_cantidad: int

class PuntoReposicionOut(BaseModel):
    id_punto: int
    id_mueble: int
    nivel: int
    estanteria: int
    producto: Optional[ProductoAsociado]

class MuebleOut(BaseModel):
    filas: int
    columnas: int
    puntos_reposicion: List[PuntoReposicionOut]

class ObjetoOut(BaseModel):
    nombre: str
    tipo: str
    caminable: Optional[bool]

class UbicacionOut(BaseModel):
    x: int
    y: int
    objeto: ObjetoOut
    mueble: Optional[MuebleOut]

class MapaOut(BaseModel):
    id: int
    nombre: str
    ancho: int
    alto: int

class MapeoReposicionResponse(BaseModel):
    mapa: Optional[MapaOut] = None
    ubicaciones: List[UbicacionOut]
    mensaje: Optional[str] = None

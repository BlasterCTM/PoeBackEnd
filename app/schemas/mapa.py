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
    objeto: Optional[ObjetoOut]
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

# Listado general de objetos del mapa
class ObjetoTipoListadoOut(BaseModel):
    id: int
    nombre: str
    caminable: Optional[bool]

class ObjetoListadoOut(BaseModel):
    id_objeto: int
    nombre: str
    tipo: ObjetoTipoListadoOut

# Inputs para guardar layout completo
class UbicacionInput(BaseModel):
    x: int
    y: int
    ref_objeto_temp_id: Optional[str] = None
    id_objeto_real: Optional[int] = None

class ObjetoNuevoInput(BaseModel):
    temp_id: str
    nombre: str
    id_tipo: int
    filas: Optional[int] = None
    columnas: Optional[int] = None
    direccion: Optional[str] = None  # 'N','S','E','O','T'

class LayoutCompletoCreate(BaseModel):
    objetos_nuevos: List[ObjetoNuevoInput]
    ubicaciones: List[UbicacionInput]

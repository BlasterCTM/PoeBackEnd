from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date

class PuntoTareaCreate(BaseModel):
    id_punto: int
    cantidad: int

class TareaBase(BaseModel):
    """Esquema base para tareas"""
    id_reponedor: Optional[int] = Field(None, description="ID del reponedor asignado")
    estado_id: int = Field(..., description="ID del estado de la tarea")

class TareaCreate(TareaBase):
    """Esquema para crear una tarea"""
    puntos: List[PuntoTareaCreate]

    @model_validator(mode="after")
    def validar_puntos(cls, values):
        puntos = values.puntos
        if not puntos or len(puntos) == 0:
            raise ValueError('Debe incluir al menos un punto de reposición para la tarea.')
        ids = [p.id_punto for p in puntos]
        if len(ids) != len(set(ids)):
            raise ValueError('No se permiten puntos de reposición repetidos en la tarea.')
        for p in puntos:
            if p.cantidad <= 0:
                raise ValueError('Las cantidades deben ser mayores a 0.')
        return values

class DetalleProductoResponse(BaseModel):
    """Esquema para respuesta de detalle de producto en tarea"""
    id_producto: int
    nombre_producto: str
    cantidad: int
    id_punto: int

class TareaResponse(TareaBase):
    """Esquema para respuesta de tarea"""
    id_tarea: int
    fecha_creacion: date
    estado_id: int
    id_supervisor: int

    class Config:
        orm_mode = True

class TareaDetalleResponse(TareaResponse):
    """Esquema para respuesta de tarea con detalles"""
    detalles: List[DetalleProductoResponse] = []

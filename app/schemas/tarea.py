from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class TareaBase(BaseModel):
    """Esquema base para tareas"""
    id_punto: int = Field(..., description="ID del punto de reposición")
    id_reponedor: Optional[int] = Field(None, description="ID del reponedor asignado (opcional)")

class TareaCreate(TareaBase):
    """Esquema para crear una tarea"""
    id_supervisor: Optional[int] = Field(None, description="ID del supervisor (requerido para administradores, ignorado para supervisores)")

class DetalleProductoResponse(BaseModel):
    """Esquema para respuesta de detalle de producto en tarea"""
    id_producto: int
    nombre_producto: str
    cantidad: int

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
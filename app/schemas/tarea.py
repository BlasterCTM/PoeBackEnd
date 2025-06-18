from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date

class ProductoTareaCreate(BaseModel):
    id_producto: int
    cantidad: int

class TareaBase(BaseModel):
    """Esquema base para tareas"""
    id_punto: int = Field(..., description="ID del punto de reposición")
    id_reponedor: Optional[int] = Field(None, description="ID del reponedor asignado (opcional)")

class TareaCreate(TareaBase):
    """Esquema para crear una tarea"""
    id_supervisor: Optional[int] = Field(None, description="ID del supervisor (requerido para administradores, ignorado para supervisores)")
    productos: List[ProductoTareaCreate]

    @model_validator(mode="after")
    def validar_productos(cls, values):
        productos = values.productos
        if not productos or len(productos) == 0:
            raise ValueError('Debe incluir al menos un producto para la tarea.')
        ids = [p.id_producto for p in productos]
        if len(ids) != len(set(ids)):
            raise ValueError('No se permiten productos repetidos en la tarea.')
        for p in productos:
            if p.cantidad <= 0:
                raise ValueError('Las cantidades deben ser mayores a 0.')
        return values

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

from pydantic import BaseModel, Field
from typing import Optional

class PuntoReposicionCreate(BaseModel):
    id_mueble: int = Field(..., description="ID del mueble de reposición")
    nivel: int = Field(..., ge=0, description="Nivel del punto de reposición")
    estanteria: int = Field(..., ge=0, description="Estantería del punto de reposición")
    id_producto: Optional[int] = Field(None, description="ID del producto asociado (opcional)")
    id_usuario: Optional[int] = Field(None, description="ID del usuario responsable (opcional)")

class PuntoReposicionResponse(BaseModel):
    id_punto: int
    id_mueble: int
    nivel: int
    estanteria: int
    id_producto: Optional[int]
    id_usuario: Optional[int]

    class Config:
        from_attributes = True

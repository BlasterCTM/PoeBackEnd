from pydantic import BaseModel, Field, validator
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    categoria: str = Field(..., min_length=1, max_length=50)
    unidad_tipo: str = Field(..., min_length=1, max_length=20)
    unidad_cantidad: int = Field(..., gt=0)
    codigo_unico: Optional[str] = None
    estado: Optional[str] = Field("activo", pattern="^(activo|inactivo)$")

    @validator('nombre', 'categoria', 'unidad_tipo')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('El campo no puede estar vacío')
        return v

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id_producto: int
    class Config:
        from_attributes = True
        orm_mode = True

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    categoria: Optional[str] = Field(None, min_length=1, max_length=50)

    @validator('nombre')
    def nombre_no_vacio(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v

    @validator('categoria')
    def categoria_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError('La categoría no puede estar vacía')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "nombre": "Leche descremada 1L",
                "categoria": "Lácteos"
            }
        }

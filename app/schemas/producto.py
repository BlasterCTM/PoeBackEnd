from pydantic import BaseModel, Field, validator
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    categoria: str = Field(..., min_length=1, max_length=50)
    unidad_tipo: str = Field(..., min_length=1, max_length=20)
    unidad_cantidad: int = Field(..., gt=0)
    codigo_unico: str = Field(..., min_length=1, max_length=50)
    estado: Optional[str] = Field("activo", pattern="^(activo|inactivo)$")

    @validator('nombre', 'categoria', 'unidad_tipo', 'codigo_unico')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('El campo no puede estar vacío')
        return v

class ProductoCreate(ProductoBase):
    id_usuario: int

class ProductoOut(ProductoBase):
    id_producto: int
    class Config:
        from_attributes = True

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    categoria: Optional[str] = Field(None, min_length=1, max_length=50)
    codigo_unico: Optional[str] = Field(None, min_length=1, max_length=50)
    id_usuario: Optional[int] = Field(None, description="ID del supervisor asignado al producto")
    unidad_tipo: Optional[str] = Field(None, min_length=1, max_length=20)
    unidad_cantidad: Optional[int] = Field(None, gt=0)

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

    @validator('codigo_unico')
    def codigo_unico_no_vacio(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El código único no puede estar vacío')
        return v

    @validator('unidad_tipo')
    def unidad_tipo_no_vacio(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El tipo de unidad no puede estar vacío')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "nombre": "Leche descremada 1L",
                "categoria": "Lácteos",
                "codigo_unico": "LECH-004",
                "id_usuario": 1,
                "unidad_tipo": "litros",
                "unidad_cantidad": 1
            }
        }

class ProductoOutConSupervisor(ProductoBase):
    id_producto: int
    id_usuario: int
    nombre_supervisor: Optional[str] = Field(None, description="Nombre del supervisor que creó el producto")
    
    class Config:
        from_attributes = True

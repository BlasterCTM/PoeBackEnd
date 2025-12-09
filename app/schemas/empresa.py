from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class EmpresaBase(BaseModel):
    """Schema base para Empresa"""
    nombre_empresa: str = Field(..., min_length=3, max_length=100, description="Nombre de la empresa")
    rut_empresa: str = Field(..., min_length=9, max_length=20, description="RUT de la empresa (ej: 76.123.456-7)")
    direccion: str = Field(..., max_length=255, description="Dirección física de la empresa")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad donde opera")
    region: Optional[str] = Field(None, max_length=100, description="Región (ej: Región Metropolitana)")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email corporativo de la empresa")

class EmpresaCreate(EmpresaBase):
    """Schema para crear una empresa"""
    pass

class EmpresaUpdate(BaseModel):
    """Schema para actualizar una empresa"""
    nombre_empresa: Optional[str] = Field(None, min_length=3, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    estado: Optional[str] = Field(None, pattern="^(activo|inactivo)$")

class EmpresaResponse(BaseModel):
    """Schema para respuesta de empresa (flexible para datos legacy)"""
    id_empresa: int
    nombre_empresa: str
    rut_empresa: str  # Sin validación de longitud mínima para datos legacy
    direccion: Optional[str] = None  # Permitir NULL
    ciudad: Optional[str] = None
    region: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None  # Usar str en vez de EmailStr para permitir datos legacy
    estado: str
    fecha_registro: datetime

    class Config:
        from_attributes = True

class EmpresaRegistroRequest(BaseModel):
    """Schema para registro completo de empresa + admin"""
    # Datos de la empresa
    empresa: EmpresaCreate
    
    # Datos del usuario administrador
    admin_nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del administrador")
    admin_correo: EmailStr = Field(..., description="Email del administrador")
    admin_contraseña: str = Field(..., min_length=6, max_length=100, description="Contraseña del administrador")

class EmpresaRegistroResponse(BaseModel):
    """Schema para respuesta de registro exitoso"""
    mensaje: str
    empresa: dict
    administrador: dict

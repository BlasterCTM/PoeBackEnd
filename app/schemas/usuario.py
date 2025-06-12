from pydantic import BaseModel, EmailStr, constr, validator, Field
from typing import Optional, Dict, List
from app.models.usuario import RolEnum

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr

class UsuarioCreate(UsuarioBase):
    contraseña: constr(min_length=6)
    rol: RolEnum

    @validator('rol')
    def validar_rol(cls, v):
        if v not in [RolEnum.SUPERVISOR, RolEnum.REPONEDOR]:
            raise ValueError('El rol debe ser Supervisor o Reponedor')
        return v

class Usuario(UsuarioBase):
    id_usuario: int
    estado: Optional[str] = "activo"
    rol_id: int

    class Config:
        from_attributes = True

class UsuarioResponse(BaseModel):
    mensaje: str
    usuario: Optional[Usuario] = None

class LoginSchema(BaseModel):
    correo: EmailStr
    contraseña: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    correo: Optional[str] = None

class ReponedorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr
    contraseña: str = Field(..., min_length=6)
    estado: str = Field(default="activo", pattern="^(activo|inactivo)$")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class AuthError(BaseModel):
    detail: str
    error_type: str = Field(..., description="Tipo de error: 'not_found', 'invalid_password', 'inactive'")
    message: str

class UsuarioOutListado(BaseModel):
    id_usuario: int
    nombre: str
    correo: EmailStr
    rol: str
    estado: str

    class Config:
        from_attributes = True

class ListaUsuariosResponse(BaseModel):
    total: int
    usuarios: List[UsuarioOutListado]
    mensaje: Optional[str] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    correo: Optional[EmailStr] = None
    rol: Optional[RolEnum] = None

    @validator('rol')
    def validar_rol_update(cls, v):
        if v is not None:
            return v
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "correo": "juan.perez@ejemplo.com",
                "rol": "Supervisor"
            }
        }

class UsuarioEstadoUpdate(BaseModel):
    estado: str = Field(..., pattern="^(activo|inactivo)$", description="Estado del usuario: activo o inactivo")

    class Config:
        json_schema_extra = {
            "example": {
                "estado": "inactivo"
            }
        }

class ReponedorListado(BaseModel):
    id: int = Field(alias="id_usuario")
    nombre: str
    correo: EmailStr
    estado: str

    class Config:
        from_attributes = True
        populate_by_name = True

class ReponedoresResponse(BaseModel):
    total: int
    reponedores: List[ReponedorListado]
    mensaje: Optional[str] = None

class ReponedoresDisponiblesResponse(BaseModel):
    total: int
    reponedores: List[ReponedorListado]
    mensaje: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "reponedores": [
                    {
                        "id": 12,
                        "nombre": "Juan Pérez",
                        "correo": "juan@correo.com",
                        "estado": "activo"
                    }
                ],
                "mensaje": "Reponedores disponibles listados exitosamente"
            }
        }

class UsuarioPerfilOut(BaseModel):
    nombre: str
    correo: EmailStr
    rol: str
    estado: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "nombre": "blast",
                "correo": "blast@poe.cl",
                "rol": "Reponedor",
                "estado": "activo"
            }
        }

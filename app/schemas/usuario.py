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
    user_info: Dict[str, str]

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

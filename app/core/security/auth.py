from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.core.config.settings import settings
from app.repositories.usuario import UsuarioRepository
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_database
from app.models.usuario import RolEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/token")

# Configuración JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_database)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"Decodificando token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token decodificado: {payload}")
        email: str = payload.get("sub")
        if email is None:
            print("No se encontró el email en el token")
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    usuario_repo = UsuarioRepository()
    user = usuario_repo.get_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    print(f"Verificando permisos de administrador para usuario: {current_user.correo}")
    usuario_repo = UsuarioRepository()
    rol_admin = usuario_repo.get_rol_by_nombre(db, RolEnum.ADMINISTRADOR.value)
    print(f"Rol admin encontrado: {rol_admin.id_rol if rol_admin else 'No encontrado'}")
    print(f"Rol del usuario actual: {current_user.rol_id}")
    
    if current_user.rol_id != rol_admin.id_rol:
        print("El usuario no tiene permisos de administrador")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    print("Usuario verificado como administrador")
    return current_user

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Union
from app.api.dependencies.database import get_database
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, Token, LoginSchema
from app.repositories.usuario import UsuarioRepository
from app.core.security.auth import create_access_token, get_current_admin_user
from app.core.security.password import verify_password
from datetime import timedelta
from app.core.config.settings import settings

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"]
)

@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    description="Crear un nuevo usuario (requiere ser administrador)"
)
async def crear_usuario(
    usuario: UsuarioCreate,
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[dict, Depends(get_current_admin_user)]
):
    # Inicializar el repositorio
    usuario_repo = UsuarioRepository()
    
    # Verificar si el correo ya existe
    if usuario_repo.get_by_email(db, usuario.correo):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado"
        )
    
    # Obtener el ID del rol correspondiente
    rol = usuario_repo.get_rol_by_nombre(db, usuario.rol.value)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol {usuario.rol.value} no existe"
        )
    
    # Crear el usuario
    try:
        nuevo_usuario = usuario_repo.create_usuario(
            db=db,
            nombre=usuario.nombre,
            correo=usuario.correo,
            contraseña=usuario.contraseña,
            rol_id=rol.id_rol
        )
        return UsuarioResponse(
            mensaje="Usuario creado exitosamente",
            usuario=nuevo_usuario
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    login_data: LoginSchema,
    db: Session = Depends(get_database)
):
    try:
        # Buscar usuario por correo
        usuario_repo = UsuarioRepository()
        usuario = usuario_repo.get_by_email(db, login_data.correo)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not verify_password(login_data.contraseña, usuario.contraseña):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": usuario.correo}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error en login: {str(e)}")  # Para debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

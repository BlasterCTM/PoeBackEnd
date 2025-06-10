from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.api.dependencies.database import get_database
from app.schemas.usuario import ReponedorCreate, UsuarioResponse
from app.repositories.usuario import UsuarioRepository
from app.core.security.auth import get_current_user
from app.models.usuario import RolEnum, Usuario

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"]
)

@router.post(
    "/reponedores",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    description="Registrar un nuevo reponedor (requiere ser supervisor)"
)
async def registrar_reponedor(
    reponedor: ReponedorCreate,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden registrar reponedores"
        )
    
    # Verificar si el correo ya existe
    if usuario_repo.get_by_email(db, reponedor.correo):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado"
        )
    
    # Obtener el rol de reponedor
    rol_reponedor = usuario_repo.get_rol_by_nombre(db, RolEnum.REPONEDOR.value)
    if not rol_reponedor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el rol de reponedor"
        )
    
    try:
        # Crear el reponedor con rol predefinido
        nuevo_reponedor = usuario_repo.create_usuario(
            db=db,
            nombre=reponedor.nombre,
            correo=reponedor.correo,
            contraseña=reponedor.contraseña,
            rol_id=rol_reponedor.id_rol
        )
        
        return UsuarioResponse(
            mensaje="Reponedor registrado exitosamente",
            usuario=nuevo_reponedor
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el reponedor: {str(e)}"
        )

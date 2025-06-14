from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.api.dependencies.database import get_database
from app.schemas.usuario import (
    ReponedorCreate, UsuarioResponse, ReponedorListado, 
    ReponedoresResponse, ReponedoresDisponiblesResponse
)
from app.repositories.usuario import UsuarioRepository
from app.repositories.supervision import SupervisionRepository
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
        
        # Asignar automáticamente el reponedor al supervisor actual
        supervision_repo = SupervisionRepository()
        supervision_repo.asignar_reponedor(db, supervisor_id=current_user.id_usuario, reponedor_id=nuevo_reponedor.id_usuario)
        
        return UsuarioResponse(
            mensaje="Reponedor registrado y asignado exitosamente",
            usuario=nuevo_reponedor
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el reponedor: {str(e)}"
        )

@router.get(
    "/reponedores",
    response_model=ReponedoresResponse,
    status_code=status.HTTP_200_OK,
    description="Obtener la lista de reponedores asignados al supervisor"
)
async def listar_reponedores(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden ver sus reponedores asignados"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedores = supervision_repo.get_reponedores_by_supervisor(db, current_user.id_usuario)
        
        if not reponedores:
            return ReponedoresResponse(
                total=0,
                reponedores=[],
                mensaje="No tienes reponedores asignados"
            )
        
        # Transformar los reponedores a su formato de salida
        reponedores_response = [
            ReponedorListado(
                id=reponedor.id_usuario,
                nombre=reponedor.nombre,
                correo=reponedor.correo,
                estado=reponedor.estado
            ) for reponedor in reponedores
        ]
        
        return ReponedoresResponse(
            total=len(reponedores_response),
            reponedores=reponedores_response,
            mensaje="Reponedores listados exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar reponedores: {str(e)}"
        )

@router.get(
    "/reponedores/disponibles",
    response_model=ReponedoresDisponiblesResponse,
    status_code=status.HTTP_200_OK,
    description="Obtener la lista de reponedores disponibles para asignar"
)
async def listar_reponedores_disponibles(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden ver reponedores disponibles"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedores = supervision_repo.get_reponedores_disponibles(db)
        
        if not reponedores:
            return ReponedoresDisponiblesResponse(
                total=0,
                reponedores=[],
                mensaje="No hay reponedores disponibles para asignar"
            )
        
        # Transformar los reponedores a su formato de salida
        reponedores_response = [
            ReponedorListado(
                id=reponedor.id_usuario,
                nombre=reponedor.nombre,
                correo=reponedor.correo,
                estado=reponedor.estado
            ) for reponedor in reponedores
        ]
        
        return ReponedoresDisponiblesResponse(
            total=len(reponedores_response),
            reponedores=reponedores_response,
            mensaje="Reponedores disponibles listados exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar reponedores disponibles: {str(e)}"
        )

@router.post(
    "/reponedores/{reponedor_id}/asignar",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Asignar un reponedor al supervisor"
)
async def asignar_reponedor(
    reponedor_id: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden asignar reponedores"
        )
    
    try:
        # Verificar que el reponedor exista y esté disponible
        supervision_repo = SupervisionRepository()
        reponedor = usuario_repo.get_usuario_by_id(db, reponedor_id)
        
        if not reponedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reponedor no encontrado"
            )
            
        # Verificar que sea un reponedor
        rol_reponedor = usuario_repo.get_rol_by_nombre(db, RolEnum.REPONEDOR.value)
        if reponedor.rol_id != rol_reponedor.id_rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario seleccionado no es un reponedor"
            )
            
        # Verificar que no esté asignado a otro supervisor
        if supervision_repo.get_supervisor_of_reponedor(db, reponedor_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reponedor ya está asignado a otro supervisor"
            )
        
        # Asignar el reponedor
        supervision_repo.asignar_reponedor(
            db=db,
            supervisor_id=current_user.id_usuario,
            reponedor_id=reponedor_id
        )
        
        return UsuarioResponse(
            mensaje="Reponedor asignado exitosamente",
            usuario=reponedor
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar reponedor: {str(e)}"
        )

@router.delete(
    "/reponedores/{reponedor_id}/desasignar",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Desasignar un reponedor del supervisor"
)
async def desasignar_reponedor(
    reponedor_id: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden desasignar reponedores"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedor = usuario_repo.get_usuario_by_id(db, reponedor_id)
        
        if not reponedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reponedor no encontrado"
            )
        
        # Verificar que el reponedor esté asignado a este supervisor
        supervisor = supervision_repo.get_supervisor_of_reponedor(db, reponedor_id)
        if not supervisor or supervisor.id_usuario != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reponedor no está asignado a tu supervisión"
            )
        
        # Desasignar el reponedor
        supervision_repo.desasignar_reponedor(db, current_user.id_usuario, reponedor_id)
        
        return UsuarioResponse(
            mensaje="Reponedor desasignado exitosamente",
            usuario=reponedor
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desasignar reponedor: {str(e)}"
        )

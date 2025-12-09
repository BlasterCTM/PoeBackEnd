from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database.database import get_db
from app.schemas.actividad_cliente import (
    ActividadClienteCreate,
    ActividadClienteUpdate,
    ActividadClienteResponse,
    ActividadClienteListItem,
    ActividadStats,
    TipoActividad,
    EstadoActividad
)
from app.repositories.actividad_cliente import ActividadClienteRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.utils.tenant import require_super_admin, validate_tenant_access, is_super_admin

router = APIRouter()


# ============================================
# ENDPOINTS PRIVADOS
# ============================================

@router.get("/", response_model=List[ActividadClienteListItem])
def listar_actividades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    tipo: Optional[TipoActividad] = None,
    estado: Optional[EstadoActividad] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista todas las actividades de todos los clientes
    **ADMIN** - Lista actividades de su empresa
    """
    actividad_repo = ActividadClienteRepository()
    
    if is_super_admin(current_user):
        # SuperAdmin ve todas
        actividades = actividad_repo.get_all(
            db,
            skip=skip,
            limit=limit,
            tipo=tipo.value if tipo else None,
            estado=estado.value if estado else None
        )
    else:
        # Admin ve solo de su empresa
        actividades = actividad_repo.get_by_empresa(
            db,
            current_user.id_empresa,
            skip=skip,
            limit=limit,
            tipo=tipo.value if tipo else None,
            estado=estado.value if estado else None
        )
    
    return actividades


@router.get("/pendientes", response_model=List[ActividadClienteListItem])
def listar_actividades_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN o ADMIN** - Lista actividades pendientes
    """
    actividad_repo = ActividadClienteRepository()
    
    id_empresa = None if is_super_admin(current_user) else current_user.id_empresa
    
    return actividad_repo.get_pendientes(db, id_empresa)


@router.get("/proximas", response_model=List[ActividadClienteListItem])
def listar_actividades_proximas(
    dias: int = Query(7, ge=1, le=30, description="Días hacia adelante"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista actividades programadas para los próximos N días
    """
    require_super_admin(current_user)
    
    actividad_repo = ActividadClienteRepository()
    return actividad_repo.get_proximas(db, dias)


@router.get("/stats", response_model=ActividadStats)
def obtener_estadisticas_actividades(
    id_empresa: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Estadísticas de actividades
    
    Si se proporciona id_empresa, muestra stats de esa empresa.
    """
    require_super_admin(current_user)
    
    actividad_repo = ActividadClienteRepository()
    return actividad_repo.get_stats(db, id_empresa)


@router.get("/{id_actividad}", response_model=ActividadClienteResponse)
def obtener_actividad(
    id_actividad: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN o ADMIN** - Obtiene una actividad por ID
    """
    actividad_repo = ActividadClienteRepository()
    actividad = actividad_repo.get_by_id(db, id_actividad)
    
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad {id_actividad} no encontrada"
        )
    
    # Validar acceso
    if not is_super_admin(current_user):
        validate_tenant_access(current_user, actividad.id_empresa, "ver esta actividad")
    
    return actividad


@router.post("/", response_model=ActividadClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_actividad(
    actividad_data: ActividadClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Crea una actividad para un cliente
    
    Ejemplos:
    - Programar capacitación
    - Registrar incidencia
    - Agendar reunión
    - Documentar upgrade de plan
    """
    require_super_admin(current_user)
    
    actividad_repo = ActividadClienteRepository()
    
    actividad_dict = actividad_data.model_dump()
    nueva_actividad = actividad_repo.create(db, actividad_dict)
    
    # TODO: Enviar notificación a la empresa
    
    return nueva_actividad


@router.patch("/{id_actividad}", response_model=ActividadClienteResponse)
def actualizar_actividad(
    id_actividad: int,
    actividad_update: ActividadClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Actualiza una actividad
    """
    require_super_admin(current_user)
    
    actividad_repo = ActividadClienteRepository()
    
    actividad = actividad_repo.get_by_id(db, id_actividad)
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad {id_actividad} no encontrada"
        )
    
    update_data = actividad_update.model_dump(exclude_unset=True)
    actividad_actualizada = actividad_repo.update(db, id_actividad, update_data)
    
    return actividad_actualizada


@router.post("/{id_actividad}/completar", response_model=ActividadClienteResponse)
def marcar_actividad_completada(
    id_actividad: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Marca una actividad como completada
    """
    require_super_admin(current_user)
    
    actividad_repo = ActividadClienteRepository()
    actividad = actividad_repo.marcar_completada(db, id_actividad)
    
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad {id_actividad} no encontrada"
        )
    
    return actividad

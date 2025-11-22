from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database.database import get_db
from app.schemas.plan_empresa import (
    PlanEmpresaCreate,
    PlanEmpresaUpdate,
    PlanEmpresaResponse,
    PlanEmpresaConLimites,
    PlanEmpresaUpgrade,
    ValidacionLimite
)
from app.repositories.plan_empresa import PlanEmpresaRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.utils.tenant import require_super_admin, validate_tenant_access, is_super_admin

router = APIRouter()


# ============================================
# ENDPOINTS PRIVADOS
# ============================================

@router.get("/mi-plan", response_model=PlanEmpresaConLimites)
def obtener_mi_plan(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **USUARIO** - Obtiene el plan de la empresa del usuario autenticado
    
    Incluye información de uso de límites.
    """
    if is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SuperAdmin no tiene plan asociado"
        )
    
    plan_repo = PlanEmpresaRepository()
    plan = plan_repo.get_by_empresa(db, current_user.id_empresa)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Su empresa no tiene un plan activo"
        )
    
    # Obtener uso de recursos
    uso = plan_repo.get_uso_recursos(db, current_user.id_empresa)
    
    # Preparar respuesta
    plan_dict = plan.__dict__.copy()
    plan_dict.update(uso)
    
    # Calcular validaciones
    validaciones = {}
    for recurso in ["supervisores", "reponedores", "productos", "puntos"]:
        campo_uso = f"uso_{recurso}"
        if campo_uso in uso:
            validacion = plan_repo.validar_limite(
                db, 
                current_user.id_empresa, 
                recurso, 
                uso[campo_uso]
            )
            validaciones[recurso] = validacion
    
    plan_dict["validaciones"] = validaciones
    
    return plan_dict


@router.get("/", response_model=List[PlanEmpresaResponse])
def listar_planes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista todos los planes de todas las empresas
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    planes = plan_repo.get_all(db, skip=skip, limit=limit, activo=activo)
    
    return planes


@router.get("/validar-limite", response_model=ValidacionLimite)
def validar_limite_recurso(
    recurso: str = Query(..., description="Tipo de recurso"),
    cantidad: int = Query(..., description="Cantidad a validar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **USUARIO** - Valida si puede crear más recursos según su plan
    
    Ejemplo: Antes de crear un nuevo supervisor, validar si tiene espacio disponible.
    """
    if is_super_admin(current_user):
        return ValidacionLimite(
            recurso=recurso,
            cantidad_actual=cantidad,
            limite_plan=-1,
            disponible=-1,
            porcentaje_uso=0,
            excedido=False
        )
    
    plan_repo = PlanEmpresaRepository()
    validacion = plan_repo.validar_limite(db, current_user.id_empresa, recurso, cantidad)
    
    if not validacion.get("valido"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=validacion.get("mensaje", "Límite excedido")
        )
    
    return validacion


@router.get("/{id_plan}", response_model=PlanEmpresaResponse)
def obtener_plan(
    id_plan: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN o ADMIN** - Obtiene un plan por ID
    
    - SuperAdmin: puede ver cualquier plan
    - Admin: solo puede ver el plan de su empresa
    """
    plan_repo = PlanEmpresaRepository()
    plan = plan_repo.get_by_id(db, id_plan)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {id_plan} no encontrado"
        )
    
    # Validar acceso
    if not is_super_admin(current_user):
        validate_tenant_access(current_user, plan.id_empresa, "ver este plan")
    
    return plan


@router.post("/", response_model=PlanEmpresaResponse, status_code=status.HTTP_201_CREATED)
def crear_plan(
    plan_data: PlanEmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Crea un plan para una empresa
    
    Solo puede existir 1 plan por empresa (relación 1:1).
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    
    # Validar que la empresa no tenga ya un plan
    plan_existente = plan_repo.get_by_empresa(db, plan_data.id_empresa)
    if plan_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La empresa {plan_data.id_empresa} ya tiene un plan activo"
        )
    
    # Crear plan
    plan_dict = plan_data.model_dump()
    plan_dict["creado_por"] = current_user.id_usuario
    
    nuevo_plan = plan_repo.create(db, plan_dict)
    
    return nuevo_plan


@router.patch("/{id_plan}", response_model=PlanEmpresaResponse)
def actualizar_plan(
    id_plan: int,
    plan_update: PlanEmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Actualiza un plan
    
    Permite modificar límites, precio, features, etc.
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    
    # Verificar que existe
    plan = plan_repo.get_by_id(db, id_plan)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {id_plan} no encontrado"
        )
    
    # Actualizar
    update_data = plan_update.model_dump(exclude_unset=True)
    plan_actualizado = plan_repo.update(db, id_plan, update_data)
    
    return plan_actualizado


@router.post("/{id_plan}/activar")
def activar_plan(
    id_plan: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Activa un plan
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    plan = plan_repo.activar_desactivar(db, id_plan, True)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {id_plan} no encontrado"
        )
    
    return {"mensaje": "Plan activado", "id_plan": id_plan}


@router.post("/{id_plan}/desactivar")
def desactivar_plan(
    id_plan: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Desactiva un plan
    
    ⚠️ Esto bloqueará el acceso de la empresa al sistema.
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    plan = plan_repo.activar_desactivar(db, id_plan, False)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {id_plan} no encontrado"
        )
    
    return {"mensaje": "Plan desactivado", "id_plan": id_plan}


@router.post("/{id_plan}/upgrade", response_model=PlanEmpresaResponse)
def upgrade_plan(
    id_plan: int,
    upgrade_data: PlanEmpresaUpgrade,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Hace upgrade del plan de una empresa
    
    Aumenta límites y/o precio.
    """
    require_super_admin(current_user)
    
    plan_repo = PlanEmpresaRepository()
    
    # Verificar que existe
    plan = plan_repo.get_by_id(db, id_plan)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {id_plan} no encontrado"
        )
    
    # Preparar actualización
    update_data = {
        "precio_mensual": upgrade_data.nuevo_precio_mensual,
        "notas": f"{plan.notas or ''}\n\nUpgrade: {upgrade_data.motivo}"
    }
    
    if upgrade_data.nueva_cantidad_supervisores:
        update_data["cantidad_supervisores"] = upgrade_data.nueva_cantidad_supervisores
    
    if upgrade_data.nueva_cantidad_reponedores:
        update_data["cantidad_reponedores"] = upgrade_data.nueva_cantidad_reponedores
    
    # Actualizar
    plan_actualizado = plan_repo.update(db, id_plan, update_data)
    
    # TODO: Registrar actividad de upgrade
    # TODO: Notificar a la empresa del upgrade
    
    return plan_actualizado




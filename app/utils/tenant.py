"""
Utilidades para validación de Multi-Tenant y Sistema B2B
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.usuario import Usuario, RolEnum


# ============================================
# FUNCIONES DE AUTENTICACIÓN Y PERMISOS
# ============================================

def is_super_admin(user: Usuario) -> bool:
    """
    Verifica si el usuario es SuperAdmin
    
    Args:
        user: Usuario autenticado
        
    Returns:
        True si es SuperAdmin, False en caso contrario
    """
    return user.rol.nombre_rol == RolEnum.SUPERADMIN.value


def validate_tenant_access(
    current_user: Usuario, 
    resource_empresa_id: int,
    action: str = "acceder a este recurso"
) -> None:
    """
    Valida que el usuario tenga acceso al recurso de la empresa.
    
    - SuperAdmin: Acceso a todo
    - Otros roles: Solo acceso a su propia empresa
    
    Args:
        current_user: Usuario autenticado
        resource_empresa_id: ID de la empresa del recurso
        action: Descripción de la acción (para mensaje de error)
        
    Raises:
        HTTPException 403: Si el usuario no tiene permiso
    """
    # SuperAdmin tiene acceso a todo
    if is_super_admin(current_user):
        return
    
    # Otros usuarios solo pueden acceder a recursos de su empresa
    if current_user.id_empresa != resource_empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tiene permisos para {action}. Este recurso pertenece a otra empresa."
        )


def get_tenant_filter(current_user: Usuario) -> int | None:
    """
    Retorna el id_empresa para filtrar queries, o None si es SuperAdmin.
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        id_empresa si es usuario normal, None si es SuperAdmin (ve todo)
    """
    if is_super_admin(current_user):
        return None
    return current_user.id_empresa


def require_super_admin(current_user: Usuario) -> None:
    """
    Valida que el usuario sea SuperAdmin.
    
    Args:
        current_user: Usuario autenticado
        
    Raises:
        HTTPException 403: Si no es SuperAdmin
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de SuperAdmin"
        )


# ============================================
# FUNCIONES DE VALIDACIÓN DE PLAN B2B
# ============================================

def get_plan_empresa(db: Session, id_empresa: int):
    """
    Obtiene el plan activo de una empresa
    
    Args:
        db: Sesión de base de datos
        id_empresa: ID de la empresa
        
    Returns:
        PlanEmpresa o None
    """
    from app.models.plan_empresa import PlanEmpresa
    return db.query(PlanEmpresa).filter(
        PlanEmpresa.id_empresa == id_empresa,
        PlanEmpresa.activo == True
    ).first()


def validar_plan_activo(db: Session, current_user: Usuario) -> None:
    """
    Valida que la empresa del usuario tenga un plan activo
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Raises:
        HTTPException 403: Si no tiene plan activo
    """
    # SuperAdmin no necesita plan
    if is_super_admin(current_user):
        return
    
    plan = get_plan_empresa(db, current_user.id_empresa)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su empresa no tiene un plan activo. Contacte al administrador."
        )


def validar_limite_recurso(
    db: Session, 
    current_user: Usuario, 
    recurso: str, 
    cantidad_actual: int
) -> None:
    """
    Valida que no se exceda el límite de un recurso según el plan
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        recurso: Tipo de recurso ('locales', 'supervisores', 'reponedores', 'productos', 'puntos')
        cantidad_actual: Cantidad actual del recurso
        
    Raises:
        HTTPException 403: Si se excede el límite
    """
    # SuperAdmin no tiene límites
    if is_super_admin(current_user):
        return
    
    from app.repositories.plan_empresa import PlanEmpresaRepository
    
    plan_repo = PlanEmpresaRepository()
    validacion = plan_repo.validar_limite(db, current_user.id_empresa, recurso, cantidad_actual)
    
    if not validacion["valido"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=validacion["mensaje"]
        )


def tiene_feature(db: Session, current_user: Usuario, feature: str) -> bool:
    """
    Verifica si la empresa tiene un feature habilitado en su plan
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        feature: Nombre del feature
        
    Returns:
        bool
    """
    # SuperAdmin tiene todos los features
    if is_super_admin(current_user):
        return True
    
    from app.repositories.plan_empresa import PlanEmpresaRepository
    
    plan_repo = PlanEmpresaRepository()
    return plan_repo.tiene_feature(db, current_user.id_empresa, feature)


def validar_feature_disponible(
    db: Session, 
    current_user: Usuario, 
    feature: str,
    mensaje_personalizado: Optional[str] = None
) -> None:
    """
    Valida que la empresa tenga un feature habilitado, lanza excepción si no
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        feature: Nombre del feature
        mensaje_personalizado: Mensaje de error personalizado
        
    Raises:
        HTTPException 403: Si no tiene el feature
    """
    if not tiene_feature(db, current_user, feature):
        mensaje = mensaje_personalizado or f"Esta funcionalidad '{feature}' no está disponible en su plan. Contacte a su administrador para un upgrade."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensaje
        )


def obtener_info_plan(db: Session, current_user: Usuario) -> Dict[str, Any]:
    """
    Obtiene información completa del plan de la empresa
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        dict con información del plan
    """
    # SuperAdmin: retorna info especial
    if is_super_admin(current_user):
        return {
            "es_super_admin": True,
            "sin_limites": True,
            "todos_features": True
        }
    
    from app.repositories.plan_empresa import PlanEmpresaRepository
    
    plan_repo = PlanEmpresaRepository()
    plan = plan_repo.get_by_empresa(db, current_user.id_empresa)
    
    if not plan:
        return {
            "activo": False,
            "mensaje": "Sin plan activo"
        }
    
    # Obtener uso actual de recursos
    uso = plan_repo.get_uso_recursos(db, current_user.id_empresa)
    
    return {
        "activo": plan.activo,
        "cantidad_supervisores": plan.cantidad_supervisores,
        "cantidad_reponedores": plan.cantidad_reponedores,
        "precio_mensual": plan.precio_mensual,
        "features": plan.features,
        "uso_actual": uso,
        "fecha_vencimiento": plan.fecha_vencimiento
    }

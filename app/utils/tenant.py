"""
Utilidades para validación de Multi-Tenant
"""
from fastapi import HTTPException, status
from app.models.usuario import Usuario, RolEnum


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

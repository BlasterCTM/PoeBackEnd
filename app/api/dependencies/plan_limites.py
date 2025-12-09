"""
Dependency para validar límites de plan antes de crear recursos.
Bloquea la acción si el límite se excede y solicita upgrade.
"""
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.plan_empresa import PlanEmpresaRepository
from app.utils.tenant import is_super_admin


def validar_limite_plan(
    recurso: str,
    id_empresa: int,
    db: Session
) -> None:
    """
    Valida si la empresa puede crear más recursos según su plan.
    
    Args:
        recurso: Tipo de recurso ('supervisores', 'reponedores', 'productos', 'puntos')
        id_empresa: ID de la empresa
        db: Sesión de base de datos
    
    Raises:
        HTTPException 402: Si se excede el límite del plan (requiere upgrade)
    """
    plan_repo = PlanEmpresaRepository()
    
    # Obtener plan de la empresa
    plan = plan_repo.get_by_empresa(db, id_empresa)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su empresa no tiene un plan activo. Contacte al administrador."
        )
    
    if not plan.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El plan de su empresa está inactivo. Contacte al administrador."
        )
    
    # Obtener uso actual de recursos
    uso_recursos = plan_repo.get_uso_recursos(db, id_empresa)
    
    # Mapeo de recursos a campos de uso
    uso_map = {
        "supervisores": "uso_supervisores",
        "reponedores": "uso_reponedores",
        "productos": "uso_productos",
        "puntos": "uso_puntos"
    }
    
    limite_map = {
        "supervisores": "cantidad_supervisores",
        "reponedores": "cantidad_reponedores",
        "productos": "cantidad_productos",
        "puntos": "cantidad_puntos"
    }
    
    campo_uso = uso_map.get(recurso)
    campo_limite = limite_map.get(recurso)
    
    if not campo_uso or not campo_limite:
        # Recurso no limitado por plan
        print(f"[DEBUG validar_limite_plan] Recurso {recurso} no tiene mapeo - retornando")
        return
    
    cantidad_actual = uso_recursos.get(campo_uso, 0)
    limite_plan = getattr(plan, campo_limite, None)
    
    print(f"[DEBUG validar_limite_plan] Recurso: {recurso}, Cantidad Actual: {cantidad_actual}, Límite Plan: {limite_plan}")
    
    # Si el límite es None, significa que es ilimitado
    if limite_plan is None:
        print(f"[DEBUG validar_limite_plan] Límite es None (ilimitado) - retornando")
        return
    
    # Validar si se puede crear uno más (cantidad_actual + 1)
    print(f"[DEBUG validar_limite_plan] Validando {cantidad_actual + 1} items contra límite {limite_plan}")
    validacion = plan_repo.validar_limite(db, id_empresa, recurso, cantidad_actual + 1)
    
    print(f"[DEBUG validar_limite_plan] Resultado validación: {validacion}")
    
    if validacion.get("excedido"):
        print(f"[DEBUG validar_limite_plan] LÍMITE EXCEDIDO - lanzando excepción 402")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "plan_limit_exceeded",
                "mensaje": f"Ha alcanzado el límite de {recurso} permitido en su plan actual",
                "recurso": recurso,
                "limite_plan": limite_plan,
                "uso_actual": cantidad_actual,
                "accion_requerida": "upgrade_plan",
                "sugerencia": f"Su plan permite {limite_plan} {recurso}. Actualmente tiene {cantidad_actual}. Para crear más {recurso}, debe actualizar su plan. Contacte al superusuario o administrador de su empresa."
            }
        )
    else:
        print(f"[DEBUG validar_limite_plan] Validación pasó - permitiendo creación")


class ValidarLimitePlanDependency:
    """
    Dependency callable para validar límites de plan.
    
    Uso en endpoints:
        @router.post("/usuarios")
        def crear_usuario(
            ...,
            _: None = Depends(ValidarLimitePlanDependency("supervisores"))
        ):
    """
    def __init__(self, recurso: str):
        self.recurso = recurso
    
    def __call__(
        self,
        current_user: Usuario,
        db: Session = Depends(get_db)
    ) -> None:
        # SuperAdmin no tiene límites
        if is_super_admin(current_user):
            return
        
        validar_limite_plan(self.recurso, current_user.id_empresa, db)


# Shortcuts para dependency injection
validar_limite_supervisores = ValidarLimitePlanDependency("supervisores")
validar_limite_reponedores = ValidarLimitePlanDependency("reponedores")
validar_limite_productos = ValidarLimitePlanDependency("productos")
validar_limite_puntos = ValidarLimitePlanDependency("puntos")

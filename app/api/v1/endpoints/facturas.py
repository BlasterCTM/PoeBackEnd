from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database.database import get_db
from app.schemas.factura import (
    FacturaCreate,
    FacturaUpdate,
    FacturaResponse,
    FacturaListItem,
    FacturaRegistrarPago,
    FacturaGenerar,
    FacturaStats,
    EstadoFactura
)
from app.repositories.factura import FacturaRepository
from app.repositories.plan_empresa import PlanEmpresaRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.utils.tenant import require_super_admin, validate_tenant_access, is_super_admin

router = APIRouter()


# ============================================
# ENDPOINTS PRIVADOS
# ============================================

@router.get("/mis-facturas", response_model=List[FacturaListItem])
def listar_mis_facturas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    estado: Optional[EstadoFactura] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **ADMIN** - Lista las facturas de mi empresa
    """
    if is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SuperAdmin no tiene empresa asociada. Use /facturas/ para ver todas"
        )
    
    factura_repo = FacturaRepository()
    facturas = factura_repo.get_by_empresa(
        db,
        current_user.id_empresa,
        skip=skip,
        limit=limit,
        estado=estado.value if estado else None
    )
    
    return facturas


@router.get("/", response_model=List[FacturaListItem])
def listar_facturas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    estado: Optional[EstadoFactura] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista todas las facturas de todas las empresas
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    facturas = factura_repo.get_all(
        db,
        skip=skip,
        limit=limit,
        estado=estado.value if estado else None
    )
    
    return facturas


@router.get("/pendientes", response_model=List[FacturaListItem])
def listar_facturas_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista facturas pendientes de pago
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    return factura_repo.get_pendientes(db)


@router.get("/vencidas", response_model=List[FacturaListItem])
def listar_facturas_vencidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista facturas vencidas
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    return factura_repo.get_vencidas(db)


@router.get("/stats", response_model=FacturaStats)
def obtener_estadisticas_facturas(
    id_empresa: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Estadísticas de facturación
    
    Si se proporciona id_empresa, muestra stats de esa empresa.
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    return factura_repo.get_stats(db, id_empresa)


@router.get("/{id_factura}", response_model=FacturaResponse)
def obtener_factura(
    id_factura: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN o ADMIN** - Obtiene una factura por ID
    """
    factura_repo = FacturaRepository()
    factura = factura_repo.get_by_id(db, id_factura)
    
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {id_factura} no encontrada"
        )
    
    # Validar acceso
    if not is_super_admin(current_user):
        validate_tenant_access(current_user, factura.id_empresa, "ver esta factura")
    
    return factura


@router.post("/generar", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def generar_factura_automatica(
    factura_gen: FacturaGenerar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Genera una factura automática basada en el plan de la empresa
    
    Calcula automáticamente los montos (subtotal, IVA, total) según el plan activo.
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    plan_repo = PlanEmpresaRepository()
    
    # Obtener plan de la empresa
    plan = plan_repo.get_by_empresa(db, factura_gen.id_empresa)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La empresa {factura_gen.id_empresa} no tiene un plan activo"
        )
    
    # Calcular montos
    subtotal = plan.precio_mensual
    iva = int(subtotal * 0.19)  # IVA 19% en Chile
    total = subtotal + iva
    
    # Generar número de factura
    numero_factura = factura_repo.generar_numero_factura(db)
    
    # Crear factura
    factura_data = {
        "id_empresa": factura_gen.id_empresa,
        "id_plan": plan.id_plan,
        "numero_factura": numero_factura,
        "fecha_emision": datetime.utcnow().date(),
        "fecha_vencimiento": factura_gen.fecha_vencimiento,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "descripcion": factura_gen.descripcion or f"Servicio POE - {factura_gen.periodo_facturado}",
        "periodo_facturado": factura_gen.periodo_facturado,
        "estado": "pendiente",
        "emitida_por": current_user.id_usuario
    }
    
    nueva_factura = factura_repo.create(db, factura_data)
    
    # TODO: Generar PDF de la factura
    # TODO: Enviar factura por email a la empresa
    
    return nueva_factura


@router.post("/", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def crear_factura_manual(
    factura_data: FacturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Crea una factura manualmente
    
    Permite crear facturas con montos personalizados.
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    
    # Generar número si no viene
    factura_dict = factura_data.model_dump()
    if not factura_dict.get("numero_factura"):
        factura_dict["numero_factura"] = factura_repo.generar_numero_factura(db)
    
    factura_dict["emitida_por"] = current_user.id_usuario
    factura_dict["estado"] = "pendiente"
    
    nueva_factura = factura_repo.create(db, factura_dict)
    
    return nueva_factura


@router.patch("/{id_factura}", response_model=FacturaResponse)
def actualizar_factura(
    id_factura: int,
    factura_update: FacturaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Actualiza una factura
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    
    factura = factura_repo.get_by_id(db, id_factura)
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {id_factura} no encontrada"
        )
    
    update_data = factura_update.model_dump(exclude_unset=True)
    factura_actualizada = factura_repo.update(db, id_factura, update_data)
    
    return factura_actualizada


@router.post("/{id_factura}/registrar-pago", response_model=FacturaResponse)
def registrar_pago_factura(
    id_factura: int,
    pago_data: FacturaRegistrarPago,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Registra el pago de una factura
    
    Cambia el estado a "pagada" y registra los datos del pago.
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    
    factura = factura_repo.registrar_pago(
        db,
        id_factura,
        pago_data.fecha_pago,
        pago_data.metodo_pago,
        pago_data.referencia_pago
    )
    
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {id_factura} no encontrada"
        )
    
    # TODO: Enviar email de confirmación de pago
    
    return factura


@router.post("/{id_factura}/marcar-vencida")
def marcar_factura_vencida(
    id_factura: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Marca una factura como vencida manualmente
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    factura = factura_repo.marcar_vencida(db, id_factura)
    
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {id_factura} no encontrada"
        )
    
    return {"mensaje": "Factura marcada como vencida", "id_factura": id_factura}


@router.post("/{id_factura}/anular")
def anular_factura(
    id_factura: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Anula una factura
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    factura = factura_repo.anular(db, id_factura)
    
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {id_factura} no encontrada"
        )
    
    return {"mensaje": "Factura anulada", "id_factura": id_factura}


@router.post("/actualizar-vencidas")
def actualizar_facturas_vencidas_automatico(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Actualiza automáticamente las facturas pendientes que ya vencieron
    
    Útil para ejecutar periódicamente (cron job).
    """
    require_super_admin(current_user)
    
    factura_repo = FacturaRepository()
    cantidad_actualizadas = factura_repo.actualizar_vencidas_automatico(db)
    
    return {
        "mensaje": f"{cantidad_actualizadas} facturas marcadas como vencidas",
        "cantidad": cantidad_actualizadas
    }

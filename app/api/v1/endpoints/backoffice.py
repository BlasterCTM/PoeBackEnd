"""
Endpoints de Backoffice / SuperAdmin
Gestión del sistema SIN exponer datos sensibles de clientes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.models.empresa import Empresa
from app.models.plan_empresa import PlanEmpresa
from app.models.factura import Factura
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import EstadoCotizacion
from app.models.actividad_cliente import ActividadCliente
from app.schemas.actividad_cliente import EstadoActividad
from app.models.log_auditoria import LogAuditoria
from app.schemas.backoffice import (
    EmpresaBackoffice,
    UsuarioBackoffice,
    PlanEmpresaBackoffice,
    MetricasSistema,
    ResumenEmpresa,
    ConsumoRecursos
)
from app.schemas.log_auditoria import (
    LogAuditoriaResponse,
    LogAuditoriaFiltros,
    EstadisticasAuditoria
)
from app.repositories.log_auditoria import LogAuditoriaRepository
from app.services.auditoria import AuditoriaService
from app.utils.tenant import require_super_admin

router = APIRouter()


# ============================================================
# DASHBOARD Y MÉTRICAS AGREGADAS
# ============================================================

@router.get("/dashboard/metricas", response_model=MetricasSistema)
def obtener_metricas_sistema(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Métricas agregadas del sistema
    
    Retorna solo números agregados, sin datos sensibles:
    - Total de empresas por estado
    - Total de usuarios por rol
    - Estado de suscripciones
    - Facturación del mes
    - Actividades de soporte
    
    NO incluye:
    - Nombres de empleados
    - Datos de productos
    - Rutas/logística
    """
    require_super_admin(current_user)
    
    # Empresas
    total_empresas = db.query(func.count(Empresa.id_empresa)).scalar()
    empresas_activas = db.query(func.count(Empresa.id_empresa)).filter(
        Empresa.estado == "activo"
    ).scalar()
    empresas_inactivas = db.query(func.count(Empresa.id_empresa)).filter(
        Empresa.estado == "inactivo"
    ).scalar()
    empresas_suspendidas = db.query(func.count(Empresa.id_empresa)).filter(
        Empresa.estado == "suspendido"
    ).scalar()
    empresas_en_prueba = db.query(func.count(Empresa.id_empresa)).filter(
        Empresa.estado == "prueba"
    ).scalar()
    
    # Usuarios
    total_usuarios = db.query(func.count(Usuario.id_usuario)).scalar()
    usuarios_activos = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.estado == "activo"
    ).scalar()
    
    # Usuarios por rol
    from app.models.usuario import Rol
    usuarios_por_rol = {}
    roles = db.query(Rol).all()
    for rol in roles:
        count = db.query(func.count(Usuario.id_usuario)).filter(
            Usuario.rol_id == rol.id_rol
        ).scalar()
        usuarios_por_rol[rol.nombre_rol] = count
    
    # Suscripciones
    planes_activos = db.query(func.count(PlanEmpresa.id_plan)).filter(
        PlanEmpresa.activo == True
    ).scalar()
    
    hoy = date.today()
    planes_vencidos = db.query(func.count(PlanEmpresa.id_plan)).filter(
        PlanEmpresa.fecha_vencimiento < hoy,
        PlanEmpresa.activo == True
    ).scalar()
    
    en_30_dias = hoy + timedelta(days=30)
    planes_por_vencer = db.query(func.count(PlanEmpresa.id_plan)).filter(
        PlanEmpresa.fecha_vencimiento <= en_30_dias,
        PlanEmpresa.fecha_vencimiento >= hoy,
        PlanEmpresa.activo == True
    ).scalar()
    
    # Facturación
    facturas_pendientes = db.query(func.count(Factura.id_factura)).filter(
        Factura.estado == "pendiente"
    ).scalar()
    
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    facturas_pagadas_mes = db.query(func.count(Factura.id_factura)).filter(
        Factura.estado == "pagada",
        Factura.fecha_pago >= inicio_mes
    ).scalar()
    
    ingresos_mes = db.query(func.sum(Factura.total)).filter(
        Factura.estado == "pagada",
        Factura.fecha_pago >= inicio_mes
    ).scalar() or 0
    
    # Mes anterior
    mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    fin_mes_anterior = inicio_mes - timedelta(days=1)
    ingresos_mes_anterior = db.query(func.sum(Factura.total)).filter(
        Factura.estado == "pagada",
        Factura.fecha_pago >= mes_anterior,
        Factura.fecha_pago <= fin_mes_anterior
    ).scalar() or 0
    
    # Cotizaciones
    cotizaciones_pendientes = db.query(func.count(Cotizacion.id_cotizacion)).filter(
        Cotizacion.estado == EstadoCotizacion.PENDIENTE
    ).scalar()
    cotizaciones_aprobadas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
        Cotizacion.estado == EstadoCotizacion.APROBADA
    ).scalar()
    cotizaciones_rechazadas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
        Cotizacion.estado == EstadoCotizacion.RECHAZADA
    ).scalar()
    
    # Actividades
    actividades_pendientes = db.query(func.count(ActividadCliente.id_actividad)).filter(
        or_(
            ActividadCliente.estado == EstadoActividad.PENDIENTE,
            ActividadCliente.estado == EstadoActividad.EN_PROGRESO
        )
    ).scalar()
    actividades_completadas = db.query(func.count(ActividadCliente.id_actividad)).filter(
        ActividadCliente.estado == EstadoActividad.COMPLETADA,
        ActividadCliente.fecha_completada >= inicio_mes
    ).scalar()
    
    return MetricasSistema(
        total_empresas=total_empresas,
        empresas_activas=empresas_activas,
        empresas_inactivas=empresas_inactivas,
        empresas_suspendidas=empresas_suspendidas,
        empresas_en_prueba=empresas_en_prueba,
        total_usuarios=total_usuarios,
        usuarios_activos=usuarios_activos,
        usuarios_por_rol=usuarios_por_rol,
        planes_activos=planes_activos,
        planes_vencidos=planes_vencidos,
        planes_por_vencer_30d=planes_por_vencer,
        facturas_pendientes=facturas_pendientes,
        facturas_pagadas_mes=facturas_pagadas_mes,
        ingresos_mes_actual=ingresos_mes,
        ingresos_mes_anterior=ingresos_mes_anterior,
        cotizaciones_pendientes=cotizaciones_pendientes,
        cotizaciones_aprobadas=cotizaciones_aprobadas,
        cotizaciones_rechazadas=cotizaciones_rechazadas,
        actividades_pendientes=actividades_pendientes,
        actividades_completadas_mes=actividades_completadas
    )


@router.get("/empresas", response_model=List[EmpresaBackoffice])
def listar_empresas_backoffice(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista empresas con info segura
    
    Retorna:
    - Nombre, RUT, ubicación
    - Estado de suscripción
    - Email de contacto comercial
    
    NO retorna:
    - Datos de empleados
    - Productos/stock
    - Rutas/logística
    """
    require_super_admin(current_user)
    
    query = db.query(Empresa).outerjoin(PlanEmpresa)
    
    if estado:
        query = query.filter(Empresa.estado == estado)
    
    empresas = query.offset(skip).limit(limit).all()
    
    resultado = []
    for empresa in empresas:
        # Obtener plan activo si existe
        plan = db.query(PlanEmpresa).filter(
            PlanEmpresa.id_empresa == empresa.id_empresa,
            PlanEmpresa.activo == True
        ).first()
        
        resultado.append(EmpresaBackoffice(
            id_empresa=empresa.id_empresa,
            nombre_empresa=empresa.nombre_empresa,
            rut_empresa=empresa.rut_empresa,
            direccion=empresa.direccion,
            ciudad=empresa.ciudad,
            region=empresa.region,
            estado=empresa.estado,
            email=empresa.email,
            telefono=empresa.telefono,
            fecha_registro=empresa.fecha_registro,
            tiene_plan_activo=plan is not None,
            nombre_plan=f"Plan {empresa.nombre_empresa}" if plan else None,
            estado_plan="activo" if plan and plan.activo else "inactivo",
            fecha_vencimiento_plan=plan.fecha_vencimiento if plan else None
        ))
    
    return resultado


@router.get("/empresas/{id_empresa}/resumen", response_model=ResumenEmpresa)
def obtener_resumen_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Resumen de una empresa específica
    
    Datos seguros agregados sin información sensible
    """
    require_super_admin(current_user)
    
    empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Plan activo
    plan = db.query(PlanEmpresa).filter(
        PlanEmpresa.id_empresa == id_empresa,
        PlanEmpresa.activo == True
    ).first()
    
    # Usuarios
    total_usuarios = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.id_empresa == id_empresa
    ).scalar()
    usuarios_activos = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.id_empresa == id_empresa,
        Usuario.estado == "activo"
    ).scalar()
    
    # Facturación
    ultima_factura = db.query(Factura).filter(
        Factura.id_empresa == id_empresa,
        Factura.estado == "pagada"
    ).order_by(Factura.fecha_pago.desc()).first()
    
    facturas_pendientes = db.query(func.count(Factura.id_factura)).filter(
        Factura.id_empresa == id_empresa,
        Factura.estado == "pendiente"
    ).scalar()
    
    # Actividades
    actividades_pendientes = db.query(func.count(ActividadCliente.id_actividad)).filter(
        ActividadCliente.id_empresa == id_empresa,
        or_(
            ActividadCliente.estado == EstadoActividad.PENDIENTE,
            ActividadCliente.estado == EstadoActividad.EN_PROGRESO
        )
    ).scalar()
    
    ultima_actividad = db.query(ActividadCliente).filter(
        ActividadCliente.id_empresa == id_empresa
    ).order_by(ActividadCliente.fecha_creacion.desc()).first()
    
    return ResumenEmpresa(
        id_empresa=empresa.id_empresa,
        nombre_empresa=empresa.nombre_empresa,
        rut_empresa=empresa.rut_empresa,
        estado=empresa.estado,
        tiene_plan=plan is not None,
        plan_activo=plan.activo if plan else False,
        precio_mensual=plan.precio_mensual if plan else None,
        fecha_vencimiento=plan.fecha_vencimiento if plan else None,
        total_usuarios=total_usuarios,
        usuarios_activos=usuarios_activos,
        ultima_factura_pagada=ultima_factura.fecha_pago if ultima_factura else None,
        facturas_pendientes=facturas_pendientes,
        actividades_pendientes=actividades_pendientes,
        ultima_actividad=ultima_actividad.fecha_creacion if ultima_actividad else None
    )


@router.get("/empresas/{id_empresa}/consumo", response_model=ConsumoRecursos)
def obtener_consumo_recursos(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Consumo de recursos vs límites del plan
    
    Solo números agregados, sin datos sensibles
    """
    require_super_admin(current_user)
    
    empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    plan = db.query(PlanEmpresa).filter(
        PlanEmpresa.id_empresa == id_empresa,
        PlanEmpresa.activo == True
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Empresa no tiene plan activo")
    
    # Contar supervisores
    from app.models.usuario import Rol
    rol_supervisor = db.query(Rol).filter(Rol.nombre_rol == RolEnum.SUPERVISOR.value).first()
    supervisores_uso = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.id_empresa == id_empresa,
        Usuario.rol_id == rol_supervisor.id_rol if rol_supervisor else None,
        Usuario.estado == "activo"
    ).scalar()
    
    # Contar reponedores
    rol_reponedor = db.query(Rol).filter(Rol.nombre_rol == RolEnum.REPONEDOR.value).first()
    reponedores_uso = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.id_empresa == id_empresa,
        Usuario.rol_id == rol_reponedor.id_rol if rol_reponedor else None,
        Usuario.estado == "activo"
    ).scalar()
    
    total_usuarios = db.query(func.count(Usuario.id_usuario)).filter(
        Usuario.id_empresa == id_empresa
    ).scalar()
    
    return ConsumoRecursos(
        id_empresa=empresa.id_empresa,
        nombre_empresa=empresa.nombre_empresa,
        supervisores_limite=plan.cantidad_supervisores,
        supervisores_uso=supervisores_uso,
        supervisores_disponibles=plan.cantidad_supervisores - supervisores_uso,
        reponedores_limite=plan.cantidad_reponedores,
        reponedores_uso=reponedores_uso,
        reponedores_disponibles=plan.cantidad_reponedores - reponedores_uso,
        total_usuarios=total_usuarios
    )


# ============================================================
# LOGS DE AUDITORÍA
# ============================================================

@router.get("/auditoria/logs", response_model=List[LogAuditoriaResponse])
def obtener_logs_auditoria(
    filtros: LogAuditoriaFiltros = Depends(),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista logs de auditoría con filtros
    
    Permite auditar todas las acciones administrativas:
    - Quién realizó la acción
    - Qué se modificó
    - Cuándo se realizó
    - Datos antes/después del cambio
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    logs, total = repo.obtener_logs(db, filtros)
    
    return logs


@router.get("/auditoria/estadisticas", response_model=EstadisticasAuditoria)
def obtener_estadisticas_auditoria(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Estadísticas de auditoría
    
    Resumen de actividad administrativa del sistema
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    stats = repo.obtener_estadisticas(db)
    
    return EstadisticasAuditoria(**stats)


@router.get("/auditoria/entidad/{entidad}/{id_entidad}", response_model=List[LogAuditoriaResponse])
def obtener_historial_entidad(
    entidad: str,
    id_entidad: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Historial completo de cambios de una entidad
    
    Ejemplo: Ver todos los cambios realizados al plan_empresa con id=5
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    logs = repo.obtener_logs_por_entidad(db, entidad, id_entidad, limit)
    
    return logs


# ============================================================
# GESTIÓN DE ESTADO DE EMPRESAS
# ============================================================

@router.post("/empresas/{id_empresa}/suspender")
def suspender_empresa(
    id_empresa: int,
    motivo: str = Query(..., min_length=10, description="Motivo de la suspensión"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Suspende una empresa
    
    Cambia el estado a 'suspendido' y registra en auditoría
    """
    require_super_admin(current_user)
    
    empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Guardar estado anterior
    estado_anterior = empresa.estado
    
    # Suspender
    empresa.estado = "suspendido"
    db.commit()
    
    # Auditar
    auditoria_service = AuditoriaService(db)
    auditoria_service.registrar(
        usuario=current_user,
        accion="suspender_empresa",
        entidad="empresa",
        id_entidad=id_empresa,
        nombre_entidad=empresa.nombre_empresa,
        datos_anteriores={"estado": estado_anterior, "motivo": None},
        datos_nuevos={"estado": "suspendido", "motivo": motivo}
    )
    
    return {"message": f"Empresa {empresa.nombre_empresa} suspendida correctamente"}


@router.post("/empresas/{id_empresa}/reactivar")
def reactivar_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Reactiva una empresa suspendida
    """
    require_super_admin(current_user)
    
    empresa = db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    estado_anterior = empresa.estado
    empresa.estado = "activo"
    db.commit()
    
    # Auditar
    auditoria_service = AuditoriaService(db)
    auditoria_service.registrar(
        usuario=current_user,
        accion="reactivar_empresa",
        entidad="empresa",
        id_entidad=id_empresa,
        nombre_entidad=empresa.nombre_empresa,
        datos_anteriores={"estado": estado_anterior},
        datos_nuevos={"estado": "activo"}
    )
    
    return {"message": f"Empresa {empresa.nombre_empresa} reactivada correctamente"}

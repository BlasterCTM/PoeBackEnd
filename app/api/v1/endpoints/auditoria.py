"""
Endpoints de Auditoría - Solo SuperAdmin
Permite consultar TODOS los logs de TODOS los usuarios del sistema
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.core.database.database import get_db
from app.schemas.log_auditoria import (
    LogAuditoriaResponse,
    LogAuditoriaFiltros,
    EstadisticasAuditoria
)
from app.repositories.log_auditoria import LogAuditoriaRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.utils.tenant import require_super_admin

router = APIRouter()


@router.get("/", response_model=List[LogAuditoriaResponse])
async def listar_logs_auditoria(
    # Filtros de búsqueda
    id_usuario: Optional[int] = Query(None, description="Filtrar por usuario específico"),
    accion: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    entidad: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    id_entidad: Optional[int] = Query(None, description="Filtrar por ID de entidad específica"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    
    # Paginación
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=500, description="Límite de registros"),
    
    # Dependencias
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    📊 **Listar logs de auditoría** (Solo SuperAdmin)
    
    **Muestra TODOS los logs de TODOS los usuarios del sistema:**
    - ✅ Acciones de SuperAdmin
    - ✅ Acciones de Administradores
    - ✅ Acciones de Supervisores
    - ✅ Acciones de Reponedores
    
    **Filtros disponibles:**
    - Por usuario específico
    - Por tipo de acción (crear_tarea, actualizar_producto, etc.)
    - Por entidad (tarea, producto, usuario, etc.)
    - Por rango de fechas
    
    **Casos de uso:**
    - Ver qué hizo un usuario específico hoy
    - Auditar cambios en un producto específico
    - Ver todas las tareas creadas esta semana
    - Investigar quién modificó un plan
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    # Crear filtros
    filtros = LogAuditoriaFiltros(
        id_usuario=id_usuario,
        accion=accion,
        entidad=entidad,
        id_entidad=id_entidad,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Obtener logs
    logs = repo.listar_con_filtros(db, filtros, skip=skip, limit=limit)
    
    return logs


@router.get("/estadisticas", response_model=EstadisticasAuditoria)
async def obtener_estadisticas_auditoria(
    dias: int = Query(7, ge=1, le=90, description="Últimos N días"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    📈 **Estadísticas de auditoría** (Solo SuperAdmin)
    
    **Dashboard de actividad del sistema:**
    - Total de acciones por tipo
    - Usuarios más activos
    - Entidades más modificadas
    - Actividad por día
    - Distribución por tipo de usuario (Admin, Supervisor, Reponedor)
    
    **Útil para:**
    - Monitorear actividad del sistema
    - Detectar patrones de uso
    - Identificar usuarios inactivos o muy activos
    - Planificar recursos
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    fecha_desde = datetime.utcnow() - timedelta(days=dias)
    
    stats = repo.obtener_estadisticas(db, fecha_desde)
    
    return stats


@router.get("/usuario/{id_usuario}", response_model=List[LogAuditoriaResponse])
async def listar_logs_por_usuario(
    id_usuario: int,
    dias: int = Query(30, ge=1, le=365, description="Últimos N días"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    👤 **Historial de actividad de un usuario** (Solo SuperAdmin)
    
    **Muestra TODO lo que ha hecho un usuario:**
    - Todas sus acciones registradas
    - Ordenado por fecha (más reciente primero)
    - Con detalles completos (datos anteriores y nuevos)
    
    **Casos de uso:**
    - Auditar trabajo de un empleado
    - Verificar qué cambió un usuario
    - Investigar errores o problemas
    - Generar reporte de productividad
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    fecha_desde = datetime.utcnow() - timedelta(days=dias)
    
    filtros = LogAuditoriaFiltros(
        id_usuario=id_usuario,
        fecha_desde=fecha_desde.date()
    )
    
    logs = repo.listar_con_filtros(db, filtros, skip=0, limit=limit)
    
    return logs


@router.get("/entidad/{entidad}/{id_entidad}", response_model=List[LogAuditoriaResponse])
async def listar_logs_por_entidad(
    entidad: str,
    id_entidad: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    📝 **Historial de cambios de una entidad** (Solo SuperAdmin)
    
    **Muestra TODO el historial de una entidad específica:**
    - Quién la creó
    - Todas las modificaciones
    - Quién hizo cada cambio
    - Datos antes y después de cada cambio
    
    **Ejemplos:**
    - `/auditoria/entidad/tarea/123` - Historial de tarea #123
    - `/auditoria/entidad/producto/456` - Historial de producto #456
    - `/auditoria/entidad/usuario/789` - Historial de usuario #789
    
    **Casos de uso:**
    - Auditar cambios en un producto
    - Ver evolución de una tarea
    - Investigar quién modificó un plan
    - Rastrear cambios en configuración
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    filtros = LogAuditoriaFiltros(
        entidad=entidad,
        id_entidad=id_entidad
    )
    
    logs = repo.listar_con_filtros(db, filtros, skip=0, limit=1000)
    
    return logs


@router.get("/acciones", response_model=List[str])
async def listar_acciones_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    📋 **Lista de todas las acciones registradas** (Solo SuperAdmin)
    
    Devuelve lista única de todas las acciones que se han registrado:
    - crear_tarea
    - actualizar_producto
    - eliminar_usuario
    - etc.
    
    Útil para autocompletar filtros en UI
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    acciones = repo.listar_acciones_unicas(db)
    
    return acciones


@router.get("/entidades", response_model=List[str])
async def listar_entidades_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    📦 **Lista de todas las entidades registradas** (Solo SuperAdmin)
    
    Devuelve lista única de todos los tipos de entidad:
    - tarea
    - producto
    - usuario
    - plan_empresa
    - etc.
    
    Útil para autocompletar filtros en UI
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    entidades = repo.listar_entidades_unicas(db)
    
    return entidades


@router.get("/actividad-reciente", response_model=List[LogAuditoriaResponse])
async def obtener_actividad_reciente(
    minutos: int = Query(60, ge=1, le=1440, description="Últimos N minutos"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    ⚡ **Actividad en tiempo real** (Solo SuperAdmin)
    
    **Muestra las últimas acciones de TODOS los usuarios:**
    - Ordenado por timestamp (más reciente primero)
    - Actualizable en tiempo real
    - Para dashboard de monitoreo
    
    **Casos de uso:**
    - Dashboard de actividad en vivo
    - Monitorear qué están haciendo los usuarios ahora
    - Detectar actividad sospechosa
    - Feed de actividad para SuperAdmin
    """
    require_super_admin(current_user)
    
    repo = LogAuditoriaRepository()
    
    fecha_desde = datetime.utcnow() - timedelta(minutes=minutos)
    
    filtros = LogAuditoriaFiltros(
        fecha_desde=fecha_desde.date()
    )
    
    logs = repo.listar_con_filtros(db, filtros, skip=0, limit=limit)
    
    # Filtrar solo los de los últimos N minutos (más preciso que solo fecha)
    logs_recientes = [
        log for log in logs 
        if log.fecha >= fecha_desde
    ]
    
    return logs_recientes[:limit]

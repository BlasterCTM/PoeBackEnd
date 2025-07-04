"""
Endpoints para el sistema de reportes de tareas completadas.
Permite consultar historial de tareas y generar reportes en PDF/Excel.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import io

from app.api.dependencies.database import get_database
from app.core.security.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.services.reportes import ReportesService


router = APIRouter(prefix="/reportes", tags=["reportes"])


def validar_acceso_admin(current_user: Usuario = Depends(get_current_user)):
    """
    Valida que el usuario actual sea administrador.
    Solo los administradores pueden acceder a los reportes.
    """
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden acceder a los reportes."
        )
    return current_user


@router.get("/reponedores")
async def listar_reponedores(
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(validar_acceso_admin)
):
    """
    Lista todos los reponedores disponibles en el sistema.
    
    **Acceso:** Solo administradores
    
    **Respuesta:**
    - Lista de reponedores con información básica
    """
    # Obtener todos los reponedores
    reponedores = db.query(Usuario).filter(
        Usuario.rol.has(nombre_rol=RolEnum.REPONEDOR.value)
    ).all()
    
    result = []
    for reponedor in reponedores:
        result.append({
            "id_usuario": reponedor.id_usuario,
            "nombre": reponedor.nombre,
            "email": reponedor.correo,
            "estado": reponedor.estado
        })
    
    return {
        "total": len(result),
        "reponedores": result
    }


@router.get("/reponedor/{id_reponedor}")
async def obtener_historial_reponedor(
    id_reponedor: int,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(validar_acceso_admin),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio del filtro (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin del filtro (YYYY-MM-DD)"),
    estado: Optional[str] = Query(None, description="Estado de tarea para filtrar (completada, cancelada, etc.)"),
    limit: int = Query(100, description="Límite de resultados", le=1000),
    offset: int = Query(0, description="Offset para paginación", ge=0)
):
    """
    Obtiene el historial de tareas de un reponedor específico.
    
    **Acceso:** Solo administradores
    
    **Parámetros:**
    - `id_reponedor`: ID del reponedor
    - `fecha_inicio`: Fecha de inicio del filtro (opcional)
    - `fecha_fin`: Fecha de fin del filtro (opcional)
    - `estado`: Estado de tarea para filtrar (opcional)
    - `limit`: Límite de resultados (máximo 1000)
    - `offset`: Offset para paginación
    
    **Respuesta:**
    - Historial de tareas con detalles completos
    - Estadísticas agregadas
    - Información de paginación
    """
    try:
        servicio = ReportesService(db)
        
        # Validar fechas
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio no puede ser mayor que la fecha de fin."
            )
        
        resultado = servicio.obtener_historial_tareas_reponedor(
            id_reponedor=id_reponedor,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_filtro=estado,
            limit=limit,
            offset=offset
        )
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/reponedor/{id_reponedor}/descargar")
async def descargar_reporte_reponedor(
    id_reponedor: int,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(validar_acceso_admin),
    formato: str = Query("excel", description="Formato del reporte: 'excel' o 'pdf'"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio del filtro (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin del filtro (YYYY-MM-DD)"),
    estado: Optional[str] = Query(None, description="Estado de tarea para filtrar (completada, cancelada, etc.)")
):
    """
    Descarga un reporte del historial de tareas de un reponedor.
    
    **Acceso:** Solo administradores
    
    **Parámetros:**
    - `id_reponedor`: ID del reponedor
    - `formato`: Formato del reporte ('excel' o 'pdf')
    - `fecha_inicio`: Fecha de inicio del filtro (opcional)
    - `fecha_fin`: Fecha de fin del filtro (opcional)
    - `estado`: Estado de tarea para filtrar (opcional)
    
    **Respuesta:**
    - Archivo Excel (.xlsx) o PDF según el formato solicitado
    """
    try:
        servicio = ReportesService(db)
        
        # Validar formato
        if formato not in ["excel", "pdf"]:
            raise HTTPException(
                status_code=400,
                detail="El formato debe ser 'excel' o 'pdf'."
            )
        
        # Validar fechas
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio no puede ser mayor que la fecha de fin."
            )
        
        # Generar reporte según el formato
        if formato == "excel":
            archivo, nombre_archivo = servicio.generar_reporte_excel(
                id_reponedor=id_reponedor,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado_filtro=estado
            )
            
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
        else:  # formato == "pdf"
            archivo, nombre_archivo = servicio.generar_reporte_pdf(
                id_reponedor=id_reponedor,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado_filtro=estado
            )
            
            media_type = "application/pdf"
        
        # Preparar respuesta con el archivo
        archivo.seek(0)
        content = archivo.read()
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={nombre_archivo}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/supervisor/{id_supervisor}/reponedores")
async def obtener_reponedores_supervisor(
    id_supervisor: int,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(validar_acceso_admin)
):
    """
    Obtiene la lista de reponedores bajo la supervisión de un supervisor específico.
    
    **Acceso:** Solo administradores
    
    **Parámetros:**
    - `id_supervisor`: ID del supervisor
    
    **Respuesta:**
    - Lista de reponedores supervisados
    """
    try:
        servicio = ReportesService(db)
        
        # Validar que el supervisor existe
        supervisor = db.query(Usuario).filter(
            Usuario.id_usuario == id_supervisor,
            Usuario.rol.has(nombre_rol=RolEnum.SUPERVISOR.value)
        ).first()
        
        if not supervisor:
            raise HTTPException(
                status_code=404,
                detail="Supervisor no encontrado o no tiene el rol correcto."
            )
        
        reponedores = servicio.obtener_reponedores_supervisor(id_supervisor)
        
        return {
            "supervisor": {
                "id": supervisor.id_usuario,
                "nombre": supervisor.nombre,
                "email": supervisor.correo
            },
            "total_reponedores": len(reponedores),
            "reponedores": reponedores
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/estadisticas/general")
async def obtener_estadisticas_generales(
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(validar_acceso_admin),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio del filtro (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin del filtro (YYYY-MM-DD)")
):
    """
    Obtiene estadísticas generales del sistema de tareas.
    
    **Acceso:** Solo administradores
    
    **Parámetros:**
    - `fecha_inicio`: Fecha de inicio del filtro (opcional)
    - `fecha_fin`: Fecha de fin del filtro (opcional)
    
    **Respuesta:**
    - Estadísticas agregadas de todas las tareas del sistema
    """
    try:
        from app.models.tarea import Tarea
        from app.models.estado_tarea import EstadoTarea
        from sqlalchemy import func, and_
        
        # Validar fechas
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio no puede ser mayor que la fecha de fin."
            )
        
        # Query base
        query = db.query(Tarea)
        
        # Aplicar filtros de fecha
        if fecha_inicio:
            query = query.filter(Tarea.fecha_creacion >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Tarea.fecha_creacion <= fecha_fin)
        
        # Estadísticas básicas
        total_tareas = query.count()
        
        # Estadísticas por estado
        estadisticas_estado = db.query(
            EstadoTarea.nombre_estado,
            func.count(Tarea.id_tarea).label('count')
        ).join(Tarea).group_by(EstadoTarea.nombre_estado)
        
        if fecha_inicio:
            estadisticas_estado = estadisticas_estado.filter(Tarea.fecha_creacion >= fecha_inicio)
        if fecha_fin:
            estadisticas_estado = estadisticas_estado.filter(Tarea.fecha_creacion <= fecha_fin)
        
        estados_resultado = estadisticas_estado.all()
        
        # Estadísticas por reponedor
        estadisticas_reponedor = db.query(
            Usuario.nombre,
            func.count(Tarea.id_tarea).label('count')
        ).join(Tarea, Usuario.id_usuario == Tarea.id_reponedor).group_by(Usuario.nombre)
        
        if fecha_inicio:
            estadisticas_reponedor = estadisticas_reponedor.filter(Tarea.fecha_creacion >= fecha_inicio)
        if fecha_fin:
            estadisticas_reponedor = estadisticas_reponedor.filter(Tarea.fecha_creacion <= fecha_fin)
        
        reponedores_resultado = estadisticas_reponedor.all()
        
        return {
            "periodo": {
                "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
                "fecha_fin": fecha_fin.isoformat() if fecha_fin else None
            },
            "total_tareas": total_tareas,
            "estadisticas_por_estado": {
                estado.nombre_estado: estado.count for estado in estados_resultado
            },
            "estadisticas_por_reponedor": {
                reponedor.nombre: reponedor.count for reponedor in reponedores_resultado
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

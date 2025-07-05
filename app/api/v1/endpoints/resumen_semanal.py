from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.api.dependencies.database import get_database
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.services.resumen_semanal import ResumenSemanalService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/resumen-semanal")
async def obtener_resumen_semanal(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio de la semana (formato YYYY-MM-DD). Si no se especifica, usa la semana actual"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el resumen semanal de tareas para el reponedor autenticado.
    
    Este endpoint permite a los reponedores ver sus tareas organizadas por día de la semana
    en formato calendario, ideal para una vista de calendario en el frontend.
    
    - **fecha_inicio**: Fecha de inicio de la semana (lunes). Si no se especifica, usa la semana actual
    - Solo accesible para usuarios con rol de Reponedor
    - Retorna estructura de calendario con tareas agrupadas por día
    """
    try:
        # Verificar que el usuario sea reponedor
        if current_user.rol.nombre_rol != RolEnum.REPONEDOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los reponedores pueden acceder a este endpoint."
            )
        
        # Parsear fecha de inicio si se proporciona
        fecha_inicio_date = None
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        # Generar resumen semanal
        service = ResumenSemanalService(db)
        resumen = service.obtener_resumen_semanal(
            reponedor_id=current_user.id_usuario,
            fecha_inicio=fecha_inicio_date
        )
        
        logger.info(f"Resumen semanal generado para reponedor {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Resumen semanal obtenido exitosamente",
            "data": resumen
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener resumen semanal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al generar el resumen semanal"
        )

@router.get("/semanas-disponibles")
async def obtener_semanas_disponibles(
    limite: int = Query(12, ge=1, le=52, description="Número máximo de semanas a retornar"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene las semanas disponibles para el reponedor autenticado.
    
    Este endpoint permite a los reponedores ver qué semanas tienen tareas disponibles
    para consultar, útil para navegar por períodos anteriores.
    
    - **limite**: Número máximo de semanas a retornar (1-52)
    - Solo accesible para usuarios con rol de Reponedor
    - Retorna lista de semanas con información básica
    """
    try:
        # Verificar que el usuario sea reponedor
        if current_user.rol.nombre_rol != RolEnum.REPONEDOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los reponedores pueden acceder a este endpoint."
            )
        
        # Obtener semanas disponibles
        service = ResumenSemanalService(db)
        semanas = service.obtener_semanas_disponibles(
            reponedor_id=current_user.id_usuario,
            limite=limite
        )
        
        logger.info(f"Semanas disponibles obtenidas para reponedor {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Semanas disponibles obtenidas exitosamente",
            "data": {
                "semanas": semanas,
                "total": len(semanas)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener semanas disponibles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener semanas disponibles"
        )

@router.get("/resumen-semanal/estadisticas")
async def obtener_estadisticas_generales(
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas generales del reponedor para todas sus tareas.
    
    Este endpoint proporciona métricas generales del rendimiento del reponedor
    a lo largo de todo el tiempo.
    
    - Solo accesible para usuarios con rol de Reponedor
    - Retorna estadísticas consolidadas de todas las tareas
    """
    try:
        # Verificar que el usuario sea reponedor
        if current_user.rol.nombre_rol != RolEnum.REPONEDOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los reponedores pueden acceder a este endpoint."
            )
        
        # Obtener estadísticas generales
        from app.models.tarea import Tarea
        from app.models.detalle_tarea import DetalleTarea
        from sqlalchemy import func, and_
        
        # Total de tareas
        total_tareas = db.query(Tarea).filter(
            Tarea.id_reponedor == current_user.id_usuario
        ).count()
        
        # Tareas por estado
        tareas_por_estado = db.query(
            Tarea.estado_id,
            func.count(Tarea.id_tarea)
        ).filter(
            Tarea.id_reponedor == current_user.id_usuario
        ).group_by(Tarea.estado_id).all()
        
        # Total de productos repuestos
        total_productos = db.query(
            func.sum(DetalleTarea.cantidad)
        ).join(Tarea).filter(
            Tarea.id_reponedor == current_user.id_usuario
        ).scalar() or 0
        
        # Fechas de actividad
        fecha_primera_tarea = db.query(
            func.min(Tarea.fecha_creacion)
        ).filter(
            Tarea.id_reponedor == current_user.id_usuario
        ).scalar()
        
        fecha_ultima_tarea = db.query(
            func.max(Tarea.fecha_creacion)
        ).filter(
            Tarea.id_reponedor == current_user.id_usuario
        ).scalar()
        
        # Formatear estados
        estados_formateados = {}
        for estado_id, cantidad in tareas_por_estado:
            estado_nombre = {
                1: "pendiente",
                2: "en_progreso",
                3: "completada",
                4: "cancelada"
            }.get(estado_id, "desconocido")
            estados_formateados[estado_nombre] = cantidad
        
        estadisticas = {
            "total_tareas": total_tareas,
            "total_productos_repuestos": int(total_productos),
            "tareas_por_estado": estados_formateados,
            "periodo_actividad": {
                "fecha_primera_tarea": fecha_primera_tarea.isoformat() if fecha_primera_tarea else None,
                "fecha_ultima_tarea": fecha_ultima_tarea.isoformat() if fecha_ultima_tarea else None
            },
            "promedio_productos_por_tarea": round(total_productos / total_tareas, 2) if total_tareas > 0 else 0
        }
        
        logger.info(f"Estadísticas generales obtenidas para reponedor {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Estadísticas generales obtenidas exitosamente",
            "data": estadisticas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estadísticas generales: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener estadísticas generales"
        )

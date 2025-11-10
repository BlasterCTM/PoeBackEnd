from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.api.dependencies.database import get_database
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.services.estadisticas_puntos import EstadisticasPuntosService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/puntos-mas-usados")
async def obtener_puntos_mas_usados(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    id_producto: Optional[int] = Query(None, description="ID del producto para filtrar"),
    id_reponedor: Optional[int] = Query(None, description="ID del reponedor para filtrar"),
    limite: int = Query(50, ge=1, le=100, description="Número máximo de puntos a retornar"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un ranking de los puntos de reposición más utilizados.
    
    Este endpoint permite al administrador visualizar qué puntos de reposición
    son los más activos, con opciones de filtrado por fecha, producto y reponedor.
    
    - **fecha_inicio**: Fecha de inicio del período a analizar (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período a analizar (formato YYYY-MM-DD)
    - **id_producto**: ID del producto para filtrar (opcional)
    - **id_reponedor**: ID del reponedor para filtrar (opcional)
    - **limite**: Número máximo de puntos a retornar (1-100)
    - Solo accesible para administradores
    """
    try:
        # Verificar que el usuario sea administrador o SuperAdmin
        if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERADMIN.value]:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Validar que fecha_inicio no sea mayor que fecha_fin
        if fecha_inicio_date and fecha_fin_date and fecha_inicio_date > fecha_fin_date:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio no puede ser mayor que la fecha de fin"
            )
        
        # Verificar si es SuperAdmin
        es_superadmin = current_user.rol.nombre_rol == RolEnum.SUPERADMIN.value
        
        # Obtener estadísticas con filtro multi-tenant
        service = EstadisticasPuntosService(db)
        resultado = service.obtener_puntos_mas_usados(
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date,
            id_producto=id_producto,
            id_reponedor=id_reponedor,
            limite=limite,
            id_empresa=current_user.id_empresa,
            es_superadmin=es_superadmin
        )
        
        logger.info(f"Estadísticas de puntos más usados obtenidas por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Estadísticas de puntos más usados obtenidas exitosamente",
            "data": resultado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener puntos más usados: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener estadísticas"
        )

@router.get("/productos-disponibles")
async def obtener_productos_disponibles(
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de productos disponibles para filtrado.
    
    Este endpoint permite al administrador obtener la lista de productos
    activos que pueden ser utilizados como filtro en las estadísticas.
    
    - Solo accesible para administradores
    - Retorna lista de productos con ID, nombre y categoría
    """
    try:
        # Verificar que el usuario sea administrador
        if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Obtener productos
        service = EstadisticasPuntosService(db)
        productos = service.obtener_productos_disponibles()
        
        logger.info(f"Lista de productos disponibles obtenida por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Lista de productos disponibles obtenida exitosamente",
            "data": {
                "productos": productos,
                "total": len(productos)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener productos disponibles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener productos"
        )

@router.get("/reponedores-disponibles")
async def obtener_reponedores_disponibles(
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de reponedores disponibles para filtrado.
    
    Este endpoint permite al administrador obtener la lista de reponedores
    que pueden ser utilizados como filtro en las estadísticas.
    
    - Solo accesible para administradores
    - Retorna lista de reponedores con ID, nombre y correo
    """
    try:
        # Verificar que el usuario sea administrador
        if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Obtener reponedores
        service = EstadisticasPuntosService(db)
        reponedores = service.obtener_reponedores_disponibles()
        
        logger.info(f"Lista de reponedores disponibles obtenida por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Lista de reponedores disponibles obtenida exitosamente",
            "data": {
                "reponedores": reponedores,
                "total": len(reponedores)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener reponedores disponibles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener reponedores"
        )

@router.get("/punto-detalle/{id_punto}")
async def obtener_detalle_punto(
    id_punto: int,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene información detallada de un punto de reposición específico.
    
    Este endpoint permite al administrador ver información detallada sobre
    un punto de reposición específico, incluyendo estadísticas y productos.
    
    - **id_punto**: ID del punto de reposición
    - Solo accesible para administradores
    - Retorna información detallada del punto
    """
    try:
        # Verificar que el usuario sea administrador
        if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Obtener detalle del punto
        service = EstadisticasPuntosService(db)
        detalle = service.obtener_resumen_punto_especifico(id_punto)
        
        if "error" in detalle:
            if detalle["error"] == "Punto de reposición no encontrado":
                raise HTTPException(
                    status_code=404,
                    detail="Punto de reposición no encontrado"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=detalle["error"]
                )
        
        logger.info(f"Detalle del punto {id_punto} obtenido por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Detalle del punto obtenido exitosamente",
            "data": detalle
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalle del punto {id_punto}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener detalle del punto"
        )

@router.get("/resumen-general")
async def obtener_resumen_general_estadisticas(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un resumen general de las estadísticas de reposición.
    
    Este endpoint proporciona métricas generales sobre la actividad de reposición,
    útil para dashboards y vistas generales.
    
    - **fecha_inicio**: Fecha de inicio del período (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período (formato YYYY-MM-DD)
    - Solo accesible para administradores
    """
    try:
        # Verificar que el usuario sea administrador
        if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Obtener estadísticas generales usando el servicio
        service = EstadisticasPuntosService(db)
        resultado = service.obtener_puntos_mas_usados(
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date,
            limite=1  # Solo necesitamos las estadísticas generales
        )
        
        logger.info(f"Resumen general de estadísticas obtenido por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Resumen general de estadísticas obtenido exitosamente",
            "data": {
                "filtros_aplicados": resultado["filtros_aplicados"],
                "estadisticas_generales": resultado["estadisticas_generales"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener resumen general: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener resumen general"
        )

@router.get("/supervisor/metricas")
async def obtener_metricas_supervisor(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene métricas específicas del supervisor autenticado.
    
    Este endpoint proporciona métricas personalizadas para el supervisor,
    incluyendo estadísticas de sus reponedores y productos asociados.
    
    - **fecha_inicio**: Fecha de inicio del período (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período (formato YYYY-MM-DD)
    - Solo accesible para supervisores
    """
    try:
        # Verificar que el usuario sea supervisor
        if current_user.rol.nombre_rol != RolEnum.SUPERVISOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los supervisores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Obtener métricas del supervisor
        service = EstadisticasPuntosService(db)
        metricas = service.obtener_metricas_supervisor(
            id_supervisor=current_user.id_usuario,
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date
        )
        
        logger.info(f"Métricas del supervisor obtenidas por usuario {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Métricas del supervisor obtenidas exitosamente",
            "data": metricas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener métricas del supervisor: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener métricas del supervisor"
        )

@router.get("/supervisor/{id_supervisor}/metricas")
async def obtener_metricas_supervisor_por_id(
    id_supervisor: int,
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene métricas específicas de un supervisor por ID.
    
    Este endpoint permite al administrador obtener métricas detalladas
    de un supervisor específico, incluyendo sus reponedores y productos.
    
    - **id_supervisor**: ID del supervisor a consultar
    - **fecha_inicio**: Fecha de inicio del período (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período (formato YYYY-MM-DD)
    - Solo accesible para administradores
    """
    try:
        # Verificar que el usuario sea administrador
        if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los administradores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Obtener métricas del supervisor específico
        service = EstadisticasPuntosService(db)
        metricas = service.obtener_metricas_supervisor(
            id_supervisor=id_supervisor,
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date
        )
        
        if "error" in metricas:
            if metricas["error"] == "Supervisor no encontrado":
                raise HTTPException(
                    status_code=404,
                    detail="Supervisor no encontrado"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=metricas["error"]
                )
        
        logger.info(f"Métricas del supervisor {id_supervisor} obtenidas por administrador {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Métricas del supervisor obtenidas exitosamente",
            "data": metricas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener métricas del supervisor {id_supervisor}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener métricas del supervisor"
        )

@router.get("/supervisor/reponedores-rendimiento")
async def obtener_rendimiento_reponedores(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el rendimiento de los reponedores del supervisor autenticado.
    
    Este endpoint proporciona métricas de rendimiento de todos los reponedores
    asignados al supervisor, incluyendo tareas completadas, tiempo promedio, etc.
    
    - **fecha_inicio**: Fecha de inicio del período (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período (formato YYYY-MM-DD)
    - Solo accesible para supervisores
    """
    try:
        # Verificar que el usuario sea supervisor
        if current_user.rol.nombre_rol != RolEnum.SUPERVISOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los supervisores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Obtener rendimiento de reponedores
        service = EstadisticasPuntosService(db)
        rendimiento = service.obtener_rendimiento_reponedores_supervisor(
            id_supervisor=current_user.id_usuario,
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date
        )
        
        logger.info(f"Rendimiento de reponedores obtenido por supervisor {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Rendimiento de reponedores obtenido exitosamente",
            "data": rendimiento
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener rendimiento de reponedores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener rendimiento de reponedores"
        )

@router.get("/supervisor/productos-estadisticas")
async def obtener_estadisticas_productos_supervisor(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio del período (formato YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin del período (formato YYYY-MM-DD)"),
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas de productos del supervisor autenticado.
    
    Este endpoint proporciona métricas detalladas sobre los productos
    asignados al supervisor, incluyendo tareas de reposición, frecuencia, etc.
    
    - **fecha_inicio**: Fecha de inicio del período (formato YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin del período (formato YYYY-MM-DD)
    - Solo accesible para supervisores
    """
    try:
        # Verificar que el usuario sea supervisor
        if current_user.rol.nombre_rol != RolEnum.SUPERVISOR.value:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado. Solo los supervisores pueden acceder a este endpoint."
            )
        
        # Validar y convertir fechas
        fecha_inicio_date = None
        fecha_fin_date = None
        
        if fecha_inicio:
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Obtener estadísticas de productos
        service = EstadisticasPuntosService(db)
        estadisticas = service.obtener_estadisticas_productos_supervisor(
            id_supervisor=current_user.id_usuario,
            fecha_inicio=fecha_inicio_date,
            fecha_fin=fecha_fin_date
        )
        
        logger.info(f"Estadísticas de productos obtenidas por supervisor {current_user.id_usuario}")
        
        return {
            "success": True,
            "message": "Estadísticas de productos obtenidas exitosamente",
            "data": estadisticas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de productos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al obtener estadísticas de productos"
        )

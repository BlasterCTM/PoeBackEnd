from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from app.models.punto_reposicion import PuntoReposicion
from app.models.detalle_tarea import DetalleTarea
from app.models.tarea import Tarea
from app.models.producto import Producto
from app.models.usuario import Usuario
import logging

logger = logging.getLogger(__name__)

class EstadisticasPuntosService:
    """
    Servicio para gestionar estadísticas de puntos de reposición más usados.
    
    Este servicio permite al administrador obtener rankings de puntos de reposición
    basados en su uso, con opciones de filtrado por fecha, producto y reponedor.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_puntos_mas_usados(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_producto: Optional[int] = None,
        id_reponedor: Optional[int] = None,
        limite: int = 50,
        id_empresa: Optional[int] = None,
        es_superadmin: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene un ranking de los puntos de reposición más utilizados.
        
        **MULTI-TENANT:** Filtra por empresa (excepto SuperAdmin).
        
        Args:
            fecha_inicio: Fecha de inicio del período a analizar
            fecha_fin: Fecha de fin del período a analizar
            id_producto: ID del producto para filtrar (opcional)
            id_reponedor: ID del reponedor para filtrar (opcional)
            limite: Número máximo de puntos a retornar
            id_empresa: ID de la empresa (para filtro multi-tenant)
            es_superadmin: Si el usuario es SuperAdmin
            
        Returns:
            Dict con los filtros aplicados y el ranking de puntos
        """
        try:
            # Construir la consulta base
            query = self.db.query(
                PuntoReposicion.id_punto,
                PuntoReposicion.nivel,
                PuntoReposicion.estanteria,
                Producto.nombre.label('producto_nombre'),
                Producto.id_producto,
                func.count(DetalleTarea.id_detalle).label('total_tareas'),
                func.sum(DetalleTarea.cantidad).label('total_productos_repuestos'),
                func.count(func.distinct(DetalleTarea.id_tarea)).label('frecuencia_uso')
            ).join(
                DetalleTarea, PuntoReposicion.id_punto == DetalleTarea.id_punto
            ).join(
                Tarea, DetalleTarea.id_tarea == Tarea.id_tarea
            ).join(
                Producto, DetalleTarea.id_producto == Producto.id_producto
            )
            
            # Aplicar filtros
            filtros = []
            
            # FILTRO MULTI-TENANT: Solo SuperAdmin puede ver todas las empresas
            if not es_superadmin and id_empresa:
                filtros.append(PuntoReposicion.id_empresa == id_empresa)
            
            if fecha_inicio:
                filtros.append(Tarea.fecha_creacion >= fecha_inicio)
            
            if fecha_fin:
                filtros.append(Tarea.fecha_creacion <= fecha_fin)
            
            if id_producto:
                filtros.append(DetalleTarea.id_producto == id_producto)
            
            if id_reponedor:
                filtros.append(Tarea.id_reponedor == id_reponedor)
            
            if filtros:
                query = query.filter(and_(*filtros))
            
            # Agrupar por punto de reposición
            query = query.group_by(
                PuntoReposicion.id_punto,
                PuntoReposicion.nivel,
                PuntoReposicion.estanteria,
                Producto.nombre,
                Producto.id_producto
            )
            
            # Ordenar por frecuencia de uso (descendente)
            query = query.order_by(func.count(func.distinct(DetalleTarea.id_tarea)).desc())
            
            # Aplicar límite
            resultados = query.limit(limite).all()
            
            # Formatear resultados
            ranking = []
            for resultado in resultados:
                ranking.append({
                    "id_punto": resultado.id_punto,
                    "nivel": resultado.nivel,
                    "estanteria": resultado.estanteria,
                    "producto": resultado.producto_nombre,
                    "id_producto": resultado.id_producto,
                    "total_tareas": resultado.total_tareas,
                    "total_productos_repuestos": int(resultado.total_productos_repuestos or 0),
                    "frecuencia_uso": resultado.frecuencia_uso
                })
            
            # Obtener información adicional para los filtros aplicados
            filtros_aplicados = {
                "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
                "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
                "producto": None,
                "reponedor": None
            }
            
            # Obtener nombre del producto si se filtró por uno
            if id_producto:
                producto = self.db.query(Producto).filter(Producto.id_producto == id_producto).first()
                if producto:
                    filtros_aplicados["producto"] = {
                        "id": producto.id_producto,
                        "nombre": producto.nombre
                    }
            
            # Obtener nombre del reponedor si se filtró por uno
            if id_reponedor:
                reponedor = self.db.query(Usuario).filter(Usuario.id_usuario == id_reponedor).first()
                if reponedor:
                    filtros_aplicados["reponedor"] = {
                        "id": reponedor.id_usuario,
                        "nombre": f"{reponedor.nombres} {reponedor.apellidos}"
                    }
            
            # Calcular estadísticas adicionales
            estadisticas_generales = self._calcular_estadisticas_generales(filtros)
            
            return {
                "filtros_aplicados": filtros_aplicados,
                "ranking": ranking,
                "estadisticas_generales": estadisticas_generales,
                "total_puntos_encontrados": len(ranking),
                "limite_aplicado": limite
            }
            
        except Exception as e:
            logger.error(f"Error al obtener puntos más usados: {str(e)}")
            raise
    
    def _calcular_estadisticas_generales(self, filtros: List) -> Dict[str, Any]:
        """
        Calcula estadísticas generales para el período seleccionado.
        
        Args:
            filtros: Lista de filtros aplicados
            
        Returns:
            Dict con estadísticas generales
        """
        try:
            # Consulta para estadísticas generales
            query_stats = self.db.query(
                func.count(func.distinct(PuntoReposicion.id_punto)).label('total_puntos_utilizados'),
                func.count(DetalleTarea.id_detalle).label('total_reposiciones'),
                func.sum(DetalleTarea.cantidad).label('total_productos_repuestos'),
                func.count(func.distinct(DetalleTarea.id_tarea)).label('total_tareas')
            ).join(
                DetalleTarea, PuntoReposicion.id_punto == DetalleTarea.id_punto
            ).join(
                Tarea, DetalleTarea.id_tarea == Tarea.id_tarea
            )
            
            if filtros:
                query_stats = query_stats.filter(and_(*filtros))
            
            resultado = query_stats.first()
            
            return {
                "total_puntos_utilizados": resultado.total_puntos_utilizados or 0,
                "total_reposiciones": resultado.total_reposiciones or 0,
                "total_productos_repuestos": int(resultado.total_productos_repuestos or 0),
                "total_tareas": resultado.total_tareas or 0,
                "promedio_productos_por_tarea": round(
                    (resultado.total_productos_repuestos or 0) / max(resultado.total_tareas or 1, 1), 2
                )
            }
            
        except Exception as e:
            logger.error(f"Error al calcular estadísticas generales: {str(e)}")
            return {
                "total_puntos_utilizados": 0,
                "total_reposiciones": 0,
                "total_productos_repuestos": 0,
                "total_tareas": 0,
                "promedio_productos_por_tarea": 0
            }
    
    def obtener_productos_disponibles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de productos disponibles para filtrado.
        
        Returns:
            Lista de productos con ID y nombre
        """
        try:
            productos = self.db.query(
                Producto.id_producto,
                Producto.nombre,
                Producto.categoria
            ).filter(
                Producto.estado == "activo"
            ).order_by(
                Producto.nombre
            ).all()
            
            return [
                {
                    "id": producto.id_producto,
                    "nombre": producto.nombre,
                    "categoria": producto.categoria
                }
                for producto in productos
            ]
            
        except Exception as e:
            logger.error(f"Error al obtener productos disponibles: {str(e)}")
            return []
    
    def obtener_reponedores_disponibles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de reponedores disponibles para filtrado.
        
        Returns:
            Lista de reponedores con ID y nombre
        """
        try:
            from app.models.usuario import RolEnum
            
            reponedores = self.db.query(
                Usuario.id_usuario,
                Usuario.nombres,
                Usuario.apellidos,
                Usuario.correo
            ).join(
                Usuario.rol
            ).filter(
                Usuario.rol.has(nombre_rol=RolEnum.REPONEDOR.value)
            ).order_by(
                Usuario.nombres,
                Usuario.apellidos
            ).all()
            
            return [
                {
                    "id": reponedor.id_usuario,
                    "nombre": f"{reponedor.nombres} {reponedor.apellidos}",
                    "correo": reponedor.correo
                }
                for reponedor in reponedores
            ]
            
        except Exception as e:
            logger.error(f"Error al obtener reponedores disponibles: {str(e)}")
            return []
    
    def obtener_resumen_punto_especifico(self, id_punto: int) -> Dict[str, Any]:
        """
        Obtiene un resumen detallado de un punto de reposición específico.
        
        Args:
            id_punto: ID del punto de reposición
            
        Returns:
            Dict con información detallada del punto
        """
        try:
            # Información básica del punto
            punto = self.db.query(PuntoReposicion).filter(
                PuntoReposicion.id_punto == id_punto
            ).first()
            
            if not punto:
                return {"error": "Punto de reposición no encontrado"}
            
            # Estadísticas del punto
            estadisticas = self.db.query(
                func.count(DetalleTarea.id_detalle).label('total_reposiciones'),
                func.sum(DetalleTarea.cantidad).label('total_productos'),
                func.count(func.distinct(DetalleTarea.id_tarea)).label('total_tareas'),
                func.count(func.distinct(DetalleTarea.id_producto)).label('productos_diferentes')
            ).filter(
                DetalleTarea.id_punto == id_punto
            ).first()
            
            # Productos más repuestos en este punto
            productos_mas_repuestos = self.db.query(
                Producto.nombre,
                func.sum(DetalleTarea.cantidad).label('total_cantidad'),
                func.count(DetalleTarea.id_detalle).label('veces_repuesto')
            ).join(
                DetalleTarea, Producto.id_producto == DetalleTarea.id_producto
            ).filter(
                DetalleTarea.id_punto == id_punto
            ).group_by(
                Producto.id_producto,
                Producto.nombre
            ).order_by(
                func.sum(DetalleTarea.cantidad).desc()
            ).limit(5).all()
            
            return {
                "punto": {
                    "id": punto.id_punto,
                    "nivel": punto.nivel,
                    "estanteria": punto.estanteria,
                    "id_mueble": punto.id_mueble
                },
                "estadisticas": {
                    "total_reposiciones": estadisticas.total_reposiciones or 0,
                    "total_productos": int(estadisticas.total_productos or 0),
                    "total_tareas": estadisticas.total_tareas or 0,
                    "productos_diferentes": estadisticas.productos_diferentes or 0
                },
                "productos_mas_repuestos": [
                    {
                        "nombre": producto.nombre,
                        "total_cantidad": int(producto.total_cantidad),
                        "veces_repuesto": producto.veces_repuesto
                    }
                    for producto in productos_mas_repuestos
                ]
            }
            
        except Exception as e:
            logger.error(f"Error al obtener resumen del punto {id_punto}: {str(e)}")
            return {"error": "Error interno del servidor"}
    
    def obtener_metricas_supervisor(
        self,
        id_supervisor: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene métricas específicas de un supervisor.
        
        Args:
            id_supervisor: ID del supervisor
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Dict con las métricas del supervisor
        """
        try:
            # Verificar que el supervisor existe
            supervisor = self.db.query(Usuario).filter(
                Usuario.id_usuario == id_supervisor
            ).first()
            
            if not supervisor:
                return {"error": "Supervisor no encontrado"}
            
            # Construir filtros de fecha
            filtros = []
            if fecha_inicio:
                filtros.append(Tarea.fecha_creacion >= fecha_inicio)
            if fecha_fin:
                filtros.append(Tarea.fecha_creacion <= fecha_fin)
            
            # Obtener productos del supervisor
            productos_supervisor = self.db.query(Producto).filter(
                Producto.id_usuario == id_supervisor
            ).all()
            
            # Obtener tareas relacionadas con productos del supervisor
            tareas_query = self.db.query(Tarea).join(
                DetalleTarea
            ).join(
                Producto
            ).filter(
                Producto.id_usuario == id_supervisor
            )
            
            if filtros:
                tareas_query = tareas_query.filter(and_(*filtros))
            
            tareas_totales = tareas_query.count()
            tareas_completadas = tareas_query.filter(
                Tarea.estado == "completada"
            ).count()
            
            # Estadísticas de productos
            productos_stats = self.db.query(
                func.count(DetalleTarea.id_detalle).label('total_reposiciones'),
                func.sum(DetalleTarea.cantidad).label('total_cantidad'),
                func.count(func.distinct(DetalleTarea.id_producto)).label('productos_diferentes')
            ).join(
                Producto
            ).filter(
                Producto.id_usuario == id_supervisor
            )
            
            if filtros:
                productos_stats = productos_stats.join(Tarea).filter(and_(*filtros))
            
            stats = productos_stats.first()
            
            # Reponedores más activos - simplificado
            reponedores_activos = self.db.query(
                Usuario.id_usuario,
                Usuario.nombre,
                func.count(Tarea.id_tarea).label('tareas_completadas')
            ).join(
                Tarea, Tarea.id_reponedor == Usuario.id_usuario
            ).filter(
                Tarea.id_supervisor == id_supervisor,
                Tarea.id_reponedor.isnot(None)
            )
            
            if filtros:
                reponedores_activos = reponedores_activos.filter(and_(*filtros))
            
            reponedores_activos = reponedores_activos.group_by(
                Usuario.id_usuario,
                Usuario.nombre
            ).order_by(
                func.count(Tarea.id_tarea).desc()
            ).limit(10).all()
            
            # Productos más movidos
            productos_movidos = self.db.query(
                Producto.id_producto,
                Producto.nombre,
                func.sum(DetalleTarea.cantidad).label('total_cantidad'),
                func.count(DetalleTarea.id_detalle).label('veces_repuesto')
            ).join(
                DetalleTarea
            ).filter(
                Producto.id_usuario == id_supervisor
            )
            
            if filtros:
                productos_movidos = productos_movidos.join(Tarea).filter(and_(*filtros))
            
            productos_movidos = productos_movidos.group_by(
                Producto.id_producto,
                Producto.nombre
            ).order_by(
                func.sum(DetalleTarea.cantidad).desc()
            ).limit(10).all()
            
            return {
                "supervisor": {
                    "id": supervisor.id_usuario,
                    "nombre": supervisor.nombre,
                    "correo": supervisor.correo
                },
                "resumen_general": {
                    "total_productos": len(productos_supervisor),
                    "total_tareas": tareas_totales,
                    "tareas_completadas": tareas_completadas,
                    "tasa_completacion": round((tareas_completadas / tareas_totales * 100) if tareas_totales > 0 else 0, 2),
                    "total_reposiciones": int(stats.total_reposiciones or 0),
                    "total_cantidad_repuesta": int(stats.total_cantidad or 0),
                    "productos_diferentes_repuestos": int(stats.productos_diferentes or 0)
                },
                "reponedores_activos": [
                    {
                        "id": rep.id_usuario,
                        "nombre": rep.nombre,
                        "tareas_completadas": rep.tareas_completadas
                    }
                    for rep in reponedores_activos
                ],
                "productos_mas_movidos": [
                    {
                        "id": prod.id_producto,
                        "nombre": prod.nombre,
                        "total_cantidad": int(prod.total_cantidad),
                        "veces_repuesto": prod.veces_repuesto
                    }
                    for prod in productos_movidos
                ],
                "filtros_aplicados": {
                    "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None,
                    "fecha_fin": fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener métricas del supervisor {id_supervisor}: {str(e)}")
            return {"error": "Error interno del servidor"}
    
    def obtener_rendimiento_reponedores_supervisor(
        self,
        id_supervisor: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene el rendimiento de los reponedores de un supervisor.
        
        Args:
            id_supervisor: ID del supervisor
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Dict con el rendimiento de reponedores
        """
        try:
            logger.info(f"Iniciando obtención de rendimiento para supervisor {id_supervisor}")
            
            # Construir filtros de fecha
            filtros = [Tarea.id_supervisor == id_supervisor]
            if fecha_inicio:
                filtros.append(Tarea.fecha_creacion >= fecha_inicio)
                logger.info(f"Filtro fecha_inicio: {fecha_inicio}")
            if fecha_fin:
                filtros.append(Tarea.fecha_creacion <= fecha_fin)
                logger.info(f"Filtro fecha_fin: {fecha_fin}")
            
            # Obtener rendimiento de reponedores usando subconsulta más simple
            logger.info("Construyendo consulta de rendimiento...")
            rendimiento_query = self.db.query(
                Usuario.id_usuario,
                Usuario.nombre,
                Usuario.correo,
                func.count(Tarea.id_tarea).label('tareas_totales'),
                func.sum(
                    case(
                        (Tarea.estado_id == 3, 1),
                        else_=0
                    )
                ).label('tareas_completadas')
            ).join(
                Tarea, Tarea.id_reponedor == Usuario.id_usuario
            ).filter(
                and_(*filtros),
                Tarea.id_reponedor.isnot(None)
            ).group_by(
                Usuario.id_usuario,
                Usuario.nombre,
                Usuario.correo
            ).order_by(
                func.count(Tarea.id_tarea).desc()
            )
            
            logger.info("Ejecutando consulta...")
            rendimiento_result = rendimiento_query.all()
            logger.info(f"Consulta ejecutada, {len(rendimiento_result)} resultados")
            
            return {
                "reponedores": [
                    {
                        "id": rep.id_usuario,
                        "nombre": rep.nombre,
                        "correo": rep.correo,
                        "tareas_totales": rep.tareas_totales,
                        "tareas_completadas": rep.tareas_completadas,
                        "tasa_completacion": round((rep.tareas_completadas / rep.tareas_totales * 100) if rep.tareas_totales > 0 else 0, 2),
                        "tiempo_promedio_horas": 0  # Simplificado por ahora
                    }
                    for rep in rendimiento_result
                ],
                "filtros_aplicados": {
                    "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None,
                    "fecha_fin": fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener rendimiento de reponedores del supervisor {id_supervisor}: {str(e)}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Error interno del servidor: {str(e)}"}
    
    def obtener_estadisticas_productos_supervisor(
        self,
        id_supervisor: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de productos de un supervisor.
        
        Args:
            id_supervisor: ID del supervisor
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Dict con las estadísticas de productos
        """
        try:
            logger.info(f"Iniciando obtención de estadísticas de productos para supervisor {id_supervisor}")
            
            # Construir filtros de fecha
            filtros = []
            if fecha_inicio:
                filtros.append(Tarea.fecha_creacion >= fecha_inicio)
                logger.info(f"Filtro fecha_inicio: {fecha_inicio}")
            if fecha_fin:
                filtros.append(Tarea.fecha_creacion <= fecha_fin)
                logger.info(f"Filtro fecha_fin: {fecha_fin}")
            
            # Obtener estadísticas de productos - consulta simplificada
            logger.info("Construyendo consulta de productos...")
            productos_query = self.db.query(
                Producto.id_producto,
                Producto.nombre,
                Producto.codigo_unico,
                Producto.unidad_tipo,
                func.count(DetalleTarea.id_detalle).label('total_reposiciones'),
                func.sum(DetalleTarea.cantidad).label('total_cantidad'),
                func.count(func.distinct(DetalleTarea.id_punto)).label('puntos_diferentes'),
                func.avg(DetalleTarea.cantidad).label('cantidad_promedio')
            ).join(
                DetalleTarea, DetalleTarea.id_producto == Producto.id_producto
            ).filter(
                Producto.id_usuario == id_supervisor
            )
            
            # Aplicar filtros de fecha si existen
            if filtros:
                productos_query = productos_query.join(
                    Tarea, Tarea.id_tarea == DetalleTarea.id_tarea
                ).filter(and_(*filtros))
            
            productos_query = productos_query.group_by(
                Producto.id_producto,
                Producto.nombre,
                Producto.codigo_unico,
                Producto.unidad_tipo
            ).order_by(
                func.sum(DetalleTarea.cantidad).desc()
            )
            
            logger.info("Ejecutando consulta de productos...")
            productos = productos_query.all()
            logger.info(f"Consulta de productos ejecutada, {len(productos)} resultados")
            
            # Productos con más frecuencia de reposición - consulta simplificada
            logger.info("Construyendo consulta de productos frecuentes...")
            productos_frecuentes_query = self.db.query(
                Producto.id_producto,
                Producto.nombre,
                func.count(DetalleTarea.id_detalle).label('frecuencia_reposicion')
            ).join(
                DetalleTarea, DetalleTarea.id_producto == Producto.id_producto
            ).filter(
                Producto.id_usuario == id_supervisor
            )
            
            # Aplicar filtros de fecha si existen
            if filtros:
                productos_frecuentes_query = productos_frecuentes_query.join(
                    Tarea, Tarea.id_tarea == DetalleTarea.id_tarea
                ).filter(and_(*filtros))
            
            productos_frecuentes_query = productos_frecuentes_query.group_by(
                Producto.id_producto,
                Producto.nombre
            ).order_by(
                func.count(DetalleTarea.id_detalle).desc()
            ).limit(10)
            
            logger.info("Ejecutando consulta de productos frecuentes...")
            productos_frecuentes = productos_frecuentes_query.all()
            logger.info(f"Consulta de productos frecuentes ejecutada, {len(productos_frecuentes)} resultados")
            
            return {
                "productos": [
                    {
                        "id": prod.id_producto,
                        "nombre": prod.nombre,
                        "codigo_unico": prod.codigo_unico,
                        "unidad_tipo": prod.unidad_tipo,
                        "total_reposiciones": prod.total_reposiciones,
                        "total_cantidad": int(prod.total_cantidad or 0),
                        "puntos_diferentes": prod.puntos_diferentes,
                        "cantidad_promedio": round(prod.cantidad_promedio, 2) if prod.cantidad_promedio else 0
                    }
                    for prod in productos
                ],
                "productos_mas_frecuentes": [
                    {
                        "id": prod.id_producto,
                        "nombre": prod.nombre,
                        "frecuencia_reposicion": prod.frecuencia_reposicion
                    }
                    for prod in productos_frecuentes
                ],
                "resumen": {
                    "total_productos": len(productos),
                    "total_reposiciones": sum(prod.total_reposiciones for prod in productos),
                    "total_cantidad": sum(int(prod.total_cantidad or 0) for prod in productos)
                },
                "filtros_aplicados": {
                    "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None,
                    "fecha_fin": fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de productos del supervisor {id_supervisor}: {str(e)}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Error interno del servidor: {str(e)}"}

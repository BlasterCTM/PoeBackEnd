from sqlalchemy.orm import Session
from sqlalchemy import func, and_
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
        limite: int = 50
    ) -> Dict[str, Any]:
        """
        Obtiene un ranking de los puntos de reposición más utilizados.
        
        Args:
            fecha_inicio: Fecha de inicio del período a analizar
            fecha_fin: Fecha de fin del período a analizar
            id_producto: ID del producto para filtrar (opcional)
            id_reponedor: ID del reponedor para filtrar (opcional)
            limite: Número máximo de puntos a retornar
            
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

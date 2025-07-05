from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.tarea import Tarea
from app.models.detalle_tarea import DetalleTarea
from app.models.producto import Producto
from app.models.usuario import Usuario
import logging

logger = logging.getLogger(__name__)

class ResumenSemanalService:
    """Servicio para generar resúmenes semanales de tareas para reponedores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_resumen_semanal(self, reponedor_id: int, fecha_inicio: date = None) -> Dict:
        """
        Obtiene el resumen semanal de tareas para un reponedor específico.
        
        Args:
            reponedor_id: ID del reponedor
            fecha_inicio: Fecha de inicio de la semana (lunes). Si no se especifica, usa la semana actual
            
        Returns:
            Dict con estructura de calendario semanal
        """
        try:
            # Si no se especifica fecha_inicio, usar el lunes de la semana actual
            if fecha_inicio is None:
                hoy = date.today()
                dias_desde_lunes = hoy.weekday()
                fecha_inicio = hoy - timedelta(days=dias_desde_lunes)
            
            # Asegurar que fecha_inicio sea un lunes
            if fecha_inicio.weekday() != 0:
                dias_desde_lunes = fecha_inicio.weekday()
                fecha_inicio = fecha_inicio - timedelta(days=dias_desde_lunes)
            
            fecha_fin = fecha_inicio + timedelta(days=6)
            
            logger.info(f"Generando resumen semanal para reponedor {reponedor_id} del {fecha_inicio} al {fecha_fin}")
            
            # Obtener información del reponedor
            reponedor = self.db.query(Usuario).filter(Usuario.id_usuario == reponedor_id).first()
            if not reponedor:
                raise ValueError(f"Reponedor con ID {reponedor_id} no encontrado")
            
            # Obtener tareas del reponedor en el rango de fechas
            tareas_query = self.db.query(Tarea).filter(
                and_(
                    Tarea.id_reponedor == reponedor_id,
                    Tarea.fecha_creacion >= fecha_inicio,
                    Tarea.fecha_creacion <= fecha_fin
                )
            ).all()
            
            # Crear estructura de calendario
            calendario = self._crear_estructura_calendario(fecha_inicio, fecha_fin)
            
            # Procesar tareas y agrupar por día
            for tarea in tareas_query:
                fecha_tarea = tarea.fecha_creacion
                dia_semana = self._obtener_dia_semana(fecha_tarea)
                
                # Obtener detalles de la tarea
                detalles = self.db.query(DetalleTarea).filter(
                    DetalleTarea.id_tarea == tarea.id_tarea
                ).all()
                
                # Crear información de la tarea
                tarea_info = {
                    "id_tarea": tarea.id_tarea,
                    "estado_id": tarea.estado_id,
                    "fecha_creacion": fecha_tarea.isoformat(),
                    "fecha_hora_completada": tarea.fecha_hora_completada.isoformat() if tarea.fecha_hora_completada else None,
                    "total_productos": len(detalles),
                    "productos": []
                }
                
                # Agregar información de productos
                for detalle in detalles:
                    producto = self.db.query(Producto).filter(
                        Producto.id_producto == detalle.id_producto
                    ).first()
                    
                    if producto:
                        tarea_info["productos"].append({
                            "id_producto": producto.id_producto,
                            "nombre": producto.nombre,
                            "categoria": producto.categoria,
                            "cantidad": detalle.cantidad
                        })
                
                # Agregar tarea al día correspondiente
                calendario[dia_semana]["tareas"].append(tarea_info)
                calendario[dia_semana]["total_tareas"] += 1
                
                # Actualizar contadores por estado
                estado_str = self._obtener_estado_string(tarea.estado_id)
                if estado_str not in calendario[dia_semana]["tareas_por_estado"]:
                    calendario[dia_semana]["tareas_por_estado"][estado_str] = 0
                calendario[dia_semana]["tareas_por_estado"][estado_str] += 1
            
            # Calcular estadísticas generales
            estadisticas = self._calcular_estadisticas_semanales(calendario)
            
            return {
                "reponedor": {
                    "id": reponedor.id_usuario,
                    "nombre": reponedor.nombre,
                    "correo": reponedor.correo
                },
                "periodo": {
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "semana": f"Semana del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
                },
                "calendario": calendario,
                "estadisticas": estadisticas
            }
            
        except Exception as e:
            logger.error(f"Error al generar resumen semanal: {str(e)}")
            raise
    
    def _crear_estructura_calendario(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Crea la estructura base del calendario semanal"""
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        calendario = {}
        
        for i, dia in enumerate(dias_semana):
            fecha_dia = fecha_inicio + timedelta(days=i)
            calendario[dia] = {
                "fecha": fecha_dia.isoformat(),
                "dia_nombre": dia.capitalize(),
                "tareas": [],
                "total_tareas": 0,
                "tareas_por_estado": {}
            }
        
        return calendario
    
    def _obtener_dia_semana(self, fecha: date) -> str:
        """Obtiene el nombre del día de la semana para una fecha"""
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        return dias[fecha.weekday()]
    
    def _obtener_estado_string(self, estado_id: int) -> str:
        """Convierte el ID del estado a string legible"""
        estados = {
            1: "pendiente",
            2: "en_progreso", 
            3: "completada",
            4: "cancelada"
        }
        return estados.get(estado_id, "desconocido")
    
    def _calcular_estadisticas_semanales(self, calendario: Dict) -> Dict:
        """Calcula estadísticas generales de la semana"""
        total_tareas = 0
        total_productos = 0
        estados_resumen = {}
        dias_con_tareas = 0
        
        for dia, datos in calendario.items():
            if datos["total_tareas"] > 0:
                dias_con_tareas += 1
                total_tareas += datos["total_tareas"]
                
                # Contar productos
                for tarea in datos["tareas"]:
                    total_productos += tarea["total_productos"]
                
                # Consolidar estados
                for estado, cantidad in datos["tareas_por_estado"].items():
                    if estado not in estados_resumen:
                        estados_resumen[estado] = 0
                    estados_resumen[estado] += cantidad
        
        return {
            "total_tareas": total_tareas,
            "total_productos": total_productos,
            "dias_con_tareas": dias_con_tareas,
            "tareas_por_estado": estados_resumen,
            "promedio_tareas_por_dia": round(total_tareas / 7, 2) if total_tareas > 0 else 0,
            "promedio_productos_por_tarea": round(total_productos / total_tareas, 2) if total_tareas > 0 else 0
        }
    
    def obtener_semanas_disponibles(self, reponedor_id: int, limite: int = 12) -> List[Dict]:
        """
        Obtiene las semanas disponibles para un reponedor (con tareas)
        
        Args:
            reponedor_id: ID del reponedor
            limite: Número máximo de semanas a retornar
            
        Returns:
            Lista de semanas con información básica
        """
        try:
            # Obtener fechas de tareas del reponedor
            fechas_tareas = self.db.query(Tarea.fecha_creacion).filter(
                Tarea.id_reponedor == reponedor_id
            ).distinct().order_by(Tarea.fecha_creacion.desc()).limit(limite * 7).all()
            
            if not fechas_tareas:
                return []
            
            semanas = set()
            for fecha_tuple in fechas_tareas:
                fecha = fecha_tuple[0]
                # Obtener el lunes de esa semana
                dias_desde_lunes = fecha.weekday()
                lunes = fecha - timedelta(days=dias_desde_lunes)
                semanas.add(lunes)
            
            # Convertir a lista y ordenar
            semanas_lista = sorted(list(semanas), reverse=True)[:limite]
            
            resultado = []
            for lunes in semanas_lista:
                domingo = lunes + timedelta(days=6)
                
                # Contar tareas de esa semana
                total_tareas = self.db.query(Tarea).filter(
                    and_(
                        Tarea.id_reponedor == reponedor_id,
                        Tarea.fecha_creacion >= lunes,
                        Tarea.fecha_creacion <= domingo
                    )
                ).count()
                
                resultado.append({
                    "fecha_inicio": lunes.isoformat(),
                    "fecha_fin": domingo.isoformat(),
                    "descripcion": f"Semana del {lunes.strftime('%d/%m/%Y')} al {domingo.strftime('%d/%m/%Y')}",
                    "total_tareas": total_tareas
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al obtener semanas disponibles: {str(e)}")
            raise

from datetime import date, timedelta, datetime
from sqlalchemy import func, and_
from app.models.tarea import Tarea
from app.models.detalle_tarea import DetalleTarea
from app.models.producto import Producto
from app.models.usuario import Usuario, RolEnum
from typing import Optional

class DashboardService:
    def __init__(self, db):
        self.db = db

    def resumen(self, periodo: str = "dia", fecha_base: date = None, id_empresa: Optional[int] = None, es_superadmin: bool = False):
        if fecha_base is None:
            fecha_base = date.today()

        if periodo == "dia":
            fecha_inicio = fecha_base
            fecha_fin = fecha_base
        elif periodo == "semana":
            # Lunes a domingo de la semana de la fecha_base
            fecha_inicio = fecha_base - timedelta(days=fecha_base.weekday())
            fecha_fin = fecha_inicio + timedelta(days=6)
        elif periodo == "mes":
            fecha_inicio = fecha_base.replace(day=1)
            if fecha_base.month == 12:
                fecha_fin = fecha_base.replace(year=fecha_base.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fecha_fin = fecha_base.replace(month=fecha_base.month+1, day=1) - timedelta(days=1)
        else:
            raise ValueError("Periodo no válido. Usa 'dia', 'semana' o 'mes'.")

        # Tareas por estado
        query_tareas = self.db.query(Tarea.estado_id, func.count())
        
        # FILTRO MULTI-TENANT: Solo SuperAdmin puede ver todas las empresas
        if not es_superadmin and id_empresa:
            query_tareas = query_tareas.filter(Tarea.id_empresa == id_empresa)
        
        tareas_estado = (
            query_tareas
            .filter(and_(func.date(Tarea.fecha_creacion) >= fecha_inicio, func.date(Tarea.fecha_creacion) <= fecha_fin))
            .group_by(Tarea.estado_id)
            .all()
        )
        estados_map = {1: "pendientes", 2: "en_progreso", 3: "completadas"}  # Ajusta según tus IDs
        tareas = {"total": 0, "pendientes": 0, "en_progreso": 0, "completadas": 0}
        for estado_id, count in tareas_estado:
            nombre = estados_map.get(estado_id, "otros")
            tareas[nombre] = count
            tareas["total"] += count

        # Top productos más repuestos
        query_productos = (
            self.db.query(Producto.nombre, func.sum(DetalleTarea.cantidad).label("cantidad_repuesta"))
            .join(DetalleTarea, DetalleTarea.id_producto == Producto.id_producto)
            .join(Tarea, Tarea.id_tarea == DetalleTarea.id_tarea)
        )
        
        # FILTRO MULTI-TENANT: Solo SuperAdmin puede ver todas las empresas
        if not es_superadmin and id_empresa:
            query_productos = query_productos.filter(Producto.id_empresa == id_empresa)
        
        top_productos = (
            query_productos
            .filter(and_(func.date(Tarea.fecha_creacion) >= fecha_inicio, func.date(Tarea.fecha_creacion) <= fecha_fin))
            .group_by(Producto.nombre)
            .order_by(func.sum(DetalleTarea.cantidad).desc())
            .limit(5)
            .all()
        )
        top_productos = [{"nombre": n, "cantidad_repuesta": c} for n, c in top_productos]

        # Actividad por usuario
        query_actividad = (
            self.db.query(
                Usuario.nombre,
                func.count(Tarea.id_tarea).label("tareas_completadas"),
                func.coalesce(func.sum(func.extract('epoch', Tarea.fecha_hora_completada - Tarea.fecha_creacion)) / 60, 0).label("tiempo_total_minutos")
            )
            .join(Tarea, Tarea.id_reponedor == Usuario.id_usuario)
        )
        
        # FILTRO MULTI-TENANT: Solo SuperAdmin puede ver todas las empresas
        if not es_superadmin and id_empresa:
            query_actividad = query_actividad.filter(Usuario.id_empresa == id_empresa)
        
        actividad = (
            query_actividad
            .filter(
                and_(func.date(Tarea.fecha_creacion) >= fecha_inicio, func.date(Tarea.fecha_creacion) <= fecha_fin),
                Tarea.estado_id == 3  # Completada
            )
            .group_by(Usuario.nombre)
            .all()
        )
        actividad_usuarios = [
            {
                "nombre": n,
                "tareas_completadas": t,
                "tiempo_total_minutos": int(tt)
            }
            for n, t, tt in actividad
        ]

        return {
            "tareas": tareas,
            "top_productos": top_productos,
            "actividad_usuarios": actividad_usuarios,
            "periodo": periodo,
            "fecha_inicio": str(fecha_inicio),
            "fecha_fin": str(fecha_fin)
        }

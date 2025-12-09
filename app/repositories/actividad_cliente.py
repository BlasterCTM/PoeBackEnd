from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.actividad_cliente import ActividadCliente
from app.repositories.base import BaseRepository
from datetime import datetime, timedelta


class ActividadClienteRepository(BaseRepository[ActividadCliente]):
    """Repository para gestión de actividades de cliente"""
    
    def __init__(self):
        super().__init__(ActividadCliente)
    
    def get_by_id(self, db: Session, id_actividad: int) -> Optional[ActividadCliente]:
        """Obtiene actividad por ID"""
        return db.query(ActividadCliente).filter(ActividadCliente.id_actividad == id_actividad).first()
    
    def get_by_empresa(
        self, 
        db: Session, 
        id_empresa: int, 
        skip: int = 0, 
        limit: int = 100,
        tipo: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[ActividadCliente]:
        """Obtiene actividades de una empresa"""
        query = db.query(ActividadCliente).filter(ActividadCliente.id_empresa == id_empresa)
        
        if tipo:
            query = query.filter(ActividadCliente.tipo == tipo)
        
        if estado:
            query = query.filter(ActividadCliente.estado == estado)
        
        return query.order_by(ActividadCliente.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        tipo: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[ActividadCliente]:
        """Obtiene todas las actividades con filtros opcionales"""
        query = db.query(ActividadCliente)
        
        if tipo:
            query = query.filter(ActividadCliente.tipo == tipo)
        
        if estado:
            query = query.filter(ActividadCliente.estado == estado)
        
        return query.order_by(ActividadCliente.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    def get_pendientes(self, db: Session, id_empresa: Optional[int] = None) -> List[ActividadCliente]:
        """Obtiene actividades pendientes"""
        query = db.query(ActividadCliente).filter(ActividadCliente.estado == "pendiente")
        
        if id_empresa:
            query = query.filter(ActividadCliente.id_empresa == id_empresa)
        
        return query.order_by(ActividadCliente.fecha_programada).all()
    
    def get_proximas(self, db: Session, dias: int = 7) -> List[ActividadCliente]:
        """Obtiene actividades programadas para los próximos N días"""
        hoy = datetime.utcnow().date()
        fecha_limite = hoy + timedelta(days=dias)
        
        return db.query(ActividadCliente).filter(
            and_(
                ActividadCliente.estado.in_(["pendiente", "en_progreso"]),
                ActividadCliente.fecha_programada >= hoy,
                ActividadCliente.fecha_programada <= fecha_limite
            )
        ).order_by(ActividadCliente.fecha_programada).all()
    
    def create(self, db: Session, actividad_data: dict) -> ActividadCliente:
        """Crea una nueva actividad"""
        actividad = ActividadCliente(**actividad_data)
        db.add(actividad)
        db.commit()
        db.refresh(actividad)
        return actividad
    
    def update(self, db: Session, id_actividad: int, update_data: dict) -> Optional[ActividadCliente]:
        """Actualiza una actividad"""
        actividad = self.get_by_id(db, id_actividad)
        if not actividad:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(actividad, key, value)
        
        db.commit()
        db.refresh(actividad)
        return actividad
    
    def marcar_completada(self, db: Session, id_actividad: int) -> Optional[ActividadCliente]:
        """Marca una actividad como completada"""
        actividad = self.get_by_id(db, id_actividad)
        if not actividad:
            return None
        
        actividad.estado = "completada"
        actividad.fecha_completada = datetime.utcnow().date()
        
        db.commit()
        db.refresh(actividad)
        return actividad
    
    def get_stats(self, db: Session, id_empresa: Optional[int] = None) -> dict:
        """Obtiene estadísticas de actividades"""
        query = db.query(ActividadCliente)
        if id_empresa:
            query = query.filter(ActividadCliente.id_empresa == id_empresa)
        
        total = query.count()
        
        # Contar por estado
        pendientes = query.filter(ActividadCliente.estado == "pendiente").count()
        en_progreso = query.filter(ActividadCliente.estado == "en_progreso").count()
        completadas = query.filter(ActividadCliente.estado == "completada").count()
        canceladas = query.filter(ActividadCliente.estado == "cancelada").count()
        
        # Contar por tipo
        por_tipo = {}
        tipos = ["capacitacion", "soporte", "incidencia", "reunion", "upgrade", "otro"]
        for tipo in tipos:
            count = query.filter(ActividadCliente.tipo == tipo).count()
            por_tipo[tipo] = count
        
        # Próximas 7 días
        hoy = datetime.utcnow().date()
        fecha_limite = hoy + timedelta(days=7)
        proximas_7_dias = query.filter(
            and_(
                ActividadCliente.fecha_programada >= hoy,
                ActividadCliente.fecha_programada <= fecha_limite
            )
        ).count()
        
        # Vencidas (pendientes con fecha pasada)
        vencidas = query.filter(
            and_(
                ActividadCliente.estado == "pendiente",
                ActividadCliente.fecha_programada < hoy
            )
        ).count()
        
        return {
            "total": total,
            "pendientes": pendientes,
            "en_progreso": en_progreso,
            "completadas": completadas,
            "canceladas": canceladas,
            "por_tipo": por_tipo,
            "proximas_7_dias": proximas_7_dias,
            "vencidas": vencidas
        }

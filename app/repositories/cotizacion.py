from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.cotizacion import Cotizacion
from app.repositories.base import BaseRepository


class CotizacionRepository(BaseRepository[Cotizacion]):
    """Repository para gestión de cotizaciones"""
    
    def __init__(self):
        super().__init__(Cotizacion)
    
    def get_by_id(self, db: Session, id_cotizacion: int) -> Optional[Cotizacion]:
        """Obtiene cotización por ID"""
        return db.query(Cotizacion).filter(Cotizacion.id_cotizacion == id_cotizacion).first()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        estado: Optional[str] = None
    ) -> List[Cotizacion]:
        """Obtiene todas las cotizaciones con filtros opcionales"""
        query = db.query(Cotizacion)
        
        if estado:
            query = query.filter(Cotizacion.estado == estado)
        
        return query.order_by(Cotizacion.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    def get_by_email(self, db: Session, email: str) -> List[Cotizacion]:
        """Obtiene cotizaciones por email"""
        return db.query(Cotizacion).filter(Cotizacion.email == email).order_by(Cotizacion.fecha_creacion.desc()).all()
    
    def get_pendientes(self, db: Session) -> List[Cotizacion]:
        """Obtiene cotizaciones pendientes de revisión"""
        return db.query(Cotizacion).filter(
            Cotizacion.estado.in_(["pendiente", "en_revision"])
        ).order_by(Cotizacion.fecha_creacion.desc()).all()
    
    def create(self, db: Session, cotizacion_data: dict) -> Cotizacion:
        """Crea una nueva cotización"""
        cotizacion = Cotizacion(**cotizacion_data)
        db.add(cotizacion)
        db.commit()
        db.refresh(cotizacion)
        return cotizacion
    
    def update(self, db: Session, id_cotizacion: int, update_data: dict) -> Optional[Cotizacion]:
        """Actualiza una cotización"""
        cotizacion = self.get_by_id(db, id_cotizacion)
        if not cotizacion:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(cotizacion, key, value)
        
        db.commit()
        db.refresh(cotizacion)
        return cotizacion
    
    def cambiar_estado(
        self, 
        db: Session, 
        id_cotizacion: int, 
        nuevo_estado: str,
        id_usuario: Optional[int] = None
    ) -> Optional[Cotizacion]:
        """Cambia el estado de una cotización"""
        cotizacion = self.get_by_id(db, id_cotizacion)
        if not cotizacion:
            return None
        
        cotizacion.estado = nuevo_estado
        if id_usuario:
            cotizacion.atendido_por = id_usuario
        
        db.commit()
        db.refresh(cotizacion)
        return cotizacion
    
    def marcar_convertida(
        self, 
        db: Session, 
        id_cotizacion: int, 
        id_empresa: int,
        id_plan: int
    ) -> Optional[Cotizacion]:
        """Marca una cotización como convertida"""
        cotizacion = self.get_by_id(db, id_cotizacion)
        if not cotizacion:
            return None
        
        from datetime import datetime
        cotizacion.estado = "convertida"
        cotizacion.id_empresa_creada = id_empresa
        cotizacion.id_plan_creado = id_plan
        cotizacion.fecha_conversion = datetime.utcnow().date()
        
        db.commit()
        db.refresh(cotizacion)
        return cotizacion
    
    def get_stats(self, db: Session) -> dict:
        """Obtiene estadísticas de cotizaciones"""
        total = db.query(func.count(Cotizacion.id_cotizacion)).scalar()
        
        # Contar por estado
        pendientes = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "pendiente"
        ).scalar()
        
        en_revision = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "en_revision"
        ).scalar()
        
        cotizadas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "cotizada"
        ).scalar()
        
        aprobadas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "aprobada"
        ).scalar()
        
        rechazadas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "rechazada"
        ).scalar()
        
        convertidas = db.query(func.count(Cotizacion.id_cotizacion)).filter(
            Cotizacion.estado == "convertida"
        ).scalar()
        
        # Montos
        monto_total_cotizado = db.query(func.coalesce(func.sum(Cotizacion.precio_final), 0)).scalar()
        monto_total_convertido = db.query(func.coalesce(func.sum(Cotizacion.precio_final), 0)).filter(
            Cotizacion.estado == "convertida"
        ).scalar()
        
        # Tasa de conversión
        tasa_conversion = (convertidas / total * 100) if total > 0 else 0
        
        return {
            "total": total or 0,
            "pendientes": pendientes or 0,
            "en_revision": en_revision or 0,
            "cotizadas": cotizadas or 0,
            "aprobadas": aprobadas or 0,
            "rechazadas": rechazadas or 0,
            "convertidas": convertidas or 0,
            "monto_total_cotizado": int(monto_total_cotizado or 0),
            "monto_total_convertido": int(monto_total_convertido or 0),
            "tasa_conversion": round(tasa_conversion, 2)
        }

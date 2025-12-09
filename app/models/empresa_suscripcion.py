from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base

class EmpresaSuscripcion(Base):
    """Modelo para la tabla empresa_suscripcion (Vincula empresa con su plan activo)"""
    __tablename__ = "empresa_suscripcion"
    
    id_suscripcion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False, unique=True)
    id_plan = Column(Integer, ForeignKey("plan_suscripcion.id_plan"), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=False)
    estado_pago = Column(String(20), nullable=False, default="pendiente")
    id_pago_externo = Column(String(100))
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="suscripcion")
    plan = relationship("PlanSuscripcion", back_populates="suscripciones")

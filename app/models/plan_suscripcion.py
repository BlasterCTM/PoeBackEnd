from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class PlanSuscripcion(Base):
    """Modelo para la tabla plan_suscripcion (Catálogo de planes B2B)"""
    __tablename__ = "plan_suscripcion"
    
    id_plan = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_plan = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    precio_mensual = Column(Numeric(10, 2), nullable=False, default=0.00)
    limite_usuarios = Column(Integer)
    limite_rutas_mes = Column(Integer)
    soporte_ia = Column(Boolean, default=False)
    estado = Column(String(20), nullable=False, default="activo")
    
    # Relaciones
    suscripciones = relationship("EmpresaSuscripcion", back_populates="plan")

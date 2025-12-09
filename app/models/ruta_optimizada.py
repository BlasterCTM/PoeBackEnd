from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class RutaOptimizada(Base):
    __tablename__ = "ruta_optimizada"
    
    id_ruta = Column(Integer, primary_key=True, index=True)
    id_reponedor = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_tarea = Column(Integer, ForeignKey("tarea.id_tarea"), nullable=False)
    fecha_generada = Column(Date, nullable=False)
    algoritmo_usado = Column(String(50), nullable=True)
    tiempo_estimado = Column(Float, nullable=True)
    distancia_total = Column(Float, nullable=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)
    
    # Relaciones
    reponedor = relationship("Usuario")
    tarea = relationship("Tarea")
    detalles = relationship("DetalleRuta", back_populates="ruta", cascade="all, delete-orphan")
    metricas = relationship("MetricaOptimizacion", back_populates="ruta", cascade="all, delete-orphan")
    empresa = relationship("Empresa", back_populates="rutas")

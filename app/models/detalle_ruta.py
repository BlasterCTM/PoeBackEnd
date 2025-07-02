from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class DetalleRuta(Base):
    __tablename__ = "detalle_ruta"
    
    id_detalle_ruta = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey("ruta_optimizada.id_ruta"), nullable=False)
    orden = Column(Integer, nullable=False)
    id_punto = Column(Integer, ForeignKey("punto_reposicion.id_punto"), nullable=False)
    tiempo_estimado_punto = Column(Float, nullable=True)
    id_detalle_tarea = Column(Integer, ForeignKey("detalle_tarea.id_detalle"), nullable=True)
    
    # Relaciones
    ruta = relationship("RutaOptimizada", back_populates="detalles")
    punto = relationship("PuntoReposicion")
    pasos = relationship("PasoRuta", back_populates="detalle_ruta", cascade="all, delete-orphan")
    detalle_tarea = relationship("DetalleTarea")

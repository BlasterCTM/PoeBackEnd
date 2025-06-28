from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class MetricaOptimizacion(Base):
    __tablename__ = "metrica_optimizacion"
    
    id_metrica = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey("ruta_optimizada.id_ruta"), nullable=False)
    tiempo_real = Column(Float, nullable=True)
    desviaciones = Column(Integer, nullable=True)
    eficiencia = Column(Float, nullable=True)
    
    # Relaciones
    ruta = relationship("RutaOptimizada", back_populates="metricas")

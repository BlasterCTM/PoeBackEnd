from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class PasoRuta(Base):
    __tablename__ = "paso_ruta"
    
    id_paso = Column(Integer, primary_key=True, index=True)
    id_detalle_ruta = Column(Integer, ForeignKey("detalle_ruta.id_detalle_ruta", ondelete="CASCADE"), nullable=False)
    secuencia = Column(Integer, nullable=False)  # orden del paso dentro de la ruta
    x = Column(Integer, nullable=False)          # coordenada X
    y = Column(Integer, nullable=False)          # coordenada Y
    
    # Relaciones
    detalle_ruta = relationship("DetalleRuta", back_populates="pasos")

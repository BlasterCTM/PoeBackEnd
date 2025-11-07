from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class Mapa(Base):
    __tablename__ = "mapa"
    id_mapa = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ancho = Column(Integer, nullable=False)
    alto = Column(Integer, nullable=False)
    activo = Column(Boolean, default=False)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="mapas")

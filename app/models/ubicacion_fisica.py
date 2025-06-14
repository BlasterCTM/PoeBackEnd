from sqlalchemy import Column, Integer, ForeignKey
from app.core.database.database import Base

class UbicacionFisica(Base):
    __tablename__ = "ubicacion_fisica"
    id_ubicacion = Column(Integer, primary_key=True, index=True)
    id_mapa = Column(Integer, ForeignKey("mapa.id_mapa"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    id_objeto = Column(Integer, ForeignKey("objeto_mapa.id_objeto"), nullable=True)

from sqlalchemy import Column, Integer, ForeignKey
from app.core.database.database import Base

class MuebleReposicion(Base):
    __tablename__ = "mueble_reposicion"
    id_mueble = Column(Integer, primary_key=True, index=True)
    id_objeto = Column(Integer, ForeignKey("objeto_mapa.id_objeto"), nullable=False)
    filas = Column(Integer, nullable=False)
    columnas = Column(Integer, nullable=False)

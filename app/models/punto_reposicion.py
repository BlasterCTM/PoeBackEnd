from sqlalchemy import Column, Integer, ForeignKey
from app.core.database.database import Base

class PuntoReposicion(Base):
    __tablename__ = "punto_reposicion"
    id_punto = Column(Integer, primary_key=True, index=True)
    id_mueble = Column(Integer, ForeignKey("mueble_reposicion.id_mueble"), nullable=False)
    nivel = Column(Integer, nullable=False)
    estanteria = Column(Integer, nullable=False)
    id_producto = Column(Integer, ForeignKey("producto.id_producto"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)  # Nuevo campo para responsable

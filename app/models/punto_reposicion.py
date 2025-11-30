from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class PuntoReposicion(Base):
    __tablename__ = "punto_reposicion"
    id_punto = Column(Integer, primary_key=True, index=True)
    id_mueble = Column(Integer, ForeignKey("mueble_reposicion.id_mueble"), nullable=False)
    nivel = Column(Integer, nullable=False)
    estanteria = Column(Integer, nullable=False)
    id_producto = Column(Integer, ForeignKey("producto.id_producto"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)  # Usuario (reponedor) asignado
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)
    mueble = relationship("MuebleReposicion", back_populates="puntos")
    producto = relationship("Producto")
    usuario = relationship("Usuario")
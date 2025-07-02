from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class DetalleTarea(Base):
    __tablename__ = "detalle_tarea"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_tarea = Column(Integer, ForeignKey("tarea.id_tarea"), nullable=False)
    id_producto = Column(Integer, ForeignKey("producto.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    id_punto = Column(Integer, ForeignKey("punto_reposicion.id_punto"), nullable=False)
    estado_id = Column(Integer, ForeignKey("estado_tarea.estado_id"), nullable=True)

    # Relaciones
    tarea = relationship("Tarea", back_populates="detalles")
    punto = relationship("PuntoReposicion")

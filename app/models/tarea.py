from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database.database import Base

class Tarea(Base):
    __tablename__ = "tarea"
    id_tarea = Column(Integer, primary_key=True, index=True)
    fecha_creacion = Column(Date, nullable=False)
    estado_id = Column(Integer, ForeignKey("estado_tarea.estado_id"), nullable=False)
    id_supervisor = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_reponedor = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    fecha_hora_completada = Column(DateTime, nullable=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)

    # Relaciones
    detalles = relationship("DetalleTarea", back_populates="tarea")
    empresa = relationship("Empresa", back_populates="tareas")

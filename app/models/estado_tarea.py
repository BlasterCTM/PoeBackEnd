from sqlalchemy import Column, Integer, String
from app.core.database.database import Base

class EstadoTarea(Base):
    __tablename__ = "estado_tarea"
    estado_id = Column(Integer, primary_key=True, index=True)
    nombre_estado = Column(String(50), nullable=False)

from sqlalchemy import Column, Integer, String, Boolean
from app.core.database.database import Base

class ObjetoTipo(Base):
    __tablename__ = "objeto_tipo"
    id_tipo = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(50), nullable=False)
    caminable = Column(Boolean, nullable=True)
    destino = Column(Boolean, nullable=True)

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database.database import Base

class ObjetoMapa(Base):
    __tablename__ = "objeto_mapa"
    id_objeto = Column(Integer, primary_key=True, index=True)
    id_tipo = Column(Integer, ForeignKey("objeto_tipo.id_tipo"), nullable=False)
    nombre = Column(String(100), nullable=False)

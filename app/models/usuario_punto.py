from sqlalchemy import Column, Integer, ForeignKey
from app.core.database.database import Base

class UsuarioPunto(Base):
    __tablename__ = "usuario_punto"
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_punto = Column(Integer, ForeignKey("punto_reposicion.id_punto"), primary_key=True)

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database.database import Base

class Producto(Base):
    __tablename__ = "producto"
    id_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    unidad_tipo = Column(String(20), nullable=False)
    unidad_cantidad = Column(Integer, nullable=False)
    codigo_unico = Column(String(50), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)

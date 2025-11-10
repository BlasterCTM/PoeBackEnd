from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database.database import Base
from app.models.base import BaseModel

class RolEnum(str, enum.Enum):
    SUPERADMIN = "SuperAdmin"
    ADMINISTRADOR = "Administrador"
    SUPERVISOR = "Supervisor"
    REPONEDOR = "Reponedor"

class Rol(Base):
    __tablename__ = "rol"
    
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), nullable=False)
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = "usuario"
    
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), nullable=False, index=True)
    contraseña = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.id_rol"), nullable=False)
    estado = Column(String(20), default="activo")
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    empresa = relationship("Empresa", back_populates="usuarios")

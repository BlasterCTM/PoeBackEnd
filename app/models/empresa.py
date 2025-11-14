from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base

class Empresa(Base):
    """Modelo para la tabla empresa (Multi-tenant)"""
    __tablename__ = "empresa"
    
    id_empresa = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_empresa = Column(String(100), nullable=False)
    rut_empresa = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(255))
    ciudad = Column(String(100))
    region = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(255))
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(20), nullable=False, default="activo")
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    supervisiones = relationship("Supervision", back_populates="empresa", cascade="all, delete-orphan")
    mapas = relationship("Mapa", back_populates="empresa", cascade="all, delete-orphan")
    productos = relationship("Producto", back_populates="empresa", cascade="all, delete-orphan")
    tareas = relationship("Tarea", back_populates="empresa", cascade="all, delete-orphan")
    rutas = relationship("RutaOptimizada", back_populates="empresa", cascade="all, delete-orphan")
    conversaciones_chat = relationship("ChatConversacion", back_populates="empresa", cascade="all, delete-orphan")
    
    # Relaciones del módulo B2B
    plan = relationship("PlanEmpresa", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    facturas = relationship("Factura", back_populates="empresa", cascade="all, delete-orphan")
    actividades = relationship("ActividadCliente", back_populates="empresa", cascade="all, delete-orphan")

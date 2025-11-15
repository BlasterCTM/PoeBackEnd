"""
Modelo de Log de Auditoría para rastrear acciones del SuperAdmin
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class LogAuditoria(Base):
    """
    Registro de auditoría para todas las acciones administrativas
    
    Almacena:
    - Quién realizó la acción
    - Qué acción se realizó
    - Sobre qué entidad
    - Datos antes y después del cambio
    - IP de origen
    - Timestamp
    """
    __tablename__ = "log_auditoria"
    
    id_log = Column(Integer, primary_key=True, index=True)
    
    # Usuario que realizó la acción
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False, index=True)
    nombre_usuario = Column(String(255), nullable=False)  # Desnormalizado para histórico
    
    # Acción realizada
    accion = Column(String(100), nullable=False, index=True)
    # Ejemplos: "crear_plan", "modificar_empresa", "suspender_cliente", 
    #           "aprobar_cotizacion", "generar_factura", etc.
    
    # Entidad afectada
    entidad = Column(String(100), nullable=False, index=True)
    # Ejemplos: "plan_empresa", "empresa", "cotizacion", "factura", "usuario"
    
    id_entidad = Column(Integer, nullable=False, index=True)
    nombre_entidad = Column(String(255))  # Nombre descriptivo de la entidad
    
    # Datos del cambio
    datos_anteriores = Column(JSONB)  # Estado antes del cambio (null si es creación)
    datos_nuevos = Column(JSONB)      # Estado después del cambio
    
    # Metadatos de la acción
    ip_origen = Column(String(45))  # IPv4 o IPv6
    user_agent = Column(Text)       # Navegador/cliente
    
    # Timestamps
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[id_usuario], backref="logs_auditoria")
    
    def __repr__(self):
        return f"<LogAuditoria(id={self.id_log}, accion='{self.accion}', usuario='{self.nombre_usuario}', fecha='{self.fecha}')>"

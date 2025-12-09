from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base


class Cotizacion(Base):
    """
    Modelo para cotizacion - Solicitudes desde formulario "Cotiza Acá".
    Captura solicitudes de cotización y gestiona el flujo de conversión a cliente.
    """
    __tablename__ = "cotizacion"
    
    # Identificador
    id_cotizacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # ============================================
    # DATOS DE CONTACTO
    # ============================================
    nombre_contacto = Column(String(100), nullable=False)
    empresa = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    telefono = Column(String(20))
    cargo = Column(String(100))
    
    # ============================================
    # PARÁMETROS SOLICITADOS
    # ============================================
    cantidad_supervisores = Column(Integer, nullable=False)
    cantidad_reponedores = Column(Integer, nullable=False)
    
    # Parámetros opcionales
    cantidad_productos = Column(Integer)
    integraciones_requeridas = Column(Text)  # JSON array
    comentarios = Column(Text)
    
    # ============================================
    # COTIZACIÓN GENERADA
    # ============================================
    precio_sugerido = Column(Integer)  # CLP
    precio_final = Column(Integer)  # CLP (después de negociación)
    
    features_sugeridos = Column(JSONB)
    
    # ============================================
    # FLUJO DE APROBACIÓN
    # ============================================
    estado = Column(String(30), nullable=False, default="pendiente", index=True)
    # Estados: pendiente → en_revision → cotizada → negociacion → aprobada → rechazada → convertida
    
    notas_internas = Column(Text)
    
    # Validez de la cotización
    fecha_validez = Column(Date)
    
    # Conversión a cliente
    id_empresa_creada = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="SET NULL"), index=True)
    id_plan_creado = Column(Integer, ForeignKey("plan_empresa.id_plan", ondelete="SET NULL"))
    fecha_conversion = Column(Date)
    
    # Auditoría
    fecha_creacion = Column(Date, default=datetime.utcnow, index=True)
    fecha_actualizacion = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    atendido_por = Column(Integer, ForeignKey("usuario.id_usuario"))
    
    # ============================================
    # RELACIONES
    # ============================================
    empresa_creada_rel = relationship("Empresa", foreign_keys=[id_empresa_creada])
    plan_creado_rel = relationship("PlanEmpresa", foreign_keys=[id_plan_creado])
    usuario_atendio = relationship("Usuario", foreign_keys=[atendido_por])
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'en_revision', 'cotizada', 'negociacion', 'aprobada', 'rechazada', 'convertida')",
            name='cotizacion_estado_check'
        ),
    )

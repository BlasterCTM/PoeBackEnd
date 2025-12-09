from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base


class PlanEmpresa(Base):
    """
    Modelo para plan_empresa - Plan personalizado por empresa.
    Cada empresa tiene SU PROPIO plan con parámetros únicos y precio fijo mensual.
    """
    __tablename__ = "plan_empresa"
    
    # Identificador
    id_plan = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Relación 1:1 con empresa
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), 
                       nullable=False, unique=True, index=True)
    
    # ============================================
    # PARÁMETROS CONFIGURABLES
    # ============================================
    cantidad_supervisores = Column(Integer, nullable=False)
    cantidad_reponedores = Column(Integer, nullable=False)
    
    # Parámetros opcionales
    cantidad_productos = Column(Integer)
    cantidad_puntos = Column(Integer)
    
    # ============================================
    # PRICING - MONTO FIJO MENSUAL
    # ============================================
    precio_mensual = Column(Integer, nullable=False)  # CLP
    
    # ============================================
    # FEATURES HABILITADOS
    # ============================================
    features = Column(JSONB, nullable=False, default={
        "dashboard": True,
        "optimizacion_rutas": True,
        "reportes_pdf": True,
        "reportes_excel": False,
        "app_movil": False,
        "chat_supervisor": True,
        "historial_dias": 90
    })
    
    # Módulos habilitados/deshabilitados por el SuperAdmin
    # Permite activar/desactivar funcionalidades específicas por cliente
    modulos_habilitados = Column(JSONB, default={
        "optimizacion_rutas": True,
        "reportes_avanzados": True,
        "dashboard_ejecutivo": True,
        "app_movil": False,
        "chat_supervisor": True,
        "integraciones_api": False,
        "soporte_prioritario": False
    })
    
    # ============================================
    # FECHAS Y ESTADO
    # ============================================
    fecha_inicio = Column(Date, nullable=False, default=datetime.utcnow().date)
    fecha_vencimiento = Column(Date)  # NULL = sin vencimiento
    activo = Column(Boolean, nullable=False, default=True, index=True)
    
    # Notas internas
    notas = Column(Text)
    
    # Auditoría
    fecha_creacion = Column(Date, default=datetime.utcnow)
    fecha_actualizacion = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuario.id_usuario"))
    
    # ============================================
    # RELACIONES
    # ============================================
    empresa = relationship("Empresa", back_populates="plan")
    facturas = relationship("Factura", back_populates="plan", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'cantidad_supervisores > 0 AND cantidad_reponedores > 0 AND precio_mensual > 0',
            name='plan_empresa_cantidad_check'
        ),
    )

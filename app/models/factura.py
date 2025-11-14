from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base


class Factura(Base):
    """
    Modelo para factura - Facturación mensual a empresas.
    Gestiona la emisión de facturas y el control de pagos.
    """
    __tablename__ = "factura"
    
    # Identificador
    id_factura = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Relaciones
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), 
                       nullable=False, index=True)
    id_plan = Column(Integer, ForeignKey("plan_empresa.id_plan"), nullable=False)
    
    # ============================================
    # DATOS DE FACTURA
    # ============================================
    numero_factura = Column(String(50), unique=True, index=True)
    fecha_emision = Column(Date, nullable=False, default=datetime.utcnow().date, index=True)
    fecha_vencimiento = Column(Date, nullable=False)
    
    # ============================================
    # MONTOS (CLP)
    # ============================================
    subtotal = Column(Integer, nullable=False)
    iva = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    
    # Detalle
    descripcion = Column(Text)
    periodo_facturado = Column(String(50), index=True)  # "Enero 2025", "01/2025"
    
    # ============================================
    # ESTADO DE PAGO
    # ============================================
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    # Estados: pendiente → pagada → vencida → anulada
    
    fecha_pago = Column(Date)
    metodo_pago = Column(String(50))
    referencia_pago = Column(String(100))
    
    # Archivo PDF
    archivo_pdf_url = Column(Text)
    
    # Auditoría
    fecha_creacion = Column(Date, default=datetime.utcnow)
    fecha_actualizacion = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    emitida_por = Column(Integer, ForeignKey("usuario.id_usuario"))
    
    # ============================================
    # RELACIONES
    # ============================================
    empresa = relationship("Empresa", back_populates="facturas")
    plan = relationship("PlanEmpresa", back_populates="facturas")
    usuario_emitio = relationship("Usuario", foreign_keys=[emitida_por])
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'pagada', 'vencida', 'anulada')",
            name='factura_estado_check'
        ),
        CheckConstraint(
            'subtotal > 0 AND iva >= 0 AND total > 0',
            name='factura_montos_check'
        ),
    )

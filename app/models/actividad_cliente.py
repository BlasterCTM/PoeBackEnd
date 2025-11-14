from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base


class ActividadCliente(Base):
    """
    Modelo para actividad_cliente - Registro de soporte y seguimiento.
    Almacena todas las interacciones con clientes: capacitaciones, soporte, incidencias, etc.
    """
    __tablename__ = "actividad_cliente"
    
    # Identificador
    id_actividad = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Relación con empresa
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), 
                       nullable=False, index=True)
    
    # ============================================
    # TIPO DE ACTIVIDAD
    # ============================================
    tipo = Column(String(30), nullable=False, index=True)
    # Tipos: capacitacion, soporte, incidencia, reunion, upgrade, otro
    
    # ============================================
    # DETALLES
    # ============================================
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    
    # Usuario del equipo POE responsable
    id_usuario_responsable = Column(Integer, ForeignKey("usuario.id_usuario"), index=True)
    
    # Archivos adjuntos (URLs)
    archivos = Column(JSONB)  # ["url1", "url2"]
    
    # ============================================
    # ESTADO Y FECHAS
    # ============================================
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    # Estados: pendiente → en_progreso → completada → cancelada
    
    fecha_programada = Column(Date)
    fecha_completada = Column(Date)
    
    # Auditoría
    fecha_creacion = Column(Date, default=datetime.utcnow, index=True)
    fecha_actualizacion = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================
    # RELACIONES
    # ============================================
    empresa = relationship("Empresa", back_populates="actividades")
    usuario_responsable = relationship("Usuario", foreign_keys=[id_usuario_responsable])
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('capacitacion', 'soporte', 'incidencia', 'reunion', 'upgrade', 'otro')",
            name='actividad_tipo_check'
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'en_progreso', 'completada', 'cancelada')",
            name='actividad_estado_check'
        ),
    )

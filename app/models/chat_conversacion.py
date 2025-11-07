from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base

class ChatConversacion(Base):
    """Modelo para la tabla chat_conversacion (Sala de chat entre supervisor y reponedor)"""
    __tablename__ = "chat_conversacion"
    
    id_conversacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False)
    id_supervisor = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    id_reponedor = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="conversaciones_chat")
    supervisor = relationship("Usuario", foreign_keys=[id_supervisor])
    reponedor = relationship("Usuario", foreign_keys=[id_reponedor])
    mensajes = relationship("ChatMensaje", back_populates="conversacion", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('id_empresa', 'id_supervisor', 'id_reponedor', name='uq_chat_empresa_supervisor_reponedor'),
    )

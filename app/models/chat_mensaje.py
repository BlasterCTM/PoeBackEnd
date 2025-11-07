from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base

class ChatMensaje(Base):
    """Modelo para la tabla chat_mensaje (Mensajes individuales de una conversación)"""
    __tablename__ = "chat_mensaje"
    
    id_mensaje = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_conversacion = Column(Integer, ForeignKey("chat_conversacion.id_conversacion", ondelete="CASCADE"), nullable=False)
    id_emisor = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="SET NULL"), nullable=False)
    contenido = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    leido = Column(Boolean, default=False)
    
    # Relaciones
    conversacion = relationship("ChatConversacion", back_populates="mensajes")
    emisor = relationship("Usuario")

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database.database import Base
from app.models.usuario import Usuario
from datetime import datetime

class Supervision(Base):
    __tablename__ = "supervision"
    
    id_supervision = Column(Integer, primary_key=True, index=True)
    supervisor_id = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    reponedor_id = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    supervisor = relationship(
        Usuario,
        foreign_keys=[supervisor_id],
        backref="supervisiones_asignadas",
        primaryjoin="and_(Supervision.supervisor_id==Usuario.id_usuario)"
    )
    reponedor = relationship(
        Usuario,
        foreign_keys=[reponedor_id],
        backref="supervision_recibida",
        primaryjoin="and_(Supervision.reponedor_id==Usuario.id_usuario)"
    )

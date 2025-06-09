from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from app.core.database.database import Base

class BaseModel(Base):
    """Clase base para todos los modelos"""
    __abstract__ = True
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

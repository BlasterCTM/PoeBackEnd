"""
Schemas para Log de Auditoría
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class LogAuditoriaBase(BaseModel):
    """Schema base para log de auditoría"""
    accion: str = Field(..., description="Acción realizada")
    entidad: str = Field(..., description="Tipo de entidad afectada")
    id_entidad: int = Field(..., description="ID de la entidad afectada")
    nombre_entidad: Optional[str] = Field(None, description="Nombre descriptivo de la entidad")


class LogAuditoriaCreate(LogAuditoriaBase):
    """Schema para crear un log de auditoría"""
    id_usuario: int
    nombre_usuario: str
    datos_anteriores: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None


class LogAuditoriaResponse(LogAuditoriaBase):
    """Schema de respuesta para log de auditoría"""
    id_log: int
    id_usuario: int
    nombre_usuario: str
    usuario_rol: Optional[str] = None
    datos_anteriores: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None
    fecha: datetime
    
    class Config:
        from_attributes = True


class LogAuditoriaFiltros(BaseModel):
    """Filtros para búsqueda de logs"""
    id_usuario: Optional[int] = None
    accion: Optional[str] = None
    entidad: Optional[str] = None
    id_entidad: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=1000)


class EstadisticasAuditoria(BaseModel):
    """Estadísticas de auditoría"""
    total_logs: int
    acciones_por_tipo: Dict[str, int]
    usuarios_mas_activos: list[Dict[str, Any]]
    entidades_mas_modificadas: list[Dict[str, Any]]
    logs_ultimas_24h: int
    logs_ultima_semana: int

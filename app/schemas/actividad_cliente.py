from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============================================
# ENUMS
# ============================================

class TipoActividad(str, Enum):
    """Tipos de actividad"""
    CAPACITACION = "capacitacion"
    SOPORTE = "soporte"
    INCIDENCIA = "incidencia"
    REUNION = "reunion"
    UPGRADE = "upgrade"
    OTRO = "otro"


class EstadoActividad(str, Enum):
    """Estados de actividad"""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


# ============================================
# SCHEMAS BASE
# ============================================

class ActividadClienteBase(BaseModel):
    """Schema base para actividad de cliente"""
    tipo: TipoActividad = Field(..., description="Tipo de actividad")
    titulo: str = Field(..., min_length=1, max_length=200, description="Título de la actividad")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    
    id_usuario_responsable: Optional[int] = Field(None, description="ID del usuario responsable")
    
    archivos: Optional[List[str]] = Field(None, description="URLs de archivos adjuntos")
    
    estado: Optional[EstadoActividad] = Field(EstadoActividad.PENDIENTE, description="Estado de la actividad")
    fecha_programada: Optional[date] = Field(None, description="Fecha programada")


class ActividadClienteCreate(ActividadClienteBase):
    """Schema para crear actividad"""
    id_empresa: int = Field(..., description="ID de la empresa")


class ActividadClienteUpdate(BaseModel):
    """Schema para actualizar actividad"""
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    id_usuario_responsable: Optional[int] = None
    archivos: Optional[List[str]] = None
    estado: Optional[EstadoActividad] = None
    fecha_programada: Optional[date] = None
    fecha_completada: Optional[date] = None


class ActividadClienteResponse(ActividadClienteBase):
    """Schema de respuesta de actividad"""
    id_actividad: int
    id_empresa: int
    
    fecha_completada: Optional[datetime]
    
    # Auditoría
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True


class ActividadClienteListItem(BaseModel):
    """Schema resumido para listar actividades"""
    id_actividad: int
    tipo: str
    titulo: str
    estado: str
    fecha_programada: Optional[datetime]
    fecha_creacion: datetime
    
    # Datos opcionales
    nombre_empresa: Optional[str] = None
    nombre_responsable: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS DE ESTADÍSTICAS
# ============================================

class ActividadStats(BaseModel):
    """Estadísticas de actividades"""
    total: int
    pendientes: int
    en_progreso: int
    completadas: int
    canceladas: int
    
    por_tipo: dict  # {"capacitacion": 10, "soporte": 5, ...}
    
    proximas_7_dias: int
    vencidas: int

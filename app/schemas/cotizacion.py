from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class EstadoCotizacion(str, Enum):
    """Estados posibles de una cotización"""
    PENDIENTE = "pendiente"
    EN_REVISION = "en_revision"
    COTIZADA = "cotizada"
    NEGOCIACION = "negociacion"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CONVERTIDA = "convertida"


# ============================================
# SCHEMAS BASE
# ============================================

class CotizacionBase(BaseModel):
    """Schema base para cotización"""
    # Datos de contacto
    nombre_contacto: str = Field(..., min_length=1, max_length=100, 
                                 description="Nombre del contacto")
    empresa: str = Field(..., min_length=1, max_length=100, 
                        description="Nombre de la empresa")
    email: EmailStr = Field(..., description="Email del contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo del contacto")
    
    # Parámetros solicitados
    cantidad_supervisores: int = Field(..., gt=0, description="Cantidad de supervisores")
    cantidad_reponedores: int = Field(..., gt=0, description="Cantidad de reponedores")
    
    # Parámetros opcionales
    cantidad_productos: Optional[int] = Field(None, gt=0, description="Cantidad de productos")
    integraciones_requeridas: Optional[str] = Field(None, description="Integraciones requeridas (JSON array)")
    comentarios: Optional[str] = Field(None, description="Comentarios adicionales")


class CotizacionCreate(CotizacionBase):
    """Schema para crear cotización (desde formulario web)"""
    pass


class CotizacionUpdate(BaseModel):
    """Schema para actualizar cotización (admin POE)"""
    # Datos de contacto (editables)
    nombre_contacto: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre del contacto")
    empresa: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre de la empresa")
    email: Optional[EmailStr] = Field(None, description="Email del contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo del contacto")
    
    # Parámetros que influyen en el precio (editables)
    cantidad_supervisores: Optional[int] = Field(None, gt=0, description="Cantidad de supervisores")
    cantidad_reponedores: Optional[int] = Field(None, gt=0, description="Cantidad de reponedores")
    cantidad_productos: Optional[int] = Field(None, gt=0, description="Cantidad de productos")
    integraciones_requeridas: Optional[str] = Field(None, description="Integraciones requeridas")
    comentarios: Optional[str] = Field(None, description="Comentarios adicionales")
    
    # Cotización generada
    precio_sugerido: Optional[int] = Field(None, gt=0, description="Precio sugerido en CLP")
    precio_final: Optional[int] = Field(None, gt=0, description="Precio final acordado en CLP")
    features_sugeridos: Optional[dict] = Field(None, description="Features sugeridos")
    
    # Estado
    estado: Optional[EstadoCotizacion] = Field(None, description="Estado de la cotización")
    notas_internas: Optional[str] = Field(None, description="Notas internas del equipo POE")
    fecha_validez: Optional[date] = Field(None, description="Fecha de validez de la cotización")


class CotizacionResponse(CotizacionBase):
    """Schema de respuesta de cotización"""
    id_cotizacion: int
    
    # Cotización generada
    precio_sugerido: Optional[int]
    precio_final: Optional[int]
    features_sugeridos: Optional[dict]
    
    # Estado
    estado: str
    notas_internas: Optional[str]
    fecha_validez: Optional[date]
    
    # Conversión
    id_empresa_creada: Optional[int]
    id_plan_creado: Optional[int]
    fecha_conversion: Optional[datetime]
    
    # Auditoría
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    atendido_por: Optional[int]
    
    class Config:
        from_attributes = True


class CotizacionListItem(BaseModel):
    """Schema resumido para listar cotizaciones"""
    id_cotizacion: int
    nombre_contacto: str
    empresa: str
    email: str
    cantidad_supervisores: int
    cantidad_reponedores: int
    precio_final: Optional[int]
    estado: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS DE CONVERSIÓN
# ============================================

class CotizacionConvertir(BaseModel):
    """Schema para convertir cotización en empresa + plan"""
    # Datos de la empresa a crear
    nombre_empresa: str = Field(..., min_length=1, max_length=100)
    rut_empresa: str = Field(..., min_length=1, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    
    # Datos del admin a crear
    admin_nombre: str = Field(..., min_length=1, max_length=100)
    admin_correo: EmailStr
    admin_contraseña: str = Field(..., min_length=8)
    
    # Parámetros del plan (pueden diferir de la cotización)
    cantidad_supervisores: int = Field(..., gt=0)
    cantidad_reponedores: int = Field(..., gt=0)
    cantidad_productos: Optional[int] = Field(None, gt=0)
    cantidad_puntos: Optional[int] = Field(None, gt=0)
    
    # Precio final
    precio_mensual: int = Field(..., gt=0, description="Precio mensual acordado en CLP")
    
    # Features
    features: dict = Field(default_factory=dict, description="Features habilitados")
    
    # Fechas
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio del plan")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento (NULL = sin vencimiento)")


class CotizacionConvertidaResponse(BaseModel):
    """Schema de respuesta al convertir cotización"""
    mensaje: str
    id_cotizacion: int
    id_empresa: int
    id_plan: int
    id_usuario_admin: int
    
    empresa: dict
    plan: dict
    admin: dict


# ============================================
# SCHEMAS DE ESTADÍSTICAS
# ============================================

class CotizacionStats(BaseModel):
    """Estadísticas de cotizaciones"""
    total: int
    pendientes: int
    en_revision: int
    cotizadas: int
    aprobadas: int
    rechazadas: int
    convertidas: int
    
    monto_total_cotizado: int  # CLP
    monto_total_convertido: int  # CLP
    tasa_conversion: float  # %

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime


# ============================================
# SCHEMAS BASE
# ============================================

class PlanEmpresaBase(BaseModel):
    """Schema base para plan de empresa"""
    # Parámetros configurables
    cantidad_locales: int = Field(..., gt=0, description="Cantidad de locales")
    cantidad_supervisores: int = Field(..., gt=0, description="Cantidad de supervisores")
    cantidad_reponedores: int = Field(..., gt=0, description="Cantidad de reponedores")
    cantidad_productos: Optional[int] = Field(None, gt=0, description="Cantidad de productos")
    cantidad_puntos: Optional[int] = Field(None, gt=0, description="Cantidad de puntos de reposición")
    
    # Pricing
    precio_mensual: int = Field(..., gt=0, description="Precio mensual en CLP")
    
    # Features y módulos
    features: dict = Field(default_factory=dict, description="Funcionalidades habilitadas")
    modulos_habilitados: Optional[dict] = Field(None, description="Módulos específicos habilitados por el SuperAdmin")
    
    # Fechas
    fecha_inicio: Optional[date] = Field(None, description="Fecha de inicio del plan")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento (NULL = sin vencimiento)")
    
    # Notas
    notas: Optional[str] = Field(None, description="Notas internas sobre el plan")


class PlanEmpresaCreate(PlanEmpresaBase):
    """Schema para crear plan de empresa"""
    id_empresa: int = Field(..., description="ID de la empresa")


class PlanEmpresaUpdate(BaseModel):
    """Schema para actualizar plan de empresa"""
    cantidad_locales: Optional[int] = Field(None, gt=0)
    cantidad_supervisores: Optional[int] = Field(None, gt=0)
    cantidad_reponedores: Optional[int] = Field(None, gt=0)
    cantidad_productos: Optional[int] = Field(None, gt=0)
    cantidad_puntos: Optional[int] = Field(None, gt=0)
    
    precio_mensual: Optional[int] = Field(None, gt=0)
    features: Optional[dict] = None
    modulos_habilitados: Optional[dict] = Field(None, description="Módulos específicos habilitados")
    
    fecha_vencimiento: Optional[date] = None
    activo: Optional[bool] = None
    notas: Optional[str] = None


class PlanEmpresaResponse(PlanEmpresaBase):
    """Schema de respuesta de plan de empresa"""
    id_plan: int
    id_empresa: int
    activo: bool
    
    # Auditoría
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    creado_por: Optional[int]
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS DE VALIDACIÓN
# ============================================

class ValidacionLimite(BaseModel):
    """Schema para validar límites de un plan"""
    recurso: str = Field(..., description="Tipo de recurso (usuarios, productos, etc.)")
    cantidad_actual: int
    limite_plan: int
    disponible: int
    porcentaje_uso: float
    excedido: bool


class PlanEmpresaConLimites(PlanEmpresaResponse):
    """Schema de plan con información de uso de límites"""
    uso_locales: Optional[int] = Field(None, description="Cantidad actual de locales")
    uso_supervisores: Optional[int] = Field(None, description="Cantidad actual de supervisores")
    uso_reponedores: Optional[int] = Field(None, description="Cantidad actual de reponedores")
    uso_productos: Optional[int] = Field(None, description="Cantidad actual de productos")
    uso_puntos: Optional[int] = Field(None, description="Cantidad actual de puntos")
    
    # Validaciones
    validaciones: Optional[dict] = Field(None, description="Estado de validación de límites")


# ============================================
# SCHEMAS DE UPGRADE/DOWNGRADE
# ============================================

class PlanEmpresaUpgrade(BaseModel):
    """Schema para upgrade de plan"""
    nueva_cantidad_locales: Optional[int] = Field(None, gt=0)
    nueva_cantidad_supervisores: Optional[int] = Field(None, gt=0)
    nueva_cantidad_reponedores: Optional[int] = Field(None, gt=0)
    
    nuevo_precio_mensual: int = Field(..., gt=0, description="Nuevo precio mensual")
    
    motivo: str = Field(..., description="Motivo del upgrade")
    fecha_efectiva: Optional[date] = Field(None, description="Fecha efectiva del cambio")

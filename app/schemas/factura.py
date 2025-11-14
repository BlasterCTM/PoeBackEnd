from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class EstadoFactura(str, Enum):
    """Estados posibles de una factura"""
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    VENCIDA = "vencida"
    ANULADA = "anulada"


# ============================================
# SCHEMAS BASE
# ============================================

class FacturaBase(BaseModel):
    """Schema base para factura"""
    # Datos de factura
    numero_factura: Optional[str] = Field(None, max_length=50, description="Número de factura")
    fecha_emision: date = Field(..., description="Fecha de emisión")
    fecha_vencimiento: date = Field(..., description="Fecha de vencimiento")
    
    # Montos
    subtotal: int = Field(..., gt=0, description="Subtotal en CLP")
    iva: int = Field(..., ge=0, description="IVA en CLP")
    total: int = Field(..., gt=0, description="Total en CLP")
    
    # Detalle
    descripcion: Optional[str] = Field(None, description="Descripción de la factura")
    periodo_facturado: Optional[str] = Field(None, max_length=50, description="Periodo facturado")


class FacturaCreate(FacturaBase):
    """Schema para crear factura"""
    id_empresa: int = Field(..., description="ID de la empresa")
    id_plan: int = Field(..., description="ID del plan")


class FacturaUpdate(BaseModel):
    """Schema para actualizar factura"""
    estado: Optional[EstadoFactura] = Field(None, description="Estado de la factura")
    fecha_pago: Optional[date] = Field(None, description="Fecha de pago")
    metodo_pago: Optional[str] = Field(None, max_length=50, description="Método de pago")
    referencia_pago: Optional[str] = Field(None, max_length=100, description="Referencia de pago")
    archivo_pdf_url: Optional[str] = Field(None, description="URL del archivo PDF")


class FacturaResponse(FacturaBase):
    """Schema de respuesta de factura"""
    id_factura: int
    id_empresa: int
    id_plan: int
    
    # Estado de pago
    estado: str
    fecha_pago: Optional[date]
    metodo_pago: Optional[str]
    referencia_pago: Optional[str]
    
    # Archivo
    archivo_pdf_url: Optional[str]
    
    # Auditoría
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    emitida_por: Optional[int]
    
    class Config:
        from_attributes = True


class FacturaListItem(BaseModel):
    """Schema resumido para listar facturas"""
    id_factura: int
    numero_factura: Optional[str]
    fecha_emision: date
    fecha_vencimiento: date
    total: int
    estado: str
    periodo_facturado: Optional[str]
    
    # Datos de empresa (opcional)
    nombre_empresa: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS DE PAGO
# ============================================

class FacturaRegistrarPago(BaseModel):
    """Schema para registrar pago de factura"""
    fecha_pago: date = Field(..., description="Fecha del pago")
    metodo_pago: str = Field(..., max_length=50, description="Método de pago")
    referencia_pago: str = Field(..., max_length=100, description="Referencia del pago")


# ============================================
# SCHEMAS DE GENERACIÓN
# ============================================

class FacturaGenerar(BaseModel):
    """Schema para generar factura automática"""
    id_empresa: int = Field(..., description="ID de la empresa")
    periodo_facturado: str = Field(..., max_length=50, description="Periodo a facturar (Ej: Enero 2025)")
    fecha_vencimiento: date = Field(..., description="Fecha de vencimiento")
    descripcion: Optional[str] = Field(None, description="Descripción personalizada")


# ============================================
# SCHEMAS DE ESTADÍSTICAS
# ============================================

class FacturaStats(BaseModel):
    """Estadísticas de facturación"""
    total_facturas: int
    facturas_pendientes: int
    facturas_pagadas: int
    facturas_vencidas: int
    facturas_anuladas: int
    
    monto_total_facturado: int  # CLP
    monto_total_cobrado: int  # CLP
    monto_pendiente: int  # CLP
    monto_vencido: int  # CLP
    
    tasa_cobranza: float  # %

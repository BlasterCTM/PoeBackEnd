"""
Schemas seguros para Backoffice - SIN datos sensibles del cliente
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any


# ============================================================
# SCHEMAS DE EMPRESA PARA BACKOFFICE
# ============================================================

class EmpresaBackoffice(BaseModel):
    """
    Schema seguro de Empresa para backoffice
    
    PERMITIDO:
    - Nombre empresa
    - RUT empresa
    - Estado de suscripción
    - Contacto comercial
    
    PROHIBIDO (NO incluido):
    - Datos de empleados individuales
    - Datos de productos
    - Datos de logística/rutas
    - Información sensible operativa
    """
    id_empresa: int
    nombre_empresa: str
    rut_empresa: str
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    region: Optional[str] = None
    estado: str  # activo, inactivo, suspendido, prueba
    email: Optional[str] = None  # Email de contacto comercial
    telefono: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    
    # Info de suscripción
    tiene_plan_activo: bool = False
    nombre_plan: Optional[str] = None
    estado_plan: Optional[str] = None
    fecha_vencimiento_plan: Optional[date] = None
    
    class Config:
        from_attributes = True


# ============================================================
# SCHEMAS DE USUARIO PARA BACKOFFICE
# ============================================================

class UsuarioBackoffice(BaseModel):
    """
    Schema seguro de Usuario para backoffice
    
    PERMITIDO:
    - Nombre
    - Email
    - Rol
    - Estado
    
    PROHIBIDO (NO incluido):
    - Contraseña (obviamente)
    - RUT/DNI personal
    - Teléfono personal
    - Dirección personal
    - Datos laborales (salario, turno, etc.)
    """
    id_usuario: int
    nombre: str
    correo: str
    rol: str
    estado: str
    id_empresa: int
    nombre_empresa: str
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================
# SCHEMAS DE PLAN PARA BACKOFFICE
# ============================================================

class PlanEmpresaBackoffice(BaseModel):
    """Schema de Plan para backoffice con información de suscripción"""
    id_plan: int
    id_empresa: int
    nombre_empresa: str
    
    # Límites del plan
    cantidad_supervisores: int
    cantidad_reponedores: int
    cantidad_puntos_reposicion: int
    cantidad_productos: int
    
    # Pricing
    precio_mensual: int
    
    # Features habilitados
    modulos_habilitados: Optional[Dict[str, bool]] = None
    features: Dict[str, Any]
    
    # Estado
    activo: bool
    fecha_inicio: date
    fecha_vencimiento: Optional[date] = None
    
    class Config:
        from_attributes = True


# ============================================================
# MÉTRICAS AGREGADAS DEL SISTEMA
# ============================================================

class MetricasSistema(BaseModel):
    """Métricas agregadas del sistema - solo números, sin datos sensibles"""
    
    # Empresas
    total_empresas: int
    empresas_activas: int
    empresas_inactivas: int
    empresas_suspendidas: int
    empresas_en_prueba: int
    
    # Usuarios
    total_usuarios: int
    usuarios_activos: int
    usuarios_por_rol: Dict[str, int]
    
    # Suscripciones
    planes_activos: int
    planes_vencidos: int
    planes_por_vencer_30d: int
    
    # Facturación
    facturas_pendientes: int
    facturas_pagadas_mes: int
    ingresos_mes_actual: int
    ingresos_mes_anterior: int
    
    # Actividad
    cotizaciones_pendientes: int
    cotizaciones_aprobadas: int
    cotizaciones_rechazadas: int
    
    # Soporte
    actividades_pendientes: int
    actividades_completadas_mes: int


class ResumenEmpresa(BaseModel):
    """Resumen de una empresa específica para el dashboard"""
    id_empresa: int
    nombre_empresa: str
    rut_empresa: str
    estado: str
    
    # Suscripción
    tiene_plan: bool
    plan_activo: bool
    precio_mensual: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    
    # Uso actual (sin detalles sensibles)
    total_usuarios: int
    usuarios_activos: int
    
    # Facturación
    ultima_factura_pagada: Optional[date] = None
    facturas_pendientes: int
    
    # Actividades
    actividades_pendientes: int
    ultima_actividad: Optional[datetime] = None


class ConsumoRecursos(BaseModel):
    """Consumo de recursos de una empresa vs su plan"""
    id_empresa: int
    nombre_empresa: str
    
    # Límites del plan vs uso actual
    supervisores_limite: int
    supervisores_uso: int
    supervisores_disponibles: int
    
    reponedores_limite: int
    reponedores_uso: int
    reponedores_disponibles: int
    
    # Otros recursos (sin datos sensibles)
    total_usuarios: int
    almacenamiento_usado_mb: Optional[int] = None
    api_calls_mes: Optional[int] = None

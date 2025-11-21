from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EstadoPrediccion(str, Enum):
    """Estados posibles de una predicción"""
    PENDIENTE = "pendiente"
    APLICADO = "aplicado"
    RECHAZADO = "rechazado"


# ============================================
# SCHEMAS DE REQUEST
# ============================================

class PrediccionRequest(BaseModel):
    """Request para generar predicción de reposición"""
    mes: int = Field(..., ge=1, le=12, description="Mes a predecir (1-12)")
    anio: int = Field(..., ge=2024, le=2030, description="Año a predecir")
    incluir_semanas: bool = Field(default=True, description="Generar predicciones por semana")
    notas: Optional[str] = Field(None, max_length=500, description="Notas adicionales")
    
    @validator('anio')
    def validar_anio_futuro(cls, v):
        if v < datetime.now().year:
            raise ValueError(f"El año debe ser {datetime.now().year} o posterior")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mes": 12,
                "anio": 2025,
                "incluir_semanas": True,
                "notas": "Predicción para temporada navideña"
            }
        }


# ============================================
# SCHEMAS DE RESPONSE
# ============================================

class CategoriaPrediction(BaseModel):
    """Predicción para una categoría específica"""
    categoria: str
    ubicacion_mueble: int
    reposiciones: int = Field(..., description="Número de reposiciones predichas")
    total_unidades: int = Field(..., description="Unidades totales a reponer")
    dias_predichos: List[int] = Field(default_factory=list, description="Días del mes con reposición")


class SemanaPrediction(BaseModel):
    """Predicción agregada por semana"""
    semana: int = Field(..., ge=1, le=5)
    fecha_inicio: str
    fecha_fin: str
    total_unidades: int
    categorias: Dict[str, int] = Field(default_factory=dict, description="Unidades por categoría")


class ResumenPrediccion(BaseModel):
    """Resumen ejecutivo de la predicción"""
    total_reposiciones: int = Field(..., description="Total de eventos de reposición")
    total_unidades: int = Field(..., description="Unidades totales a reponer en el mes")
    categorias_activas: List[str] = Field(default_factory=list)
    promedio_diario: float = Field(..., description="Promedio de unidades por día")


class PrediccionResponse(BaseModel):
    """Response completo de una predicción generada"""
    id_prediccion: int
    id_empresa: int
    mes: int
    anio: int
    version_modelo: str
    fecha_generacion: datetime
    estado: EstadoPrediccion
    
    # Resultados
    resumen: ResumenPrediccion
    por_categoria: List[CategoriaPrediction]
    por_semana: Optional[List[SemanaPrediction]] = None
    
    # Metadata
    features_utilizados: Optional[Dict[str, Any]] = None
    notas: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_prediccion": 42,
                "id_empresa": 1,
                "mes": 12,
                "anio": 2025,
                "version_modelo": "1.0.0",
                "fecha_generacion": "2025-11-21T10:30:00",
                "estado": "pendiente",
                "resumen": {
                    "total_reposiciones": 145,
                    "total_unidades": 3850,
                    "categorias_activas": ["Lacteos", "Panaderia", "Frutas_Verduras"],
                    "promedio_diario": 124.2
                },
                "por_categoria": [
                    {
                        "categoria": "Lacteos",
                        "ubicacion_mueble": 118,
                        "reposiciones": 25,
                        "total_unidades": 780,
                        "dias_predichos": [1, 3, 5, 8, 10]
                    }
                ],
                "por_semana": [
                    {
                        "semana": 1,
                        "fecha_inicio": "2025-12-01",
                        "fecha_fin": "2025-12-07",
                        "total_unidades": 850,
                        "categorias": {"Lacteos": 200, "Panaderia": 450}
                    }
                ]
            }
        }


class PrediccionHistorialItem(BaseModel):
    """Item del historial de predicciones (versión resumida)"""
    id_prediccion: int
    mes: int
    anio: int
    fecha_generacion: datetime
    estado: EstadoPrediccion
    total_unidades: int
    total_reposiciones: int
    version_modelo: str
    
    class Config:
        from_attributes = True


class PrediccionHistorialResponse(BaseModel):
    """Response con historial de predicciones"""
    total: int
    predicciones: List[PrediccionHistorialItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "predicciones": [
                    {
                        "id_prediccion": 42,
                        "mes": 12,
                        "anio": 2025,
                        "fecha_generacion": "2025-11-21T10:30:00",
                        "estado": "pendiente",
                        "total_unidades": 3850,
                        "total_reposiciones": 145,
                        "version_modelo": "1.0.0"
                    }
                ]
            }
        }


class ActualizarEstadoRequest(BaseModel):
    """Request para actualizar estado de predicción"""
    estado: EstadoPrediccion
    notas: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "estado": "aplicado",
                "notas": "Aplicado en sistema de reposición automático"
            }
        }


# ============================================
# SCHEMAS INTERNOS (para transformaciones)
# ============================================

class PrediccionDetalle(BaseModel):
    """Schema interno con detalles completos de predicción"""
    categoria: str
    ubicacion_mueble: int
    hora: int
    dia_semana: int
    mes: int
    semana_mes: int
    dia_del_mes: int
    reposicion_predicha: int  # 0 o 1
    cantidad_predicha: Optional[int] = None  # Solo si reposicion_predicha=1
    
    class Config:
        from_attributes = True

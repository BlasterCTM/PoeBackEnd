from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# Esquemas para PasoRuta
class PasoRutaBase(BaseModel):
    secuencia: int
    x: int
    y: int

class PasoRutaCreate(PasoRutaBase):
    id_detalle_ruta: int

class PasoRutaResponse(PasoRutaBase):
    id_paso: int
    id_detalle_ruta: int

    class Config:
        from_attributes = True

# Esquemas para DetalleRuta
class DetalleRutaBase(BaseModel):
    orden: int
    id_punto: int
    tiempo_estimado_punto: Optional[float] = None

class DetalleRutaCreate(DetalleRutaBase):
    id_ruta: int

class DetalleRutaResponse(DetalleRutaBase):
    id_detalle_ruta: int
    id_ruta: int
    pasos: List[PasoRutaResponse] = []

    class Config:
        from_attributes = True

# Esquemas para RutaOptimizada
class RutaOptimizadaBase(BaseModel):
    algoritmo_usado: Optional[str] = None
    tiempo_estimado: Optional[float] = None
    distancia_total: Optional[float] = None

class RutaOptimizadaCreate(RutaOptimizadaBase):
    id_reponedor: int
    id_tarea: int
    fecha_generada: date

class RutaOptimizadaResponse(RutaOptimizadaBase):
    id_ruta: int
    id_reponedor: int
    id_tarea: int
    fecha_generada: date
    detalles: List[DetalleRutaResponse] = []

    class Config:
        from_attributes = True

# Esquemas para MetricaOptimizacion
class MetricaOptimizacionBase(BaseModel):
    tiempo_real: Optional[float] = None
    desviaciones: Optional[int] = None
    eficiencia: Optional[float] = None

class MetricaOptimizacionCreate(MetricaOptimizacionBase):
    id_ruta: int

class MetricaOptimizacionResponse(MetricaOptimizacionBase):
    id_metrica: int
    id_ruta: int

    class Config:
        from_attributes = True

# Esquema completo para rutas con todos los detalles
class RutaCompletaResponse(BaseModel):
    ruta: RutaOptimizadaResponse
    metricas: Optional[MetricaOptimizacionResponse] = None
    
    class Config:
        from_attributes = True

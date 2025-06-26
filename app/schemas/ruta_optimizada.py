# Esquemas para rutas optimizadas de reposición
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class CoordenadaResponse(BaseModel):
    """Coordenadas en el mapa"""
    x: int
    y: int

class MuebleRutaResponse(BaseModel):
    """Información del mueble en la ruta"""
    id_mueble: int
    nombre_objeto: str
    coordenadas: CoordenadaResponse
    nivel: int
    estanteria: int

class ProductoRutaResponse(BaseModel):
    """Información del producto en la ruta"""
    id_producto: int
    nombre: str
    categoria: str
    cantidad: int

class PuntoRutaResponse(BaseModel):
    """Punto de reposición en la ruta optimizada"""
    id_punto: int
    mueble: MuebleRutaResponse
    producto: ProductoRutaResponse
    orden_visita: int

class AlgoritmoResponse(BaseModel):
    """Información del algoritmo utilizado"""
    nombre: str = "A* (A-Star)"
    descripcion: str = "Algoritmo de búsqueda de camino más corto"

class RutaOptimizadaResponse(BaseModel):
    """Respuesta completa de la ruta optimizada"""
    id_tarea: int
    reponedor: str
    fecha_creacion: str
    puntos_reposicion: List[PuntoRutaResponse]
    coordenadas_ruta: List[CoordenadaResponse]
    algoritmo_utilizado: AlgoritmoResponse
    distancia_total: int
    tiempo_estimado_minutos: Optional[int] = None
    estado_tarea: str

class ErrorRutaResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detalle: str
    sugerencias: List[str] = []

# Primero importamos las clases base y utilidades
from app.models.base import BaseModel

# Luego importamos los modelos en orden de dependencia
from app.models.usuario import Usuario, Rol, RolEnum
from app.models.supervision import Supervision
from app.models.ruta_optimizada import RutaOptimizada
from app.models.detalle_ruta import DetalleRuta
from app.models.paso_ruta import PasoRuta
from app.models.metrica_optimizacion import MetricaOptimizacion

__all__ = [
    'BaseModel', 'Usuario', 'Rol', 'RolEnum', 'Supervision',
    'RutaOptimizada', 'DetalleRuta', 'PasoRuta', 'MetricaOptimizacion'
]

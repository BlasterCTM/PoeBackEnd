# Primero importamos las clases base y utilidades
from app.models.base import BaseModel

# Importar modelos multi-tenant (primero la empresa)
from app.models.empresa import Empresa
from app.models.plan_suscripcion import PlanSuscripcion
from app.models.empresa_suscripcion import EmpresaSuscripcion

# Luego importamos los modelos en orden de dependencia
from app.models.usuario import Usuario, Rol, RolEnum
from app.models.supervision import Supervision
from app.models.ruta_optimizada import RutaOptimizada
from app.models.detalle_ruta import DetalleRuta
from app.models.paso_ruta import PasoRuta
from app.models.metrica_optimizacion import MetricaOptimizacion

# Importar modelos de chat
from app.models.chat_conversacion import ChatConversacion
from app.models.chat_mensaje import ChatMensaje

__all__ = [
    'BaseModel', 'Empresa', 'PlanSuscripcion', 'EmpresaSuscripcion',
    'Usuario', 'Rol', 'RolEnum', 'Supervision',
    'RutaOptimizada', 'DetalleRuta', 'PasoRuta', 'MetricaOptimizacion',
    'ChatConversacion', 'ChatMensaje'
]

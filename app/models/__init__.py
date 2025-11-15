# Primero importamos las clases base y utilidades
from app.models.base import BaseModel

# Importar modelos multi-tenant (primero la empresa)
from app.models.empresa import Empresa

# Modelos B2B (nuevos)
from app.models.plan_empresa import PlanEmpresa
from app.models.cotizacion import Cotizacion
from app.models.factura import Factura
from app.models.actividad_cliente import ActividadCliente

# Luego importamos los modelos en orden de dependencia
from app.models.usuario import Usuario, Rol, RolEnum
from app.models.mapa import Mapa
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.producto import Producto
from app.models.punto_reposicion import PuntoReposicion
from app.models.mueble_reposicion import MuebleReposicion
from app.models.tarea import Tarea
from app.models.estado_tarea import EstadoTarea
from app.models.detalle_tarea import DetalleTarea
from app.models.supervision import Supervision
from app.models.ruta_optimizada import RutaOptimizada
from app.models.detalle_ruta import DetalleRuta
from app.models.paso_ruta import PasoRuta
from app.models.metrica_optimizacion import MetricaOptimizacion

# Importar modelos de chat
from app.models.chat_conversacion import ChatConversacion
from app.models.chat_mensaje import ChatMensaje

# Importar modelo de auditoría (Backoffice)
from app.models.log_auditoria import LogAuditoria

__all__ = [
    'BaseModel', 'Empresa', 
    'PlanEmpresa', 'Cotizacion', 'Factura', 'ActividadCliente',
    'Usuario', 'Rol', 'RolEnum', 'Mapa', 'ObjetoMapa', 'ObjetoTipo',
    'UbicacionFisica', 'Producto', 'PuntoReposicion', 'MuebleReposicion',
    'Tarea', 'EstadoTarea', 'DetalleTarea', 'Supervision',
    'RutaOptimizada', 'DetalleRuta', 'PasoRuta', 'MetricaOptimizacion',
    'ChatConversacion', 'ChatMensaje', 'LogAuditoria'
]

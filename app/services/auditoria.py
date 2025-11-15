"""
Servicio de Auditoría para registrar automáticamente acciones administrativas
"""
from functools import wraps
from typing import Optional, Dict, Any, Callable
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.repositories.log_auditoria import LogAuditoriaRepository
from app.schemas.log_auditoria import LogAuditoriaCreate


class AuditoriaService:
    """Servicio para gestión de auditoría"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = LogAuditoriaRepository()
    
    def registrar(
        self,
        usuario: Usuario,
        accion: str,
        entidad: str,
        id_entidad: int,
        nombre_entidad: Optional[str] = None,
        datos_anteriores: Optional[Dict[str, Any]] = None,
        datos_nuevos: Optional[Dict[str, Any]] = None,
        ip_origen: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Registra una acción en el log de auditoría
        
        Args:
            usuario: Usuario que realizó la acción
            accion: Tipo de acción realizada
            entidad: Tipo de entidad afectada
            id_entidad: ID de la entidad
            nombre_entidad: Nombre descriptivo de la entidad
            datos_anteriores: Estado antes del cambio
            datos_nuevos: Estado después del cambio
            ip_origen: IP del cliente
            user_agent: User agent del navegador
        """
        log_data = LogAuditoriaCreate(
            id_usuario=usuario.id_usuario,
            nombre_usuario=usuario.nombre,
            accion=accion,
            entidad=entidad,
            id_entidad=id_entidad,
            nombre_entidad=nombre_entidad,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            ip_origen=ip_origen,
            user_agent=user_agent
        )
        
        return self.repo.registrar_accion(self.db, log_data)


def extraer_ip_y_user_agent(request: Request) -> tuple[Optional[str], Optional[str]]:
    """
    Extrae IP y User-Agent del request
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Tupla (ip_origen, user_agent)
    """
    # Obtener IP (considerar proxy con X-Forwarded-For)
    ip_origen = None
    if hasattr(request, 'client') and request.client:
        ip_origen = request.client.host
    
    # También verificar headers de proxy
    if hasattr(request, 'headers'):
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            ip_origen = forwarded_for.split(',')[0].strip()
    
    # Obtener User-Agent
    user_agent = None
    if hasattr(request, 'headers'):
        user_agent = request.headers.get('User-Agent')
    
    return ip_origen, user_agent


def auditar(
    accion: str,
    entidad: str,
    obtener_id_entidad: Optional[Callable] = None,
    obtener_nombre_entidad: Optional[Callable] = None,
    capturar_datos_anteriores: bool = False,
    capturar_datos_nuevos: bool = True
):
    """
    Decorador para auditar automáticamente acciones
    
    Uso:
        @auditar(
            accion="crear_plan",
            entidad="plan_empresa",
            obtener_id_entidad=lambda result: result.id_plan,
            obtener_nombre_entidad=lambda result: f"Plan {result.nombre_plan}"
        )
        async def crear_plan(...):
            ...
    
    Args:
        accion: Nombre de la acción
        entidad: Tipo de entidad
        obtener_id_entidad: Función para extraer ID de la entidad del resultado
        obtener_nombre_entidad: Función para extraer nombre de la entidad
        capturar_datos_anteriores: Si capturar estado anterior (para updates)
        capturar_datos_nuevos: Si capturar estado nuevo
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ejecutar la función original
            result = await func(*args, **kwargs)
            
            # Intentar registrar en auditoría (no fallar si hay error)
            try:
                # Buscar db y current_user en kwargs
                db = kwargs.get('db')
                current_user = kwargs.get('current_user')
                request = kwargs.get('request')
                
                if db and current_user:
                    # Extraer ID de entidad
                    id_entidad = None
                    if obtener_id_entidad:
                        id_entidad = obtener_id_entidad(result)
                    elif hasattr(result, 'id'):
                        id_entidad = result.id
                    
                    # Extraer nombre de entidad
                    nombre_entidad = None
                    if obtener_nombre_entidad:
                        nombre_entidad = obtener_nombre_entidad(result)
                    elif hasattr(result, 'nombre'):
                        nombre_entidad = result.nombre
                    
                    # Extraer IP y User-Agent
                    ip_origen, user_agent = None, None
                    if request:
                        ip_origen, user_agent = extraer_ip_y_user_agent(request)
                    
                    # Datos nuevos (si se requiere)
                    datos_nuevos = None
                    if capturar_datos_nuevos and hasattr(result, 'model_dump'):
                        datos_nuevos = result.model_dump()
                    
                    # Registrar en auditoría
                    auditoria_service = AuditoriaService(db)
                    auditoria_service.registrar(
                        usuario=current_user,
                        accion=accion,
                        entidad=entidad,
                        id_entidad=id_entidad,
                        nombre_entidad=nombre_entidad,
                        datos_nuevos=datos_nuevos,
                        ip_origen=ip_origen,
                        user_agent=user_agent
                    )
            
            except Exception as e:
                # Log error pero no fallar la operación
                print(f"Error al registrar auditoría: {e}")
            
            return result
        
        return wrapper
    return decorator

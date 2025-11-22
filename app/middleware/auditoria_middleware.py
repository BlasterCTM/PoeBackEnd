"""
Middleware de Auditoría Global
Registra automáticamente TODAS las operaciones importantes de TODOS los usuarios
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from typing import Callable
import json
from app.core.database.database import get_db
from app.services.auditoria import AuditoriaService, extraer_ip_y_user_agent


# Mapeo de rutas a acciones auditables
RUTAS_AUDITABLES = {
    # ============================================
    # TAREAS (Supervisores y Reponedores)
    # ============================================
    "POST /tareas": {
        "accion": "crear_tarea",
        "entidad": "tarea",
        "descripcion": "Crear nueva tarea"
    },
    "PUT /tareas/{id}": {
        "accion": "actualizar_tarea",
        "entidad": "tarea",
        "descripcion": "Actualizar tarea"
    },
    "PATCH /tareas/{id}/estado": {
        "accion": "cambiar_estado_tarea",
        "entidad": "tarea",
        "descripcion": "Cambiar estado de tarea"
    },
    "DELETE /tareas/{id}": {
        "accion": "eliminar_tarea",
        "entidad": "tarea",
        "descripcion": "Eliminar tarea"
    },
    "POST /tareas/{id}/completar": {
        "accion": "completar_tarea",
        "entidad": "tarea",
        "descripcion": "Completar tarea"
    },
    
    # ============================================
    # RUTAS (Supervisores)
    # ============================================
    "POST /rutas": {
        "accion": "crear_ruta",
        "entidad": "ruta_optimizada",
        "descripcion": "Crear ruta optimizada"
    },
    "POST /rutas/optimizar": {
        "accion": "optimizar_ruta",
        "entidad": "ruta_optimizada",
        "descripcion": "Optimizar ruta con A*"
    },
    "DELETE /rutas/{id}": {
        "accion": "eliminar_ruta",
        "entidad": "ruta_optimizada",
        "descripcion": "Eliminar ruta"
    },
    
    # ============================================
    # PRODUCTOS (Administradores)
    # ============================================
    "POST /productos": {
        "accion": "crear_producto",
        "entidad": "producto",
        "descripcion": "Crear producto"
    },
    "PUT /productos/{id}": {
        "accion": "actualizar_producto",
        "entidad": "producto",
        "descripcion": "Actualizar producto"
    },
    "DELETE /productos/{id}": {
        "accion": "eliminar_producto",
        "entidad": "producto",
        "descripcion": "Eliminar producto"
    },
    
    # ============================================
    # PUNTOS DE REPOSICIÓN (Administradores)
    # ============================================
    "POST /puntos": {
        "accion": "crear_punto",
        "entidad": "punto_reposicion",
        "descripcion": "Crear punto de reposición"
    },
    "PUT /puntos/{id}": {
        "accion": "actualizar_punto",
        "entidad": "punto_reposicion",
        "descripcion": "Actualizar punto"
    },
    "DELETE /puntos/{id}": {
        "accion": "eliminar_punto",
        "entidad": "punto_reposicion",
        "descripcion": "Eliminar punto"
    },
    
    # ============================================
    # USUARIOS (Administradores y SuperAdmin)
    # ============================================
    "POST /usuarios": {
        "accion": "crear_usuario",
        "entidad": "usuario",
        "descripcion": "Crear usuario"
    },
    "PUT /usuarios/{id}": {
        "accion": "actualizar_usuario",
        "entidad": "usuario",
        "descripcion": "Actualizar usuario"
    },
    "DELETE /usuarios/{id}": {
        "accion": "eliminar_usuario",
        "entidad": "usuario",
        "descripcion": "Eliminar usuario"
    },
    "PATCH /usuarios/{id}/suspender": {
        "accion": "suspender_usuario",
        "entidad": "usuario",
        "descripcion": "Suspender usuario"
    },
    "PATCH /usuarios/{id}/activar": {
        "accion": "activar_usuario",
        "entidad": "usuario",
        "descripcion": "Activar usuario"
    },
    
    # ============================================
    # PLANES Y EMPRESAS (SuperAdmin)
    # ============================================
    "POST /planes": {
        "accion": "crear_plan",
        "entidad": "plan_empresa",
        "descripcion": "Crear plan personalizado"
    },
    "PUT /planes/{id}": {
        "accion": "actualizar_plan",
        "entidad": "plan_empresa",
        "descripcion": "Actualizar plan"
    },
    "POST /planes/{id}/upgrade": {
        "accion": "upgrade_plan",
        "entidad": "plan_empresa",
        "descripcion": "Upgrade de plan"
    },
    "PATCH /planes/{id}/suspender": {
        "accion": "suspender_plan",
        "entidad": "plan_empresa",
        "descripcion": "Suspender plan"
    },
    "POST /empresas": {
        "accion": "crear_empresa",
        "entidad": "empresa",
        "descripcion": "Crear empresa B2B"
    },
    "PUT /empresas/{id}": {
        "accion": "actualizar_empresa",
        "entidad": "empresa",
        "descripcion": "Actualizar empresa"
    },
    
    # ============================================
    # COTIZACIONES (SuperAdmin)
    # ============================================
    "POST /cotizaciones": {
        "accion": "crear_cotizacion",
        "entidad": "cotizacion",
        "descripcion": "Solicitar cotización"
    },
    "PATCH /cotizaciones/{id}": {
        "accion": "actualizar_cotizacion",
        "entidad": "cotizacion",
        "descripcion": "Actualizar cotización"
    },
    "POST /cotizaciones/{id}/convertir": {
        "accion": "convertir_cotizacion",
        "entidad": "cotizacion",
        "descripcion": "Convertir cotización a cliente"
    },
    
    # ============================================
    # PREDICCIONES ML
    # ============================================
    "POST /predicciones": {
        "accion": "generar_prediccion",
        "entidad": "prediccion_reposicion",
        "descripcion": "Generar predicción ML"
    },
    "PATCH /predicciones/{id}/aplicar": {
        "accion": "aplicar_prediccion",
        "entidad": "prediccion_reposicion",
        "descripcion": "Aplicar predicción"
    },
}


class AuditoriaMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra automáticamente acciones auditables
    de TODOS los usuarios en la base de datos
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ejecutar el request
        response = await call_next(request)
        
        # Solo auditar si fue exitoso (2xx)
        if 200 <= response.status_code < 300:
            # Intentar auditar (no fallar si hay error)
            try:
                await self._auditar_si_necesario(request, response)
            except Exception as e:
                # Log error pero no afectar la respuesta
                print(f"⚠️  Error en auditoría middleware: {e}")
        
        return response
    
    async def _auditar_si_necesario(self, request: Request, response: Response):
        """Registra la acción si está en la lista de rutas auditables"""
        
        # Verificar si la ruta es auditable
        ruta_template = self._obtener_ruta_template(request.url.path, request.method)
        
        if ruta_template not in RUTAS_AUDITABLES:
            return
        
        # Obtener configuración de auditoría para esta ruta
        config = RUTAS_AUDITABLES[ruta_template]
        
        # Obtener usuario autenticado del request.state (FastAPI lo pone ahí)
        current_user = getattr(request.state, 'user', None)
        
        # Si no está en request.state, intentar obtenerlo del header Authorization
        if not current_user:
            # Intentar obtener del contexto de la request
            # (algunos endpoints lo guardan en diferentes lugares)
            return  # No auditar requests sin usuario autenticado
        
        # Obtener DB session - crear una nueva conexión para el middleware
        from app.core.database.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Extraer ID de entidad del path
            id_entidad = self._extraer_id_de_path(request.url.path)
            
            # Extraer IP y User-Agent
            ip_origen, user_agent = extraer_ip_y_user_agent(request)
            
            # Intentar obtener body del request para datos_nuevos
            datos_nuevos = None
            if request.method in ["POST", "PUT", "PATCH"]:
                # El body ya fue consumido, no podemos leerlo aquí
                # Los datos_nuevos se capturarán en endpoints específicos con @auditar
                pass
            
            # Registrar en auditoría
            auditoria = AuditoriaService(db)
            auditoria.registrar(
                usuario=current_user,
                accion=config["accion"],
                entidad=config["entidad"],
                id_entidad=id_entidad or 0,
                nombre_entidad=config["descripcion"],
                datos_nuevos=datos_nuevos,
                ip_origen=ip_origen,
                user_agent=user_agent
            )
            
            db.commit()
        
        except Exception as e:
            db.rollback()
            # Log error pero no afectar la respuesta
            print(f"⚠️  Error al registrar auditoría: {e}")
        
        finally:
            db.close()
    
    def _obtener_ruta_template(self, path: str, method: str) -> str:
        """
        Convierte /tareas/123 a /tareas/{id}
        """
        parts = path.split('/')
        template_parts = []
        
        for part in parts:
            if part.isdigit():
                template_parts.append('{id}')
            else:
                template_parts.append(part)
        
        return f"{method} {'/'.join(template_parts)}"
    
    def _extraer_id_de_path(self, path: str) -> int:
        """Extrae el ID numérico del path"""
        parts = path.split('/')
        for part in parts:
            if part.isdigit():
                return int(part)
        return 0

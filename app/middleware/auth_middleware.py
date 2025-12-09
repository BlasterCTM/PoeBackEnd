"""
Middleware de Autenticación
Inyecta el usuario autenticado en request.state para que otros middlewares lo usen
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.core.database.database import SessionLocal
from app.core.security.auth import verify_token
from app.repositories.usuario import UsuarioRepository


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que inyecta el usuario autenticado en request.state
    
    Extrae el token JWT del header Authorization y lo valida.
    Si es válido, obtiene el usuario de la BD y lo guarda en request.state.user
    
    Otros middlewares (como AuditoriaMiddleware) pueden acceder a request.state.user
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Inicializar user como None
        request.state.user = None
        
        # Intentar obtener token del header Authorization
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            try:
                # Validar token y obtener payload
                payload = verify_token(token)
                
                if payload:
                    # Extraer ID de usuario del payload
                    user_id = payload.get("sub")
                    
                    if user_id:
                        # Obtener usuario de BD
                        db = SessionLocal()
                        try:
                            repo = UsuarioRepository()
                            user = repo.get_by_id(db, int(user_id))
                            
                            if user:
                                # Guardar usuario en request.state
                                request.state.user = user
                        
                        finally:
                            db.close()
            
            except Exception as e:
                # Si hay error en validación, simplemente no se inyecta el usuario
                # No bloqueamos la request (eso lo maneja el endpoint con Depends)
                pass
        
        # Continuar con la request normalmente
        response = await call_next(request)
        return response

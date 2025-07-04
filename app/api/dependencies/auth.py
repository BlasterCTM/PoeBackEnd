from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security.auth import get_current_user as get_current_user_core
from app.core.database.database import get_db
from fastapi.security import OAuth2PasswordBearer
from app.models.usuario import Usuario, RolEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/token")

# Wrapper para usar la función de core.security.auth
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user_core(token=token, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user

async def get_current_admin_user(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Valida que el usuario actual sea administrador.
    Solo los administradores pueden acceder a funciones administrativas.
    """
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden acceder a esta funcionalidad."
        )
    return current_user

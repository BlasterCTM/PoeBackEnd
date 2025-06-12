from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security.auth import get_current_user as get_current_user_core
from app.core.database.database import get_db
from fastapi.security import OAuth2PasswordBearer

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

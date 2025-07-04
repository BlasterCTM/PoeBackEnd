from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies.auth import get_current_admin_user
from app.api.dependencies.database import get_database
from app.services.dashboard import DashboardService
from datetime import date

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/resumen")
def dashboard_resumen(
    db: Session = Depends(get_database),
    admin_user=Depends(get_current_admin_user),
    periodo: str = Query("dia", enum=["dia", "semana", "mes"]),
    fecha: str = Query(None, description="Fecha base en formato YYYY-MM-DD")
):
    """
    Devuelve el resumen para el dashboard de administrador.
    Permite filtrar por periodo: dia, semana, mes y fecha base.
    """
    fecha_base = date.today()
    if fecha:
        fecha_base = date.fromisoformat(fecha)
    return DashboardService(db).resumen(periodo=periodo, fecha_base=fecha_base)

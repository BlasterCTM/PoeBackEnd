from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.schemas.ruta import RutaOptimaRequest, RutaOptimaResponse, Punto
from app.repositories.ruta import calcular_ruta

router = APIRouter()

@router.post("/ruta/optima", response_model=RutaOptimaResponse)
async def ruta_optima(
    datos: RutaOptimaRequest,
    db: Session = Depends(get_db)
):
    inicio = (datos.inicio.x, datos.inicio.y)
    fin = (datos.fin.x, datos.fin.y)
    ruta = calcular_ruta(db, datos.mapa_id, inicio, fin)
    if not ruta:
        raise HTTPException(status_code=404, detail="No se encontró ruta posible")
    return RutaOptimaResponse(ruta=[Punto(x=x, y=y) for x, y in ruta])

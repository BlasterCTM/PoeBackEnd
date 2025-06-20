from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.database.database import get_db
from app.models.mueble_reposicion import MuebleReposicion
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.mapa import Mapa

router = APIRouter()

@router.get("/muebles/reposicion")
def listar_muebles_reposicion(db: Session = Depends(get_db)):
    muebles = db.query(MuebleReposicion).all()
    resultado = []
    for mueble in muebles:
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first()
        if not objeto:
            continue
        tipo = db.query(ObjetoTipo).filter(ObjetoTipo.id_tipo == objeto.id_tipo).first()
        ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).all()
        ubicaciones_list = []
        for ubic in ubicaciones:
            mapa = db.query(Mapa).filter(Mapa.id_mapa == ubic.id_mapa).first()
            ubicaciones_list.append({
                "x": ubic.x,
                "y": ubic.y,
                "mapa": {
                    "id_mapa": mapa.id_mapa if mapa else None,
                    "nombre": mapa.nombre if mapa else None,
                    "ancho": mapa.ancho if mapa else None,
                    "alto": mapa.alto if mapa else None
                }
            })
        resultado.append({
            "id_mueble": mueble.id_mueble,
            "filas": mueble.filas,
            "columnas": mueble.columnas,
            "objeto_mapa": {
                "id_objeto": objeto.id_objeto,
                "nombre": objeto.nombre,
                "tipo": {
                    "id_tipo": tipo.id_tipo if tipo else None,
                    "nombre_tipo": tipo.nombre_tipo if tipo else None,
                    "caminable": tipo.caminable if tipo else None,
                    "destino": tipo.destino if tipo else None
                },
                "ubicaciones": ubicaciones_list
            }
        })
    return resultado

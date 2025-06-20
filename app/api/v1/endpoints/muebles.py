from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.core.database.database import get_db
from app.models.mueble_reposicion import MuebleReposicion
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.mapa import Mapa
from app.models.punto_reposicion import PuntoReposicion

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

@router.post("/muebles/reposicion", status_code=201)
def crear_mueble_reposicion(
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    id_objeto = body.get("id_objeto")
    filas = body.get("filas")
    columnas = body.get("columnas")
    if not id_objeto or not isinstance(filas, int) or not isinstance(columnas, int) or filas <= 0 or columnas <= 0:
        raise HTTPException(status_code=422, detail="id_objeto, filas y columnas son requeridos y deben ser mayores a cero.")
    try:
        # Iniciar transacción
        mueble = MuebleReposicion(id_objeto=id_objeto, filas=filas, columnas=columnas)
        db.add(mueble)
        db.flush()  # Para obtener id_mueble
        puntos = []
        for fila in range(1, filas+1):
            for columna in range(1, columnas+1):
                # Validar duplicidad
                existe = db.query(PuntoReposicion).filter_by(id_mueble=mueble.id_mueble, nivel=fila, estanteria=columna).first()
                if not existe:
                    punto = PuntoReposicion(id_mueble=mueble.id_mueble, nivel=fila, estanteria=columna)
                    db.add(punto)
                    puntos.append(punto)
        db.commit()
        db.refresh(mueble)
        return {
            "mueble": {
                "id_mueble": mueble.id_mueble,
                "id_objeto": mueble.id_objeto,
                "filas": mueble.filas,
                "columnas": mueble.columnas
            },
            "puntos": [
                {"id_punto": p.id_punto, "nivel": p.nivel, "estanteria": p.estanteria} for p in puntos
            ]
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear mueble o puntos: {str(e)}")

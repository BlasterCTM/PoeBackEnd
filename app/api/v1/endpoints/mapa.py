from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.models.mapa import Mapa
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.objeto_mapa import ObjetoMapa
from app.models.objeto_tipo import ObjetoTipo
from app.models.mueble_reposicion import MuebleReposicion
from app.models.punto_reposicion import PuntoReposicion
from app.models.producto import Producto
from app.schemas.mapa import MapeoReposicionResponse, MapaOut, UbicacionOut, ObjetoOut, MuebleOut, PuntoReposicionOut, ProductoAsociado
from app.schemas.mapa_vista import (
    MapaVistaGraficaResponse, MapaVistaOut, ObjetoUbicacionOut, ObjetoMapaVistaOut, ObjetoTipoOut, MuebleVistaOut, PuntoReposicionVistaOut
)

router = APIRouter()

@router.get("/mapa/reposicion", response_model=MapeoReposicionResponse)
def visualizar_mapa_reposicion(
    id_mapa: int = Query(None, description="ID del mapa a consultar (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user or current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="Solo administradores pueden consultar el mapeado de reposición.")
    # Seleccionar el mapa
    mapa = db.query(Mapa).first() if id_mapa is None else db.query(Mapa).filter(Mapa.id_mapa == id_mapa).first()
    if not mapa:
        return {"mensaje": "No hay mapas registrados.", "mapa": None, "ubicaciones": []}
    ubicaciones_db = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa.id_mapa).all()
    if not ubicaciones_db:
        return {"mensaje": "No hay ubicaciones cargadas.", "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto), "ubicaciones": []}
    ubicaciones = []
    puntos_reposicion_existen = False
    for ubic in ubicaciones_db:
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == ubic.id_objeto).first() if ubic.id_objeto else None
        objeto_out = None
        mueble_out = None
        if objeto:
            tipo = db.query(ObjetoTipo).filter(ObjetoTipo.id_tipo == objeto.id_tipo).first()
            objeto_out = ObjetoOut(
                nombre=objeto.nombre,
                tipo=tipo.nombre_tipo if tipo else "",
                caminable=tipo.caminable if tipo else None
            )
            mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_objeto == objeto.id_objeto).first()
            if mueble:
                puntos_db = db.query(PuntoReposicion).filter(PuntoReposicion.id_mueble == mueble.id_mueble).all()
                puntos_out = []
                for punto in puntos_db:
                    producto = db.query(Producto).filter(Producto.id_producto == punto.id_producto).first() if punto.id_producto else None
                    producto_out = None
                    if producto:
                        producto_out = ProductoAsociado(
                            nombre=producto.nombre,
                            categoria=producto.categoria,
                            unidad_tipo=producto.unidad_tipo,
                            unidad_cantidad=producto.unidad_cantidad
                        )
                    puntos_out.append(PuntoReposicionOut(
                        nivel=punto.nivel,
                        estanteria=punto.estanteria,
                        producto=producto_out
                    ))
                if puntos_out:
                    puntos_reposicion_existen = True
                mueble_out = MuebleOut(
                    filas=mueble.filas,
                    columnas=mueble.columnas,
                    puntos_reposicion=puntos_out
                )
        ubicaciones.append(UbicacionOut(
            x=ubic.x,
            y=ubic.y,
            objeto=objeto_out,
            mueble=mueble_out
        ))
    if not puntos_reposicion_existen:
        return {"mensaje": "No hay puntos de reposición registrados.", "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto), "ubicaciones": []}
    return {
        "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto),
        "ubicaciones": ubicaciones
    }

@router.get("/mapa/vista-grafica", response_model=MapaVistaGraficaResponse)
def vista_grafica_mapa(
    id_mapa: int = Query(None, description="ID del mapa a consultar (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user or current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="Solo administradores pueden consultar la vista gráfica del mapa.")
    mapa = db.query(Mapa).first() if id_mapa is None else db.query(Mapa).filter(Mapa.id_mapa == id_mapa).first()
    if not mapa:
        return {"mensaje": "No hay mapas registrados.", "mapa": None, "objetos": []}
    ubicaciones_db = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa.id_mapa).all()
    if not ubicaciones_db:
        return {"mensaje": "No hay ubicaciones cargadas.", "mapa": MapaVistaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto), "objetos": []}
    objetos = []
    for ubic in ubicaciones_db:
        # Validación de límites espaciales
        if ubic.x > mapa.ancho or ubic.y > mapa.alto:
            raise HTTPException(status_code=422, detail=f"Coordenadas fuera del límite del mapa: ({ubic.x}, {ubic.y})")
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == ubic.id_objeto).first() if ubic.id_objeto else None
        if not objeto:
            continue
        tipo = db.query(ObjetoTipo).filter(ObjetoTipo.id_tipo == objeto.id_tipo).first()
        tipo_out = ObjetoTipoOut(
            nombre_tipo=tipo.nombre_tipo if tipo else "",
            caminable=tipo.caminable if tipo else None,
            destino=tipo.destino if tipo else None
        )
        objeto_out = ObjetoMapaVistaOut(
            id=objeto.id_objeto,
            nombre=objeto.nombre,
            tipo=tipo_out
        )
        mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_objeto == objeto.id_objeto).first()
        mueble_out = None
        if mueble:
            puntos_db = db.query(PuntoReposicion).filter(PuntoReposicion.id_mueble == mueble.id_mueble).all()
            puntos_out = []
            for punto in puntos_db:
                # Validación de límites internos del mueble
                if punto.nivel > mueble.filas or punto.estanteria > mueble.columnas:
                    raise HTTPException(status_code=422, detail=f"El punto de reposición (id {punto.id_punto}) excede la capacidad del mueble.")
                puntos_out.append(PuntoReposicionVistaOut(
                    id_punto=punto.id_punto,
                    nivel=punto.nivel,
                    estanteria=punto.estanteria
                ))
            mueble_out = MuebleVistaOut(
                filas=mueble.filas,
                columnas=mueble.columnas,
                puntos_reposicion=puntos_out
            )
        objetos.append(ObjetoUbicacionOut(
            x=ubic.x,
            y=ubic.y,
            objeto=objeto_out,
            mueble=mueble_out
        ))
    return {
        "mapa": MapaVistaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto),
        "objetos": objetos
    }

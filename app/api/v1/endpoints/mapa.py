from fastapi import APIRouter, Depends, HTTPException, Query, Body
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
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.punto_reposicion import desasignar_producto_de_punto

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
                        id_punto=punto.id_punto,
                        id_mueble=punto.id_mueble,
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

@router.get("/mapa/supervisor")
def vista_puntos_supervisor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() != "supervisor":
        raise HTTPException(status_code=403, detail="Solo los supervisores pueden acceder a este recurso.")

    from app.models.supervision import Supervision
    from app.models.mueble_reposicion import MuebleReposicion
    from app.models.punto_reposicion import PuntoReposicion
    from app.models.objeto_mapa import ObjetoMapa
    from app.models.ubicacion_fisica import UbicacionFisica
    from app.models.objeto_tipo import ObjetoTipo
    from app.models.mapa import Mapa
    from app.models.producto import Producto

    # Obtener puntos asignados por usuario_punto
    puntos_usuario = db.query(PuntoReposicion.id_punto).filter(PuntoReposicion.id_usuario == current_user.id_usuario).all()
    puntos_usuario_ids = [p[0] for p in puntos_usuario]

    # Obtener reponedores supervisados por este supervisor
    reponedores = db.query(Supervision.reponedor_id).filter(Supervision.supervisor_id == current_user.id_usuario).all()
    reponedor_ids = [r[0] for r in reponedores]

    # Obtener puntos asignados a los reponedores supervisados
    puntos_reponedores = []
    if reponedor_ids:
        puntos_reponedores = db.query(PuntoReposicion.id_punto).filter(PuntoReposicion.id_usuario.in_(reponedor_ids)).all()
    puntos_reponedores_ids = [p[0] for p in puntos_reponedores]

    # Unir todos los puntos asignados
    puntos_ids_asignados = set(puntos_usuario_ids + puntos_reponedores_ids)

    # Obtener todos los puntos del mapa del supervisor
    # Primero, obtener el mapa asociado a los puntos asignados (si no hay, devolver mensaje)
    primer_punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto.in_(list(puntos_ids_asignados))).first()
    if not primer_punto:
        return {"mensaje": "No tienes puntos de reposición asignados actualmente."}
    mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == primer_punto.id_mueble).first()
    if not mueble:
        return {"mensaje": "No se encontró el mueble asociado a tus puntos."}
    objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first()
    if not objeto:
        return {"mensaje": "No se encontró el objeto asociado al mueble."}
    ubicacion = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).first()
    if not ubicacion:
        return {"mensaje": "No se encontró la ubicación asociada al objeto."}
    mapa = db.query(Mapa).filter(Mapa.id_mapa == ubicacion.id_mapa).first()
    if not mapa:
        return {"mensaje": "No se encontró el mapa asociado a tus puntos."}

    # Obtener todos los puntos del mapa
    muebles = db.query(MuebleReposicion).all()
    puntos_todos = db.query(PuntoReposicion).all()
    ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa.id_mapa).all()
    objetos = {o.id_objeto: o for o in db.query(ObjetoMapa).all()}

    respuesta = {
        "mapa": {
            "id": mapa.id_mapa,
            "nombre": mapa.nombre,
            "ancho": mapa.ancho,
            "alto": mapa.alto
        },
        "puntos": []
    }

    for punto in puntos_todos:
        # Buscar la ubicación y objeto relacionados
        mueble = next((m for m in muebles if m.id_mueble == punto.id_mueble), None)
        if not mueble:
            continue
        objeto = objetos.get(mueble.id_objeto)
        if not objeto:
            continue
        ubicacion = next((u for u in ubicaciones if u.id_objeto == objeto.id_objeto), None)
        if not ubicacion:
            continue
        producto = db.query(Producto).filter(Producto.id_producto == punto.id_producto).first() if punto.id_producto else None
        respuesta["puntos"].append({
            "x": ubicacion.x,
            "y": ubicacion.y,
            "punto_id": punto.id_punto,
            "pasillo": objeto.nombre,
            "estanteria": punto.estanteria,
            "nivel": punto.nivel,
            "detalle": producto.nombre if producto else None,
            "resaltado": punto.id_punto in puntos_ids_asignados
        })

    return respuesta

@router.post("/puntos/asignar")
def asignar_punto_usuario(
    id_usuario: int = Body(..., embed=True),
    id_punto: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para asignar puntos.")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == id_punto).first()
    if not usuario or not punto:
        raise HTTPException(status_code=404, detail="Usuario o punto no encontrado.")
    punto.id_usuario = id_usuario
    db.commit()
    db.refresh(punto)
    return {"mensaje": "Punto asignado correctamente", "id_punto": id_punto, "id_usuario": id_usuario}

@router.delete("/puntos/desasignar")
def desasignar_punto_usuario(
    id_punto: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Solo administradores o supervisores pueden desasignar puntos
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para desasignar puntos.")
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == id_punto).first()
    if not punto:
        raise HTTPException(status_code=404, detail="Punto de reposición no encontrado.")
    if not punto.id_usuario:
        raise HTTPException(status_code=404, detail="El punto no está asignado a ningún usuario.")
    punto.id_usuario = None
    db.commit()
    db.refresh(punto)
    return {"mensaje": "Punto desasignado correctamente."}

@router.put("/puntos/{id_punto}/asignar-producto", response_model=PuntoReposicionOut)
def asignar_producto_a_punto(
    id_punto: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    id_producto = body.get("id_producto")
    id_usuario = body.get("id_usuario")
    if not id_producto or not id_usuario:
        raise HTTPException(status_code=400, detail="Faltan datos para asignar producto y usuario.")
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="No autorizado.")

    # Asignar producto y usuario al punto
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == id_punto).first()
    if not punto:
        raise HTTPException(status_code=404, detail="Punto de reposición no encontrado.")
    punto.id_producto = id_producto
    punto.id_usuario = id_usuario
    db.commit()
    db.refresh(punto)

    # Construir respuesta como antes
    producto = db.query(Producto).filter(Producto.id_producto == punto.id_producto).first() if punto.id_producto else None
    producto_out = None
    if producto:
        producto_out = ProductoAsociado(
            nombre=producto.nombre,
            categoria=producto.categoria,
            unidad_tipo=producto.unidad_tipo,
            unidad_cantidad=producto.unidad_cantidad
        )
    return PuntoReposicionOut(
        id_punto=punto.id_punto,
        id_mueble=punto.id_mueble,
        nivel=punto.nivel,
        estanteria=punto.estanteria,
        producto=producto_out
    )

@router.delete("/puntos/{id_punto}/desasignar-producto", response_model=PuntoReposicionOut)
def desasignar_producto_punto(
    id_punto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden desasignar productos de puntos.")
    try:
        punto = desasignar_producto_de_punto(db, id_punto)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PuntoReposicionOut(
        id_punto=punto.id_punto,
        id_mueble=punto.id_mueble,
        nivel=punto.nivel,
        estanteria=punto.estanteria,
        producto=None
    )

@router.post("/mapas", status_code=201)
def crear_mapa(
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    nombre = body.get("nombre")
    ancho = body.get("ancho")
    alto = body.get("alto")
    if not nombre or not isinstance(ancho, int) or not isinstance(alto, int) or ancho <= 0 or alto <= 0:
        raise HTTPException(status_code=422, detail="nombre, ancho y alto son requeridos y deben ser mayores a cero.")
    # Validar duplicidad de nombre
    existe = db.query(Mapa).filter(Mapa.nombre == nombre).first()
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe un mapa con ese nombre.")
    try:
        mapa = Mapa(nombre=nombre, ancho=ancho, alto=alto)
        db.add(mapa)
        db.flush()  # Para obtener id_mapa
        ubicaciones = []
        for x in range(ancho):
            for y in range(alto):
                ubic = UbicacionFisica(id_mapa=mapa.id_mapa, x=x, y=y)
                db.add(ubic)
                ubicaciones.append({"x": x, "y": y})
        db.commit()
        db.refresh(mapa)
        return {
            "id_mapa": mapa.id_mapa,
            "nombre": mapa.nombre,
            "ancho": mapa.ancho,
            "alto": mapa.alto,
            "total_ubicaciones": len(ubicaciones),
            "ubicaciones": ubicaciones
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear mapa o ubicaciones: {str(e)}")


@router.get("/mapa/supervisor/vista", response_model=MapeoReposicionResponse)
def visualizar_mapa_supervisor(
    id_mapa: int = Query(None, description="ID del mapa a consultar (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() != "supervisor":
        raise HTTPException(status_code=403, detail="Solo los supervisores pueden acceder a este recurso.")

    from app.models.supervision import Supervision

    # Obtener ids de puntos asignados al supervisor y sus reponedores
    puntos_usuario = db.query(PuntoReposicion.id_punto).filter(PuntoReposicion.id_usuario == current_user.id_usuario).all()
    puntos_usuario_ids = [p[0] for p in puntos_usuario]

    reponedores = db.query(Supervision.reponedor_id).filter(Supervision.supervisor_id == current_user.id_usuario).all()
    reponedor_ids = [r[0] for r in reponedores]

    puntos_reponedores = []
    if reponedor_ids:
        puntos_reponedores = db.query(PuntoReposicion.id_punto).filter(PuntoReposicion.id_usuario.in_(reponedor_ids)).all()
    puntos_reponedores_ids = [p[0] for p in puntos_reponedores]

    puntos_ids_permitidos = set(puntos_usuario_ids + puntos_reponedores_ids)

    # Seleccionar el mapa
    mapa = db.query(Mapa).first() if id_mapa is None else db.query(Mapa).filter(Mapa.id_mapa == id_mapa).first()
    if not mapa:
        return {"mensaje": "No hay mapas registrados.", "mapa": None, "ubicaciones": []}
    ubicaciones_db = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa.id_mapa).all()
    if not ubicaciones_db:
        return {"mensaje": "No hay ubicaciones cargadas.", "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto), "ubicaciones": []}
    ubicaciones = []
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
                    # Solo mostrar detalles si el punto pertenece al supervisor o sus reponedores
                    producto_out = None
                    if punto.id_punto in puntos_ids_permitidos:
                        producto = db.query(Producto).filter(Producto.id_producto == punto.id_producto).first() if punto.id_producto else None
                        if producto:
                            producto_out = ProductoAsociado(
                                nombre=producto.nombre,
                                categoria=producto.categoria,
                                unidad_tipo=producto.unidad_tipo,
                                unidad_cantidad=producto.unidad_cantidad
                            )
                    puntos_out.append(PuntoReposicionOut(
                        id_punto=punto.id_punto,
                        id_mueble=punto.id_mueble,
                        nivel=punto.nivel,
                        estanteria=punto.estanteria,
                        producto=producto_out
                    ))
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
    return {
        "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto),
        "ubicaciones": ubicaciones
    }


@router.get("/mapa/reponedor/vista", response_model=MapeoReposicionResponse)
def visualizar_mapa_reponedor(
    id_mapa: int = Query(None, description="ID del mapa a consultar (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() != "reponedor":
        raise HTTPException(status_code=403, detail="Solo los reponedores pueden acceder a este recurso.")

    puntos_usuario = db.query(PuntoReposicion.id_punto).filter(PuntoReposicion.id_usuario == current_user.id_usuario).all()
    puntos_ids_permitidos = set([p[0] for p in puntos_usuario])

    # Seleccionar el mapa
    mapa = db.query(Mapa).first() if id_mapa is None else db.query(Mapa).filter(Mapa.id_mapa == id_mapa).first()
    if not mapa:
        return {"mensaje": "No hay mapas registrados.", "mapa": None, "ubicaciones": []}
    ubicaciones_db = db.query(UbicacionFisica).filter(UbicacionFisica.id_mapa == mapa.id_mapa).all()
    if not ubicaciones_db:
        return {"mensaje": "No hay ubicaciones cargadas.", "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto), "ubicaciones": []}
    ubicaciones = []
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
                    producto_out = None
                    if punto.id_punto in puntos_ids_permitidos:
                        producto = db.query(Producto).filter(Producto.id_producto == punto.id_producto).first() if punto.id_producto else None
                        if producto:
                            producto_out = ProductoAsociado(
                                nombre=producto.nombre,
                                categoria=producto.categoria,
                                unidad_tipo=producto.unidad_tipo,
                                unidad_cantidad=producto.unidad_cantidad
                            )
                    puntos_out.append(PuntoReposicionOut(
                        id_punto=punto.id_punto,
                        id_mueble=punto.id_mueble,
                        nivel=punto.nivel,
                        estanteria=punto.estanteria,
                        producto=producto_out
                    ))
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
    return {
        "mapa": MapaOut(id=mapa.id_mapa, nombre=mapa.nombre, ancho=mapa.ancho, alto=mapa.alto),
        "ubicaciones": ubicaciones
    }

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from app.schemas.producto import ProductoCreate, ProductoOut, ProductoUpdate
from app.repositories.producto import (
    create_producto,
    get_productos,
    update_producto,
    get_producto_by_id,
    producto_vinculado_a_tareas_activas,
    buscar_productos,  # <-- importar la nueva función
)
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from fastapi import Response
import uuid
from app.repositories.punto_reposicion import (
    obtener_punto_por_producto,
    desasignar_punto_por_producto,
    asignar_o_reasignar_producto_a_punto, obtener_ubicacion_producto
)
from app.models.punto_reposicion import PuntoReposicion
from app.models.objeto_mapa import ObjetoMapa
from app.models.mueble_reposicion import MuebleReposicion
from app.models.ubicacion_fisica import UbicacionFisica
from app.schemas.mapa import PuntoReposicionOut, ProductoAsociado

router = APIRouter()

# Estados activos: debes ajustar estos IDs según tu tabla estado_tarea
ESTADOS_ACTIVOS = [1, 2]  # Ejemplo: 1=pendiente, 2=en_progreso


@router.post("/productos", response_model=ProductoOut, status_code=201)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear productos")
    # Generar código único si no se proporciona
    codigo_unico = producto.codigo_unico or str(uuid.uuid4())[:8].upper()
    try:
        db_producto = create_producto(db, producto, id_usuario=producto.id_usuario, codigo_unico=codigo_unico)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return db_producto


@router.get("/productos")
def listar_productos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    orden: str = Query("nombre", pattern="^(nombre|fecha)$"),
    estado: str = Query(None, pattern="^(activo|inactivo)?$")
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    data = get_productos(db, page=page, limit=limit, orden=orden, estado=estado)
    return data


@router.get("/productos/buscar")
def buscar_productos_endpoint(
    nombre: str = Query(None, description="Nombre parcial o completo del producto"),
    categoria: str = Query(None, description="Categoría exacta del producto"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user or current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden buscar productos.")
    resultados = buscar_productos(db, nombre=nombre, categoria=categoria)
    if not resultados:
        return {"total": 0, "mensaje": "Sin resultados para los filtros aplicados."}
    return {
        "total": len(resultados),
        "resultados": [
            {
                "id": p.id_producto,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "unidad_tipo": p.unidad_tipo,
                "unidad_cantidad": p.unidad_cantidad
            } for p in resultados
        ]
    }


@router.get("/productos/{id_producto}")
def obtener_producto_con_ubicacion(
    id_producto: int,
    db: Session = Depends(get_db)
):
    db_producto = get_producto_by_id(db, id_producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    punto = obtener_punto_por_producto(db, id_producto)
    punto_out = None
    if punto:
        punto_out = PuntoReposicionOut(
            id_punto=punto.id_punto,
            id_mueble=punto.id_mueble,
            nivel=punto.nivel,
            estanteria=punto.estanteria,
            producto=ProductoAsociado(
                nombre=db_producto.nombre,
                categoria=db_producto.categoria,
                unidad_tipo=db_producto.unidad_tipo,
                unidad_cantidad=db_producto.unidad_cantidad
            )
        )
    return {
        "producto": db_producto,
        "ubicacion": punto_out
    }


@router.put("/productos/{id_producto}", response_model=ProductoOut)
def actualizar_producto(
    id_producto: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar productos")
    db_producto = get_producto_by_id(db, id_producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    cambios = {}
    if producto_update.nombre is not None:
        cambios["nombre"] = producto_update.nombre
    if producto_update.categoria is not None:
        cambios["categoria"] = producto_update.categoria
    if hasattr(producto_update, "codigo_unico") and producto_update.codigo_unico is not None:
        cambios["codigo_unico"] = producto_update.codigo_unico
    if not cambios:
        raise HTTPException(status_code=422, detail="No se proporcionaron campos válidos para actualizar")
    try:
        db_producto = update_producto(db, db_producto, **cambios)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return db_producto


@router.delete("/productos/{id_producto}", status_code=200)
def eliminar_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar productos.")
    db_producto = get_producto_by_id(db, id_producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto_vinculado_a_tareas_activas(db, id_producto, ESTADOS_ACTIVOS):
        raise HTTPException(
            status_code=409,
            detail="Este producto no puede ser eliminado porque está vinculado a tareas activas de reposición."
        )
    db_producto.estado = "inactivo"
    db.commit()
    return {"detail": "Producto eliminado correctamente (soft delete)."}


@router.delete("/productos/{id_producto}/desasignar-punto")
def desasignar_punto_de_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden desasignar productos de puntos.")
    try:
        punto = desasignar_punto_por_producto(db, id_producto)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "mensaje": "Producto desasignado del punto correctamente",
        "punto": {
            "id_punto": punto.id_punto,
            "id_mueble": punto.id_mueble,
            "nivel": punto.nivel,
            "estanteria": punto.estanteria,
            "producto": None
        }
    }


@router.put("/productos/{id_producto}/asignar-punto")
def asignar_punto_a_producto(
    id_producto: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden asociar productos a puntos.")
    id_punto = body.get("id_punto")
    if not id_punto:
        raise HTTPException(status_code=422, detail="El campo id_punto es obligatorio.")
    producto = get_producto_by_id(db, id_producto)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    try:
        punto = asignar_o_reasignar_producto_a_punto(db, id_producto, id_punto)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    # Obtener info de ubicación
    mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
    objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first() if mueble else None
    ubicacion = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).first() if objeto else None
    return {
        "mensaje": f"Producto '{producto.nombre}' asociado correctamente al punto {id_punto}.",
        "ubicacion": {
            "pasillo": objeto.nombre if objeto else None,
            "estanteria": punto.estanteria,
            "nivel": punto.nivel
        }
    }


@router.get("/productos/{id_producto}/ubicacion")
def obtener_ubicacion_de_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    producto = get_producto_by_id(db, id_producto)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    punto = obtener_ubicacion_producto(db, id_producto)
    if not punto:
        return {
            "producto": producto.nombre,
            "asignado": False,
            "mensaje": "Este producto aún no tiene una ubicación asignada."
        }
    mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
    objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first() if mueble else None
    return {
        "producto": producto.nombre,
        "asignado": True,
        "ubicacion": {
            "id_punto": punto.id_punto,
            "pasillo": objeto.nombre if objeto else None,
            "estanteria": punto.estanteria,
            "nivel": punto.nivel
        }
    }


from fastapi import Security
from fastapi.security import OAuth2PasswordBearer

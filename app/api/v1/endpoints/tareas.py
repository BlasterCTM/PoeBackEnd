# Endpoints para tareas y detalle de tarea

from fastapi import APIRouter, Depends, HTTPException, Body, status, Path, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.repositories.detalle_tarea import agregar_producto_a_detalle, eliminar_producto_de_detalle, listar_detalle_tarea
from app.repositories.tarea import tarea_repository
from app.models.producto import Producto
from app.schemas.tarea import TareaCreate, TareaResponse
from app.models.punto_reposicion import PuntoReposicion
from app.models.usuario import Usuario as UsuarioModel
from app.models.detalle_tarea import DetalleTarea
from app.models.producto import Producto as ProductoModel
from app.models.estado_tarea import EstadoTarea
from app.models.supervision import Supervision
from app.models.tarea import Tarea
from app.models.mueble_reposicion import MuebleReposicion
from app.models.objeto_mapa import ObjetoMapa
from app.models.ubicacion_fisica import UbicacionFisica
from datetime import date, datetime
from pydantic import BaseModel
from app.repositories.supervision import SupervisionRepository
import logging
from pytz import timezone
from fastapi import Query
from typing import Optional

router = APIRouter()
supervision_repository = SupervisionRepository()

@router.post("/tareas/{id_tarea}/detalle")
def agregar_producto_detalle(
    id_tarea: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    id_producto = body.get("id_producto")
    cantidad = body.get("cantidad")
    # Validación de campos requeridos y reglas de negocio
    if id_producto is None:
        raise HTTPException(status_code=422, detail=[{"loc": ["body", "id_producto"], "msg": "Campo requerido", "type": "value_error.missing"}])
    if cantidad is None:
        raise HTTPException(status_code=422, detail=[{"loc": ["body", "cantidad"], "msg": "Campo requerido", "type": "value_error.missing"}])
    if not isinstance(cantidad, int):
        raise HTTPException(status_code=422, detail="La cantidad debe ser un número entero.")
    if cantidad <= 0:
        raise HTTPException(status_code=422, detail="La cantidad debe ser mayor que 0.")
    try:
        detalle, producto = agregar_producto_a_detalle(db, id_tarea, id_producto, cantidad, current_user)
    except Exception as e:
        msg = str(e)
        if "ya está asignado" in msg:
            raise HTTPException(status_code=409, detail=msg)
        if "La cantidad debe ser mayor a cero." in msg:
            raise HTTPException(status_code=422, detail="La cantidad debe ser mayor que 0.")
        if "La tarea no existe." in msg or "El producto no existe." in msg:
            raise HTTPException(status_code=422, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return {
        "mensaje": "Producto agregado correctamente",
        "producto": producto.nombre,
        "cantidad": detalle.cantidad
    }

@router.delete("/tareas/{id_tarea}/detalle/{id_producto}")
def eliminar_producto_detalle(
    id_tarea: int,
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        eliminar_producto_de_detalle(db, id_tarea, id_producto, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mensaje": "Producto eliminado del detalle de la tarea."}

# @router.get("/tareas/{id_tarea}/detalle")
# def obtener_detalle_tarea(
#     id_tarea: int,
#     db: Session = Depends(get_db),
#     current_user: Usuario = Depends(get_current_user)
# ):
#     try:
#         detalles = listar_detalle_tarea(db, id_tarea, current_user)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     productos = db.query(Producto).all()
#     productos_dict = {p.id_producto: p.nombre for p in productos}
#     return [
#         {
#             "id_producto": d.id_producto,
#             "nombre_producto": productos_dict.get(d.id_producto, ""),
#             "cantidad": d.cantidad
#         } for d in detalles
#     ]

@router.post("/tareas", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    tarea_data: TareaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar permisos
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores o supervisores pueden crear tareas."
        )

    # Validar puntos (ya validado por el esquema, pero doble check)
    if not tarea_data.puntos or len(tarea_data.puntos) == 0:
        raise HTTPException(status_code=422, detail="Debe incluir al menos un punto de reposición para la tarea.")
    ids = [p.id_punto for p in tarea_data.puntos]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="No se permiten puntos de reposición repetidos en la tarea.")
    for p in tarea_data.puntos:
        if p.cantidad <= 0:
            raise HTTPException(status_code=422, detail="Las cantidades deben ser mayores a 0.")

    # Validar reponedor solo si se envía
    reponedor = None
    if tarea_data.id_reponedor is not None:
        reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea_data.id_reponedor).first()
        if not reponedor or reponedor.rol.nombre_rol.lower() != "reponedor":
            raise HTTPException(status_code=422, detail="El reponedor no existe o no tiene el rol correcto.")

    # Asignar supervisor correctamente según el rol
    if current_user.rol.nombre_rol.lower() == "supervisor":
        id_supervisor = current_user.id_usuario
        # Si se asigna reponedor, validar que esté bajo su supervisión
        if tarea_data.id_reponedor is not None:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == tarea_data.id_reponedor,
                Supervision.supervisor_id == current_user.id_usuario
            ).first()
            if not supervision:
                raise HTTPException(status_code=403, detail="No tienes permisos para asignar tareas a este reponedor.")
    else:
        if not hasattr(tarea_data, "id_supervisor") or tarea_data.id_supervisor is None:
            raise HTTPException(status_code=422, detail="Los administradores deben proporcionar un ID de supervisor al crear una tarea.")
        id_supervisor = tarea_data.id_supervisor

    # Crear la tarea principal
    tarea = Tarea(
        fecha_creacion=date.today(),
        estado_id=tarea_data.estado_id,
        id_supervisor=id_supervisor,
        id_reponedor=tarea_data.id_reponedor
    )
    db.add(tarea)
    db.commit()
    db.refresh(tarea)

    # Crear detalles de tarea
    detalles = []
    for punto in tarea_data.puntos:
        punto_db = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == punto.id_punto).first()
        if not punto_db:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"El punto de reposición con id {punto.id_punto} no existe.")
        if not punto_db.id_producto:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"El punto de reposición {punto.id_punto} no tiene producto asignado.")
        producto = db.query(ProductoModel).filter(ProductoModel.id_producto == punto_db.id_producto).first()
        if not producto:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"El producto con id {punto_db.id_producto} no existe.")
        detalle = DetalleTarea(
            id_tarea=tarea.id_tarea,
            id_producto=punto_db.id_producto,
            cantidad=punto.cantidad,
            id_punto=punto.id_punto
        )
        db.add(detalle)
        detalles.append({
            "id_producto": producto.id_producto,
            "nombre_producto": producto.nombre,
            "cantidad": punto.cantidad,
            "id_punto": punto.id_punto
        })
    db.commit()

    # Obtener estado
    estado = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    estado_nombre = estado.nombre_estado if estado else ""

    return {
        "mensaje": "Tarea creada exitosamente",
        "tarea": {
            "id_tarea": tarea.id_tarea,
            "fecha_creacion": str(tarea.fecha_creacion),
            "estado": estado_nombre,
            "id_supervisor": id_supervisor,
            "id_reponedor": tarea.id_reponedor,
            "detalle": detalles
        },
        "asignada": tarea.id_reponedor is not None
    }

class AsignarReponedorRequest(BaseModel):
    id_reponedor: int

@router.put("/tareas/{id_tarea}/asignar-reponedor", status_code=200)
def asignar_reponedor_a_tarea(
    id_tarea: int = Path(..., description="ID de la tarea a asignar"),
    body: AsignarReponedorRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    # Permitir dejar la tarea sin asignar
    if not hasattr(body, 'id_reponedor') or body.id_reponedor is None:
        tarea.id_reponedor = None
        estado_sin_asignar = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == "sin asignar").first()
        if estado_sin_asignar:
            tarea.estado_id = estado_sin_asignar.estado_id
        db.commit()
        db.refresh(tarea)
        return {
            "mensaje": "Tarea dejada sin asignar.",
            "tarea": {
                "id": tarea.id_tarea,
                "estado": "sin asignar",
                "reponedor": None
            }
        }

    # Validar que el reponedor existe, es rol correcto y está activo
    reponedor = db.query(Usuario).filter(Usuario.id_usuario == body.id_reponedor).first()
    if not reponedor or reponedor.rol.nombre_rol != RolEnum.REPONEDOR.value:
        raise HTTPException(status_code=422, detail="El usuario no es un reponedor válido.")
    if reponedor.estado != "activo":
        raise HTTPException(status_code=422, detail="El reponedor no está disponible (no activo).")

    # Validar autoridad del supervisor
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value:
        supervision = db.query(Supervision).filter(
            Supervision.supervisor_id == current_user.id_usuario,
            Supervision.reponedor_id == reponedor.id_usuario
        ).first()
        if not supervision:
            raise HTTPException(status_code=403, detail="No tienes autoridad sobre este reponedor.")

    # Validar tareas activas del reponedor
    estados_activos = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.in_(["pendiente", "en progreso"]))
    ids_estados = [e.estado_id for e in estados_activos]
    tarea_activa = db.query(Tarea).filter(
        Tarea.id_reponedor == reponedor.id_usuario,
        Tarea.estado_id.in_(ids_estados)
    ).first()
    if tarea_activa:
        raise HTTPException(
            status_code=409,
            detail=f"El reponedor ya tiene una tarea en curso (ID: {tarea_activa.id_tarea}). Asigne a otro usuario o espere a que finalice."
        )

    # Asignar reponedor y cambiar estado a 'pendiente'
    tarea.id_reponedor = reponedor.id_usuario
    estado_pendiente = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == "pendiente").first()
    if estado_pendiente:
        tarea.estado_id = estado_pendiente.estado_id
    db.commit()
    db.refresh(tarea)
    return {
        "mensaje": f"Tarea asignada correctamente a {reponedor.nombre}.",
        "tarea": {
            "id": tarea.id_tarea,
            "estado": "pendiente",
            "reponedor": reponedor.nombre
        }
    }

@router.get("/tareas/disponibles", response_model=list[TareaResponse])
def listar_tareas_disponibles(db: Session = Depends(get_db)):
    # Estados considerados como "disponibles" (sin asignar o pendiente)
    estados_disponibles = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.in_(["sin asignar", "pendiente"]))
    ids_estados = [e.estado_id for e in estados_disponibles]
    tareas = db.query(Tarea).filter(Tarea.estado_id.in_(ids_estados)).all()
    return tareas

@router.get("/tareas/asignadas", response_model=list[TareaResponse])
def listar_tareas_asignadas(db: Session = Depends(get_db)):
    # Buscar tareas con reponedor asignado (id_reponedor no nulo)
    tareas = db.query(Tarea).filter(Tarea.id_reponedor.isnot(None)).all()
    return tareas

@router.get("/tareas/no-asignadas", response_model=list[TareaResponse])
def listar_tareas_no_asignadas(db: Session = Depends(get_db)):
    # Buscar tareas sin reponedor asignado (id_reponedor es nulo)
    tareas = db.query(Tarea).filter(Tarea.id_reponedor.is_(None)).all()
    return tareas

@router.get("/tareas/supervisor")
def listar_tareas_supervisor(
    estado: str = Query(None, description="Filtrar por estado de tarea (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol != RolEnum.SUPERVISOR.value:
        raise HTTPException(status_code=403, detail="Solo los supervisores pueden acceder a este recurso.")
    query = db.query(Tarea).options(
        joinedload(Tarea.detalles)
    ).filter(Tarea.id_supervisor == current_user.id_usuario)
    if estado:
        estado_obj = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == estado).first()
        if not estado_obj:
            raise HTTPException(status_code=422, detail="Estado no válido.")
        query = query.filter(Tarea.estado_id == estado_obj.estado_id)
    tareas = query.all()
    colores_estado = {
        "pendiente": "#f1c40f",
        "en progreso": "#3498db",
        "completada": "#2ecc71",
        "cancelada": "#e74c3c",
        "sin asignar": "#95a5a6"
    }
    resultado = []
    for tarea in tareas:
        estado_nombre = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first().nombre_estado
        reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
        detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == tarea.id_tarea).all()
        productos = []
        ubicaciones = []
        for d in detalles:
            prod = db.query(Producto).filter(Producto.id_producto == d.id_producto).first()
            punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == d.id_punto).first()
            productos.append({
                "id_producto": prod.id_producto,
                "nombre": prod.nombre if prod else None,
                "cantidad": d.cantidad,
                "ubicacion": {
                    "estanteria": punto.estanteria if punto else None,
                    "nivel": punto.nivel if punto else None
                }
            })
            ubicaciones.append({
                "estanteria": punto.estanteria if punto else None,
                "nivel": punto.nivel if punto else None
            })
        resultado.append({
            "id_tarea": tarea.id_tarea,
            "estado": estado_nombre,
            "color_estado": colores_estado.get(estado_nombre, "#bdc3c7"),
            "reponedor": reponedor.nombre if reponedor else None,
            "productos": productos,
            "ubicaciones": ubicaciones,
            "fecha_creacion": str(tarea.fecha_creacion)
        })
    return resultado

@router.get("/tareas/reponedor")
def listar_tareas_reponedor(
    estado: str = Query(None, description="Filtrar por estado de tarea (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol != RolEnum.REPONEDOR.value:
        raise HTTPException(status_code=403, detail="Solo reponedores pueden acceder a esta vista.")
    query = db.query(Tarea).join(EstadoTarea).filter(Tarea.id_reponedor == current_user.id_usuario)
    if estado:
        query = query.filter(EstadoTarea.nombre_estado.ilike(estado))
    tareas = query.all()
    resultado = []
    for tarea in tareas:
        estado_nombre = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first().nombre_estado
        detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == tarea.id_tarea).all()
        productos = []
        for d in detalles:
            prod = db.query(Producto).filter(Producto.id_producto == d.id_producto).first()
            punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == d.id_punto).first()
            productos.append({
                "nombre": prod.nombre if prod else None,
                "cantidad": d.cantidad,
                "ubicacion": {
                    "estanteria": punto.estanteria if punto else None,
                    "nivel": punto.nivel if punto else None
                }
            })
        resultado.append({
            "id_tarea": tarea.id_tarea,
            "estado": estado_nombre,
            "fecha_creacion": str(tarea.fecha_creacion),
            "productos": productos
        })
    return resultado

@router.get("/tareas/{id_tarea}")
def detalle_tarea(
    id_tarea: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value and tarea.id_supervisor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea.")
    estado_nombre = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first().nombre_estado
    reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == tarea.id_tarea).all()
    productos = []
    for d in detalles:
        prod = db.query(Producto).filter(Producto.id_producto == d.id_producto).first()
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == d.id_punto).first()
        productos.append({
            "nombre": prod.nombre if prod else None,
            "cantidad": d.cantidad,
            "ubicacion": {
                "estanteria": punto.estanteria if punto else None,
                "nivel": punto.nivel if punto else None
            }
        })
    return {
        "id_tarea": tarea.id_tarea,
        "estado": estado_nombre,
        "reponedor": reponedor.nombre if reponedor else None,
        "fecha_creacion": str(tarea.fecha_creacion),
        "productos": productos
    }

class ReemplazoProductoRequest(BaseModel):
    id_producto_actual: int
    id_producto_nuevo: int
    cantidad: int

@router.put("/tareas/{id_tarea}/detalle/reemplazar")
def reemplazar_producto_detalle(
    id_tarea: int,
    body: ReemplazoProductoRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validar cantidad
    if body.cantidad <= 0:
        raise HTTPException(status_code=422, detail="La cantidad debe ser mayor a 0.")
    # Eliminar producto actual
    detalle_actual = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_producto == body.id_producto_actual).first()
    if not detalle_actual:
        raise HTTPException(status_code=404, detail="El producto actual no está en el detalle de la tarea.")
    # Validar permisos (igual que en agregar/eliminar)
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="La tarea no existe.")
    if current_user.rol.nombre_rol.lower() == "supervisor":
        supervision = db.query(Supervision).filter(Supervision.reponedor_id == tarea.id_reponedor, Supervision.supervisor_id == current_user.id_usuario).first()
        if not supervision:
            raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta tarea.")
    elif current_user.rol.nombre_rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar tareas.")
    db.delete(detalle_actual)
    db.commit()
    # Validar que el nuevo producto no esté ya en la tarea
    existe = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_producto == body.id_producto_nuevo).first()
    if existe:
        raise HTTPException(status_code=409, detail="El producto nuevo ya está asignado a la tarea.")
    # Agregar el nuevo producto
    nuevo_detalle = DetalleTarea(id_tarea=id_tarea, id_producto=body.id_producto_nuevo, cantidad=body.cantidad)
    db.add(nuevo_detalle)
    db.commit()
    producto_nuevo = db.query(Producto).filter(Producto.id_producto == body.id_producto_nuevo).first()
    return {
        "mensaje": "Producto reemplazado correctamente.",
        "producto": producto_nuevo.nombre if producto_nuevo else None,
        "nueva_cantidad": body.cantidad
    }

@router.put("/tareas/{id_tarea}/detalle/{id_producto}")
def actualizar_cantidad_producto_detalle(
    id_tarea: int,
    id_producto: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cantidad = body.get("cantidad")
    if cantidad is None or not isinstance(cantidad, int) or cantidad <= 0:
        raise HTTPException(status_code=422, detail="La cantidad debe ser un número entero mayor a 0.")
    detalle = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_producto == id_producto).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="El producto no está en el detalle de la tarea.")
    # Validar permisos (igual que en agregar/eliminar)
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="La tarea no existe.")
    if current_user.rol.nombre_rol.lower() == "supervisor":
        supervision = db.query(Supervision).filter(Supervision.reponedor_id == tarea.id_reponedor, Supervision.supervisor_id == current_user.id_usuario).first()
        if not supervision:
            raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta tarea.")
    elif current_user.rol.nombre_rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar tareas.")
    detalle.cantidad = cantidad
    db.commit()
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    return {
        "mensaje": "Cantidad actualizada correctamente.",
        "producto": producto.nombre if producto else None,
        "nueva_cantidad": cantidad
    }

@router.put("/tareas/{id_tarea}/cancelar")
def cancelar_tarea(
    id_tarea: int,
    body: dict = Body(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    # Solo supervisor creador o admin
    if current_user.rol.nombre_rol.lower() == "supervisor" and tarea.id_supervisor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permisos para cancelar esta tarea.")
    elif current_user.rol.nombre_rol.lower() not in ["supervisor", "administrador"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para cancelar tareas.")
    # Solo si está pendiente o en progreso
    estado = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    if estado.nombre_estado not in ["pendiente", "en progreso"]:
        raise HTTPException(status_code=409, detail="No se puede cancelar esta tarea porque ya está completada o fue cancelada anteriormente.")
    estado_cancelada = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == "cancelada").first()
    if not estado_cancelada:
        raise HTTPException(status_code=500, detail="No se encontró el estado 'cancelada' en la base de datos.")
    tarea.estado_id = estado_cancelada.estado_id
    db.commit()
    return {
        "mensaje": "Tarea cancelada correctamente.",
        "estado": "cancelada",
        "id_tarea": tarea.id_tarea
    }

@router.put("/tareas/{id_tarea}/completar", status_code=200)
def completar_tarea(
    id_tarea: int,
    confirmado: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Buscar tarea
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    # Validar usuario reponedor asignado
    if current_user.rol.nombre_rol.lower() != "reponedor" or int(tarea.id_reponedor) != int(current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo el reponedor asignado puede completar esta tarea.")
    # Buscar estados válidos
    estado_pendiente = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.ilike("pendiente")).first()
    estado_en_progreso = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.ilike("en_progreso")).first()
    estado_completada = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.ilike("completada")).first()
    if not estado_completada:
        raise HTTPException(status_code=500, detail="No existe el estado 'completada' en la base de datos.")
    # Validar estado actual
    if tarea.estado_id not in [estado_pendiente.estado_id if estado_pendiente else -1, estado_en_progreso.estado_id if estado_en_progreso else -1]:
        raise HTTPException(status_code=400, detail="La tarea ya fue completada previamente o no está activa.")
    # Confirmación explícita
    if not confirmado:
        raise HTTPException(status_code=400, detail="Se requiere confirmación para completar la tarea.")
    # Actualizar tarea
    tz_utc = timezone("UTC")
    tz_chile = timezone("America/Santiago")
    ahora_utc = datetime.now(tz_utc)
    tarea.estado_id = estado_completada.estado_id
    tarea.fecha_hora_completada = ahora_utc
    db.commit()
    db.refresh(tarea)
    fecha_local = tarea.fecha_hora_completada.astimezone(tz_chile)
    return {
        "mensaje": "La tarea fue marcada como completada exitosamente.",
        "estado": "completada",
        "fecha_completada": fecha_local.isoformat()
    }

@router.get("/tareas/{id_tarea}/detalle")
def detalle_tarea_reponedor(
    id_tarea: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    # Comparar id_reponedor como int para evitar problemas de tipo y loguear
    try:
        id_usuario = int(current_user.id_usuario)
    except Exception:
        id_usuario = current_user.id_usuario
    logging.warning(f"DETALLE_TAREA_DEBUG: tarea.id_reponedor={tarea.id_reponedor} (type={type(tarea.id_reponedor)}), usuario={id_usuario} (type={type(id_usuario)})")
    if current_user.rol.nombre_rol != RolEnum.REPONEDOR.value:
        raise HTTPException(status_code=403, detail="Solo reponedores pueden acceder a esta tarea.")
    if int(tarea.id_reponedor) != int(id_usuario):
        raise HTTPException(status_code=403, detail=f"No tienes acceso a esta tarea. (id_reponedor={tarea.id_reponedor}, usuario={id_usuario})")
    estado_nombre = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first().nombre_estado
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == tarea.id_tarea).all()
    productos = []
    for d in detalles:
        prod = db.query(Producto).filter(Producto.id_producto == d.id_producto).first()
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == d.id_punto).first() if d.id_punto else None
        mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first() if punto and punto.id_mueble else None
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first() if mueble and mueble.id_objeto else None
        ubicacion = None
        if objeto:
            ubicacion_fisica = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).first()
            if ubicacion_fisica:
                ubicacion = {
                    "pasillo": ubicacion_fisica.x,
                    "estanteria": punto.estanteria if punto else None,
                    "nivel": punto.nivel if punto else None
                }
        productos.append({
            "nombre": prod.nombre if prod else None,
            "cantidad": d.cantidad,
            "ubicacion": ubicacion or {
                "pasillo": None,
                "estanteria": punto.estanteria if punto else None,
                "nivel": punto.nivel if punto else None
            }
        })
    return {
        "id_tarea": tarea.id_tarea,
        "estado": estado_nombre,
        "fecha_creacion": str(tarea.fecha_creacion),
        "productos": productos
    }

@router.get("/tareas/{id_tarea}/detalle-simple")
def obtener_detalle_tarea_simple(
    id_tarea: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        detalles = listar_detalle_tarea(db, id_tarea, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    productos = db.query(Producto).all()
    productos_dict = {p.id_producto: p.nombre for p in productos}
    return [
        {
            "id_producto": d.id_producto,
            "nombre_producto": productos_dict.get(d.id_producto, ""),
            "cantidad": d.cantidad
        } for d in detalles
    ]

@router.get("/productos/{id_producto}/historial")
def historial_reposiciones_producto(
    id_producto: int,
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cantidad_min: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validar rol
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden consultar el historial.")
    # Validar producto
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    # Query historial (ORM)
    query = db.query(DetalleTarea.cantidad, Tarea.fecha_creacion, Tarea.id_tarea)
    query = query.join(Tarea, DetalleTarea.id_tarea == Tarea.id_tarea)
    query = query.filter(DetalleTarea.id_producto == id_producto)
    if fecha_inicio:
        query = query.filter(Tarea.fecha_creacion >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Tarea.fecha_creacion <= fecha_fin)
    if cantidad_min:
        query = query.filter(DetalleTarea.cantidad >= cantidad_min)
    historial = query.order_by(Tarea.fecha_creacion.desc()).all()
    if not historial:
        return {
            "producto": producto.nombre,
            "historial": [],
            "mensaje": "Este producto aún no ha sido repuesto."
        }
    total_reposiciones = len(historial)
    cantidad_total_repuesta = sum([h.cantidad for h in historial])
    return {
        "producto": producto.nombre,
        "historial": [
            {"fecha": str(h.fecha_creacion), "cantidad": h.cantidad, "tarea_id": h.id_tarea} for h in historial
        ],
        "total_reposiciones": total_reposiciones,
        "cantidad_total_repuesta": cantidad_total_repuesta
    }

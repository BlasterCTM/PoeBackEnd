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
from datetime import date
from pydantic import BaseModel
from app.repositories.supervision import SupervisionRepository

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

@router.get("/tareas/{id_tarea}/detalle")
def obtener_detalle_tarea(
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

    # Validar productos (ya validado por el esquema, pero doble check)
    if not tarea_data.productos or len(tarea_data.productos) == 0:
        raise HTTPException(status_code=422, detail="Debe incluir al menos un producto para la tarea.")
    ids = [p.id_producto for p in tarea_data.productos]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="No se permiten productos repetidos en la tarea.")
    for p in tarea_data.productos:
        if p.cantidad <= 0:
            raise HTTPException(status_code=422, detail="Las cantidades deben ser mayores a 0.")

    # Validar punto de reposición
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == tarea_data.id_punto).first()
    if not punto:
        raise HTTPException(status_code=422, detail="El punto de reposición no existe.")

    # Validar reponedor solo si se envía
    reponedor = None
    if tarea_data.id_reponedor is not None:
        reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea_data.id_reponedor).first()
        if not reponedor or reponedor.rol.nombre_rol.lower() != "reponedor":
            raise HTTPException(status_code=422, detail="El reponedor no existe o no tiene el rol correcto.")

    # Si supervisor, validar que el reponedor esté asignado a él
    if current_user.rol.nombre_rol.lower() == "supervisor" and tarea_data.id_reponedor is not None:
        supervision = db.query(Supervision).filter(
            Supervision.reponedor_id == tarea_data.id_reponedor,
            Supervision.supervisor_id == current_user.id_usuario
        ).first()
        if not supervision:
            raise HTTPException(status_code=403, detail="No tienes permisos para asignar tareas a este reponedor.")
        id_supervisor = current_user.id_usuario
    else:
        if not tarea_data.id_supervisor:
            raise HTTPException(status_code=422, detail="Los administradores deben proporcionar un ID de supervisor al crear una tarea.")
        id_supervisor = tarea_data.id_supervisor

    # Validar que el punto no esté ocupado por una tarea activa
    estados_bloqueo = ["pendiente", "en progreso"]
    resultado = db.query(Tarea, EstadoTarea, UsuarioModel).\
        join(EstadoTarea, Tarea.estado_id == EstadoTarea.estado_id).\
        join(UsuarioModel, Tarea.id_reponedor == UsuarioModel.id_usuario, isouter=True).\
        filter(
            Tarea.id_punto == tarea_data.id_punto,
            EstadoTarea.nombre_estado.in_(estados_bloqueo)
        ).first()
    if resultado:
        tarea_conflictiva, estado, reponedor_conflictivo = resultado
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "Conflicto: El punto ya está en uso por otra tarea activa.",
                "tarea_conflictiva": {
                    "id_tarea": tarea_conflictiva.id_tarea,
                    "estado": estado.nombre_estado,
                    "reponedor": reponedor_conflictivo.nombre if reponedor_conflictivo else None
                }
            }
        )

    # Crear la tarea
    if tarea_data.id_reponedor is None:
        estado_inicial = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == "sin asignar").first()
        if not estado_inicial:
            raise HTTPException(status_code=500, detail="No existe el estado 'sin asignar' en la base de datos.")
        estado_id = estado_inicial.estado_id
    else:
        estado_id = 1  # pendiente
    tarea = Tarea(
        fecha_creacion=date.today(),
        estado_id=estado_id,
        id_supervisor=id_supervisor,
        id_reponedor=tarea_data.id_reponedor,
        id_punto=tarea_data.id_punto
    )
    db.add(tarea)
    db.commit()
    db.refresh(tarea)

    # Crear detalles de tarea
    detalles = []
    for prod in tarea_data.productos:
        producto = db.query(ProductoModel).filter(ProductoModel.id_producto == prod.id_producto).first()
        if not producto:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"El producto con id {prod.id_producto} no existe.")
        detalle = DetalleTarea(id_tarea=tarea.id_tarea, id_producto=prod.id_producto, cantidad=prod.cantidad)
        db.add(detalle)
        detalles.append({
            "producto": producto.nombre,
            "cantidad": prod.cantidad
        })
    db.commit()

    # Obtener estado
    estado = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    estado_nombre = estado.nombre_estado if estado else ""

    # Obtener info de punto
    punto_dict = {
        "pasillo": str(getattr(punto, "pasillo", "")),
        "estanteria": str(getattr(punto, "estanteria", "")),
        "nivel": getattr(punto, "nivel", None)
    }

    # Respuesta diferenciada
    if tarea_data.id_reponedor is None:
        return {
            "mensaje": "Tarea creada sin reponedor.",
            "id_tarea": tarea.id_tarea,
            "estado": estado_nombre,
            "reponedor": None,
            "asignada": False
        }
    else:
        reponedor_nombre = reponedor.nombre if reponedor else None
        return {
            "mensaje": "Tarea creada exitosamente",
            "tarea": {
                "id_tarea": tarea.id_tarea,
                "fecha_creacion": str(tarea.fecha_creacion),
                "estado": estado_nombre,
                "reponedor": reponedor_nombre,
                "punto_reposicion": punto_dict,
                "detalle": detalles
            },
            "asignada": True
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
    # Diccionario de colores por estado
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
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == tarea.id_punto).first()
        # Generar nombre de la tarea
        nombre_tarea = f"Reposición estantería {punto.estanteria if punto else '-'} nivel {punto.nivel if punto else '-'}"
        resultado.append({
            "id_tarea": tarea.id_tarea,
            "nombre": nombre_tarea,
            "estado": estado_nombre,
            "color_estado": colores_estado.get(estado_nombre, "#bdc3c7"),
            "reponedor": reponedor.nombre if reponedor else None,
            "punto_reposicion": {
                "estanteria": punto.estanteria if punto else None,
                "nivel": punto.nivel if punto else None
            },
            "fecha_creacion": str(tarea.fecha_creacion)
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
    # Seguridad: solo el supervisor creador o admin puede ver
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value and tarea.id_supervisor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea.")
    # Respuesta enriquecida
    estado_nombre = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first().nombre_estado
    reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == tarea.id_punto).first()
    return {
        "id_tarea": tarea.id_tarea,
        "estado": estado_nombre,
        "reponedor": reponedor.nombre if reponedor else None,
        "punto_reposicion": {
            "estanteria": punto.estanteria if punto else None,
            "nivel": punto.nivel if punto else None
        },
        "fecha_creacion": str(tarea.fecha_creacion),
        "detalles": [
            {
                "id_producto": d.id_producto,
                "cantidad": d.cantidad
            } for d in tarea.detalles
        ]
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

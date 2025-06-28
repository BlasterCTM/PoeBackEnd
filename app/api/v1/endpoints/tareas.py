
from app.models.usuario import Usuario, RolEnum
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user

# Definir el router principal después de los imports
router = APIRouter()

@router.put("/detalles-tarea/{id_detalle}/completar", status_code=200)
def completar_detalle_tarea(
    id_detalle: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Buscar el detalle de tarea
    detalle = db.query(DetalleTarea).filter(DetalleTarea.id_detalle == id_detalle).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle de tarea no encontrado.")
    # Buscar la tarea asociada
    tarea = db.query(Tarea).filter(Tarea.id_tarea == detalle.id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea asociada no encontrada.")
    # Validar usuario reponedor asignado
    if current_user.rol.nombre_rol.lower() != "reponedor" or int(tarea.id_reponedor) != int(current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo el reponedor asignado puede completar este detalle de tarea.")
    # Buscar estado 'completada'
    estado_completada = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado.ilike("completada")).first()
    if not estado_completada:
        raise HTTPException(status_code=500, detail="No existe el estado 'completada' en la base de datos.")
    # Validar estado actual
    if detalle.estado_id == estado_completada.estado_id:
        raise HTTPException(status_code=400, detail="El detalle de tarea ya fue completado previamente.")
    # Actualizar estado
    detalle.estado_id = estado_completada.estado_id
    db.commit()
    db.refresh(detalle)
    return {
        "mensaje": "Detalle de tarea marcado como completado exitosamente.",
        "id_detalle": detalle.id_detalle,
        "estado": "completada"
    }
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
from app.schemas.ruta_optimizada import (
    RutaOptimizadaResponse, 
    PuntoRutaResponse, 
    MuebleRutaResponse, 
    ProductoRutaResponse, 
    CoordenadaResponse, 
    AlgoritmoResponse,
    ErrorRutaResponse
)
from app.repositories.ruta import calcular_ruta, generar_grafo
from app.models.mapa import Mapa
from app.models.objeto_tipo import ObjetoTipo
import random
import itertools

supervision_repository = SupervisionRepository()

def encontrar_punto_accesible(coordenada_mueble: tuple, coordenadas_caminables: set) -> tuple:
    """
    Encuentra el punto caminable más cercano a las coordenadas del mueble.
    Prioriza las 8 casillas adyacentes directas al mueble.
    """
    x, y = coordenada_mueble
    
    # VERIFICACIÓN: Si el mueble mismo es caminable, NO usarlo (es un error)
    if coordenada_mueble in coordenadas_caminables:
        print(f"WARNING: Mueble en {coordenada_mueble} está marcado como caminable, esto es incorrecto")
        # No devolver la coordenada del mueble aunque esté en coordenadas_caminables
    
    # Primero: buscar en las 8 casillas adyacentes directas (prioridad alta)
    direcciones_adyacentes = [
        (0, 1), (0, -1), (1, 0), (-1, 0),  # arriba, abajo, derecha, izquierda
        (1, 1), (1, -1), (-1, 1), (-1, -1)  # diagonales
    ]
    
    for dx, dy in direcciones_adyacentes:
        punto_candidato = (x + dx, y + dy)
        if punto_candidato in coordenadas_caminables and punto_candidato != coordenada_mueble:
            print(f"Punto accesible encontrado para mueble {coordenada_mueble}: {punto_candidato}")
            return punto_candidato
    
    # Segundo: si no hay casillas adyacentes caminables, buscar en círculos concéntricos
    for radio in range(2, 8):  # Buscar hasta 7 unidades de distancia
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                # Solo puntos en el borde del círculo actual
                if abs(dx) == radio or abs(dy) == radio:
                    punto_candidato = (x + dx, y + dy)
                    if punto_candidato in coordenadas_caminables and punto_candidato != coordenada_mueble:
                        print(f"Punto accesible encontrado (radio {radio}) para mueble {coordenada_mueble}: {punto_candidato}")
                        return punto_candidato
    
    # Si no encuentra ningún punto cercano, usar una coordenada por defecto (0,0) o la más cercana al origen
    print(f"ERROR: No se encontró punto accesible para mueble {coordenada_mueble}, usando (0,0)")
    return (0, 0)  # En lugar de devolver la coordenada del mueble

def encontrar_punto_accesible_cruz(coordenada_mueble: tuple, coordenadas_caminables: set) -> tuple:
    """
    Busca SOLO en cruz (arriba, abajo, izquierda, derecha) el punto caminable más cercano al mueble.
    """
    x, y = coordenada_mueble
    direcciones_cruz = [
        (0, 1), (0, -1), (1, 0), (-1, 0)  # arriba, abajo, derecha, izquierda
    ]
    for dx, dy in direcciones_cruz:
        punto_candidato = (x + dx, y + dy)
        if punto_candidato in coordenadas_caminables:
            return punto_candidato
    # Si no hay adyacente en cruz, busca en círculos concéntricos solo en cruz
    for radio in range(2, 8):
        for dx, dy in direcciones_cruz:
            punto_candidato = (x + dx * radio, y + dy * radio)
            if punto_candidato in coordenadas_caminables:
                return punto_candidato
    # Si no encuentra, retorna (0,0) o lanza error
    return (0, 0)

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
            "id_producto": prod.id_producto,
            "nombre": prod.nombre if prod else None,
            "cantidad": d.cantidad,
            "ubicacion": {
                "id_punto": punto.id_punto if punto else None,
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

@router.put("/tareas/{id_tarea}/detalle/{id_punto}")
def actualizar_cantidad_producto_detalle(
    id_tarea: int,
    id_punto: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cantidad = body.get("cantidad")
    if cantidad is None or not isinstance(cantidad, int) or cantidad <= 0:
        raise HTTPException(status_code=422, detail="La cantidad debe ser un número entero mayor a 0.")
    detalle = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_punto == id_punto).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="El punto de reposición no está en el detalle de la tarea.")
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
    return {
        "mensaje": "Cantidad actualizada correctamente.",
        "id_punto": id_punto,
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
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == d.id_punto).first()
        productos.append({
            "id_producto": prod.id_producto,
            "nombre": prod.nombre if prod else None,
            "cantidad": d.cantidad,
            "ubicacion": {
                "id_punto": punto.id_punto if punto else None,
                "estanteria": punto.estanteria if punto else None,
                "nivel": punto.nivel if punto else None
            }
        })
    # Obtener reponedor para la respuesta
    reponedor_obj = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first() if tarea.id_reponedor else None
    return {
        "id_tarea": tarea.id_tarea,
        "estado": estado_nombre,
        "reponedor": reponedor_obj.nombre if reponedor_obj else None,
        "fecha_creacion": str(tarea.fecha_creacion),
        "productos": productos
    }

@router.get("/tareas/{id_tarea}/ruta-optimizada", response_model=RutaOptimizadaResponse)
def obtener_ruta_optimizada_tarea(
    id_tarea: int,
    algoritmo: str = Query("vecino_mas_cercano", description="Algoritmo a utilizar: 'vecino_mas_cercano', 'fuerza_bruta', 'genetico'"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la ruta optimizada de reposición para una tarea específica.
    
    Retorna información detallada sobre:
    - Puntos de reposición ordenados por ruta óptima
    - Coordenadas completas de la ruta en el mapa
    - Información de muebles y productos
    - Distancia total y algoritmo utilizado
    """
    # Validar algoritmo seleccionado
    algoritmos_disponibles = {
        "vecino_mas_cercano": algoritmo_vecino_mas_cercano,
        "fuerza_bruta": algoritmo_fuerza_bruta,
        "genetico": algoritmo_genetico
    }
    
    if algoritmo not in algoritmos_disponibles:
        raise HTTPException(
            status_code=400,
            detail=f"Algoritmo '{algoritmo}' no válido. Algoritmos disponibles: {list(algoritmos_disponibles.keys())}"
        )
    
    # Validar que la tarea existe
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Validar permisos de acceso
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value and tarea.id_supervisor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
    elif current_user.rol.nombre_rol == RolEnum.REPONEDOR.value and tarea.id_reponedor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
    
    # Obtener información de reponedor y estado
    reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
    if not reponedor:
        raise HTTPException(status_code=400, detail="La tarea no tiene reponedor asignado")
    
    estado = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    estado_nombre = estado.nombre_estado if estado else "Desconocido"
    
    # Obtener detalles de la tarea
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea).all()
    if not detalles:
        raise HTTPException(status_code=400, detail="La tarea no tiene productos asignados")
    
    # Obtener el mapa y generar grafo de coordenadas caminables
    mapa = db.query(Mapa).first()
    if not mapa:
        raise HTTPException(status_code=500, detail="No hay mapas configurados en el sistema")
    
    coordenadas_caminables = generar_grafo(db, mapa.id_mapa)

    # FILTRAR explícitamente TODAS las coordenadas de los muebles del set de caminables
    # Un mueble puede ocupar varias ubicaciones físicas
    ubicaciones_muebles = db.query(UbicacionFisica).join(ObjetoMapa).join(ObjetoTipo).filter(ObjetoTipo.nombre_tipo == "mueble").all()
    muebles_coords = set((ubic.x, ubic.y) for ubic in ubicaciones_muebles)
    coordenadas_caminables -= muebles_coords

    # Procesar cada punto de reposición
    puntos_info = []
    coordenadas_puntos = []
    
    for detalle in detalles:
        # Obtener punto de reposición
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == detalle.id_punto).first()
        if not punto:
            continue
        # Obtener mueble
        mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
        if not mueble:
            continue
        # Obtener objeto del mapa
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first()
        if not objeto:
            continue
        # Obtener TODAS las ubicaciones físicas del mueble (puede ocupar varias casillas)
        ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).all()
        if not ubicaciones:
            continue
        # Obtener producto
        producto = db.query(Producto).filter(Producto.id_producto == detalle.id_producto).first()
        if not producto:
            continue
        # Para la lógica de ruta, buscar un punto accesible en cruz a CUALQUIERA de las posiciones del mueble
        coordenada_accesible = None
        for ubic in ubicaciones:
            c = encontrar_punto_accesible_cruz((ubic.x, ubic.y), coordenadas_caminables)
            if c != (0, 0):
                coordenada_accesible = c
                break
        if not coordenada_accesible:
            # Si no se encontró, usar (0,0) como fallback
            coordenada_accesible = (0, 0)
        coordenadas_puntos.append(coordenada_accesible)
        # Para mostrar, incluir SOLO UNA coordenada del mueble (la primera) para compatibilidad con el schema actual
        coordenada_display = CoordenadaResponse(x=ubicaciones[0].x, y=ubicaciones[0].y)
        mueble_info = MuebleRutaResponse(
            id_mueble=mueble.id_mueble,
            nombre_objeto=objeto.nombre,
            coordenadas=coordenada_display,  # Mostrar solo una coordenada del mueble
            nivel=punto.nivel,
            estanteria=punto.estanteria
        )
        producto_info = ProductoRutaResponse(
            id_producto=producto.id_producto,
            nombre=producto.nombre,
            categoria=producto.categoria,
            cantidad=detalle.cantidad
        )
        puntos_info.append({
            'id_punto': punto.id_punto,
            'mueble': mueble_info,
            'producto': producto_info,
            'coordenadas': coordenada_accesible,  # Usar coordenada accesible para cálculo
            'coordenadas_originales': [(ubic.x, ubic.y) for ubic in ubicaciones]  # Guardar todas las posiciones
        })
    
    if not puntos_info:
        raise HTTPException(
            status_code=400, 
            detail="No se pudieron obtener las coordenadas para los puntos de reposición"
        )
    
    # Calcular ruta optimizada usando el algoritmo seleccionado
    inicio = (0, 0)
    distancia_total = 0

    # Validar que el punto de inicio es caminable, si no, encontrar uno cercano
    if inicio not in coordenadas_caminables:
        inicio = encontrar_punto_accesible(inicio, coordenadas_caminables)

    # Ejecutar algoritmo seleccionado
    algoritmo_func = algoritmos_disponibles[algoritmo]
    orden_visita_coords, orden_visita_puntos, nombre_algoritmo, descripcion_algoritmo = algoritmo_func(
        puntos_info, inicio, coordenadas_caminables
    )

    # Calcular la ruta concatenada entre cada par consecutivo de puntos, asegurando que nunca pase ni termine sobre un mueble
    coordenadas_ruta_completa = []
    ruta_valida = True
    for i in range(len(orden_visita_coords) - 1):
        origen = orden_visita_coords[i]
        destino = orden_visita_coords[i + 1]
        print(f"[DEBUG RUTA] Segmento {i}: origen={origen}, destino={destino}")
        ruta_segmento = calcular_ruta(
            db,
            mapa.id_mapa,
            origen,
            destino
        )
        if ruta_segmento:
            ruta_segmento_filtrada = []
            for idx, coord in enumerate(ruta_segmento):
                if coord in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                    print(f"[DEBUG RUTA] ¡Ruta pasa por mueble! idx={idx}, coord={coord}")
                    ruta_valida = False
                    break
                ruta_segmento_filtrada.append(coord)
            print(f"[DEBUG RUTA] Segmento {i} ruta filtrada: {ruta_segmento_filtrada}")
            if not ruta_valida:
                break
            if i == 0:
                coordenadas_ruta_completa.extend(ruta_segmento_filtrada)
            else:
                coordenadas_ruta_completa.extend(ruta_segmento_filtrada[1:])
            distancia_total += len(ruta_segmento_filtrada) - 1
        else:
            if i == 0:
                coordenadas_ruta_completa.append(origen)
            x1, y1 = origen
            x2, y2 = destino
            ruta_manual = []
            if x1 < x2:
                for x in range(x1 + 1, x2 + 1):
                    if (x, y1) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        print(f"[DEBUG RUTA] ¡Ruta manual pasa por mueble! coord={(x, y1)}")
                        ruta_valida = False
                        break
                    ruta_manual.append((x, y1))
            elif x1 > x2:
                for x in range(x1 - 1, x2 - 1, -1):
                    if (x, y1) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        print(f"[DEBUG RUTA] ¡Ruta manual pasa por mueble! coord={(x, y1)}")
                        ruta_valida = False
                        break
                    ruta_manual.append((x, y1))
            if not ruta_valida:
                break
            x_final = x2
            if y1 < y2:
                for y in range(y1 + 1, y2 + 1):
                    if (x_final, y) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        print(f"[DEBUG RUTA] ¡Ruta manual pasa por mueble! coord={(x_final, y)}")
                        ruta_valida = False
                        break
                    ruta_manual.append((x_final, y))
            elif y1 > y2:
                for y in range(y1 - 1, y2 - 1, -1):
                    if (x_final, y) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        print(f"[DEBUG RUTA] ¡Ruta manual pasa por mueble! coord={(x_final, y)}")
                        ruta_valida = False
                        break
                    ruta_manual.append((x_final, y))
            if not ruta_valida:
                break
            print(f"[DEBUG RUTA] Segmento {i} ruta manual: {ruta_manual}")
            coordenadas_ruta_completa.extend(ruta_manual)
            distancia_total += len(ruta_manual)

    # FILTRO FINAL: recortar la ruta para que la última coordenada nunca sea la de un mueble
    if coordenadas_ruta_completa:
        while coordenadas_ruta_completa and coordenadas_ruta_completa[-1] in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
            print(f"[DEBUG RUTA] Última coordenada es mueble, recortando: {coordenadas_ruta_completa[-1]}")
            coordenadas_ruta_completa.pop()
        # Si después de recortar no queda ninguna coordenda válida, marcar ruta inválida
        if not coordenadas_ruta_completa:
            ruta_valida = False

    if not ruta_valida:
        raise HTTPException(
            status_code=400,
            detail="No se pudo generar una ruta válida que no pase ni termine sobre un mueble. Verifique la disposición del mapa y los puntos de reposición."
        )

    # FILTRO FINAL: Asegurar que la última coordenada de la ruta NO sea la posición de un mueble (considerando muebles de varias casillas)
    if coordenadas_ruta_completa:
        ultima_coord = coordenadas_ruta_completa[-1]
        if ultima_coord in muebles_coords:
            # Buscar una casilla adyacente en cruz que sea caminable y esté en la ruta
            adyacentes_cruz = [
                (ultima_coord[0], ultima_coord[1] + 1),
                (ultima_coord[0], ultima_coord[1] - 1),
                (ultima_coord[0] + 1, ultima_coord[1]),
                (ultima_coord[0] - 1, ultima_coord[1])
            ]
            nueva_ultima = None
            for coord in reversed(coordenadas_ruta_completa):
                if coord in muebles_coords:
                    continue
                if coord in adyacentes_cruz:
                    nueva_ultima = coord
                    break
            if nueva_ultima:
                idx_nueva = coordenadas_ruta_completa.index(nueva_ultima)
                coordenadas_ruta_completa = coordenadas_ruta_completa[:idx_nueva + 1]
            else:
                for coord in reversed(coordenadas_ruta_completa):
                    if coord not in muebles_coords:
                        nueva_ultima = coord
                        break
                if nueva_ultima:
                    idx_nueva = coordenadas_ruta_completa.index(nueva_ultima)
                    coordenadas_ruta_completa = coordenadas_ruta_completa[:idx_nueva + 1]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No se pudo ajustar la ruta final para evitar terminar sobre un mueble."
                    )

    # Crear puntos de respuesta en el orden correcto
    puntos_ordenados = []
    for idx, punto in enumerate(orden_visita_puntos, start=1):
        punto_respuesta = PuntoRutaResponse(
            id_punto=punto['id_punto'],
            mueble=punto['mueble'],
            producto=punto['producto'],
            orden_visita=idx
        )
        puntos_ordenados.append(punto_respuesta)

    # Convertir coordenadas a objetos de respuesta
    coordenadas_respuesta = [CoordenadaResponse(x=x, y=y) for x, y in coordenadas_ruta_completa]

    # Crear información del algoritmo
    algoritmo_info = AlgoritmoResponse(
        nombre=nombre_algoritmo,
        descripcion=descripcion_algoritmo
    )

    # Calcular tiempo estimado (asumiendo 1 minuto por unidad de distancia + 2 minutos por punto)
    tiempo_estimado = distancia_total + (len(puntos_ordenados) * 2)

    # --- GUARDADO DE RUTA OPTIMIZADA, DETALLES Y PASOS ---
    from app.repositories.ruta_detallada import RutaDetalladaRepository
    from app.schemas.ruta_detallada import RutaOptimizadaCreate, DetalleRutaCreate, PasoRutaCreate
    from datetime import date

    # Eliminar rutas previas para la tarea y reponedor (opcional: solo una por tarea-reponedor)
    rutas_previas = RutaDetalladaRepository.obtener_rutas_por_tarea(db, tarea.id_tarea)
    for r in rutas_previas:
        if r.id_reponedor == reponedor.id_usuario:
            RutaDetalladaRepository.eliminar_ruta(db, r.id_ruta)

    # Preparar datos para guardar
    ruta_data = RutaOptimizadaCreate(
        id_reponedor=reponedor.id_usuario,
        id_tarea=tarea.id_tarea,
        fecha_generada=date.today(),
        algoritmo_usado=nombre_algoritmo,
        tiempo_estimado=tiempo_estimado,
        distancia_total=distancia_total
    )
    detalles_data = []
    pasos_data = []
    secuencia_global = 0
    for idx, punto in enumerate(orden_visita_puntos, start=1):
        detalles_data.append(DetalleRutaCreate(
            orden=idx,
            id_punto=punto['id_punto'],
            tiempo_estimado_punto=None,  # Se puede calcular si se desea
            id_ruta=0  # Se ignora en el repo
        ))
    # Dividir la ruta completa en segmentos (tramos) entre cada par de puntos
    # Cada segmento corresponde a un DetalleRuta
    pasos_por_detalle = []
    idx_coord = 0
    for i in range(len(orden_visita_coords) - 1):
        origen = orden_visita_coords[i]
        destino = orden_visita_coords[i + 1]
        # Buscar el segmento correspondiente en la ruta completa
        segmento = []
        while idx_coord < len(coordenadas_ruta_completa):
            coord = coordenadas_ruta_completa[idx_coord]
            segmento.append(coord)
            if coord == destino:
                idx_coord += 1
                break
            idx_coord += 1
        pasos = []
        for j, (x, y) in enumerate(segmento):
            pasos.append(PasoRutaCreate(
                secuencia=j + 1,
                x=x,
                y=y,
                id_detalle_ruta=0  # Se ignora en el repo
            ))
        pasos_por_detalle.append(pasos)
    # Guardar en la base de datos
    ruta_guardada = RutaDetalladaRepository.crear_ruta_completa(
        db,
        ruta_data,
        detalles_data,
        pasos_por_detalle
    )

    return RutaOptimizadaResponse(
        id_tarea=tarea.id_tarea,
        reponedor=reponedor.nombre,
        fecha_creacion=str(tarea.fecha_creacion),
        puntos_reposicion=puntos_ordenados,
        coordenadas_ruta=coordenadas_respuesta,
        algoritmo_utilizado=algoritmo_info,
        distancia_total=distancia_total,
        tiempo_estimado_minutos=tiempo_estimado,
        estado_tarea=estado_nombre
    )

def algoritmo_vecino_mas_cercano(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo del vecino más cercano - el actual implementado
    """
    puntos_restantes = puntos_info.copy()
    posicion_actual = inicio
    orden_visita_coords = [inicio]
    orden_visita_puntos = []

    while puntos_restantes:
        punto_mas_cercano = None
        distancia_minima = float('inf')
        for punto in puntos_restantes:
            coordenadas_punto = punto['coordenadas']
            distancia = abs(posicion_actual[0] - coordenadas_punto[0]) + abs(posicion_actual[1] - coordenadas_punto[1])
            if distancia < distancia_minima:
                distancia_minima = distancia
                punto_mas_cercano = punto
        if punto_mas_cercano:
            orden_visita_coords.append(punto_mas_cercano['coordenadas'])
            orden_visita_puntos.append(punto_mas_cercano)
            posicion_actual = punto_mas_cercano['coordenadas']
            puntos_restantes.remove(punto_mas_cercano)
    
    return orden_visita_coords, orden_visita_puntos, "Vecino Más Cercano + A*", "Algoritmo de optimización que utiliza el vecino más cercano para ordenar los puntos y A* para calcular las rutas entre ellos"

def algoritmo_fuerza_bruta(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo de fuerza bruta - prueba todas las permutaciones posibles
    """
    if len(puntos_info) > 8:  # Limitar para evitar explosión combinatoria
        # Si hay muchos puntos, usar una muestra aleatoria
        puntos_muestra = random.sample(puntos_info, 8)
    else:
        puntos_muestra = puntos_info
    
    mejor_distancia = float('inf')
    mejor_orden = None
    
    # Probar todas las permutaciones
    for permutacion in itertools.permutations(puntos_muestra):
        distancia_total = 0
        pos_actual = inicio
        
        # Calcular distancia total de esta permutación
        for punto in permutacion:
            coord_punto = punto['coordenadas']
            distancia_total += abs(pos_actual[0] - coord_punto[0]) + abs(pos_actual[1] - coord_punto[1])
            pos_actual = coord_punto
        
        if distancia_total < mejor_distancia:
            mejor_distancia = distancia_total
            mejor_orden = permutacion
    
    # Construir resultado
    orden_visita_coords = [inicio]
    orden_visita_puntos = []
    for punto in mejor_orden:
        orden_visita_coords.append(punto['coordenadas'])
        orden_visita_puntos.append(punto)
    
    return orden_visita_coords, orden_visita_puntos, "Fuerza Bruta + A*", "Algoritmo que prueba todas las permutaciones posibles para encontrar la ruta óptima (limitado a 8 puntos máximo)"

def algoritmo_genetico(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo genético simple para optimización de rutas
    """
    if len(puntos_info) < 2:
        return algoritmo_vecino_mas_cercano(puntos_info, inicio, coordenadas_caminables)
    
    POBLACION_SIZE = min(20, len(puntos_info) * 2)
    GENERACIONES = 50
    TASA_MUTACION = 0.1
    
    def calcular_fitness(orden):
        """Calcular fitness (inverso de la distancia total)"""
        distancia_total = 0
        pos_actual = inicio
        for punto in orden:
            coord_punto = punto['coordenadas']
            distancia_total += abs(pos_actual[0] - coord_punto[0]) + abs(pos_actual[1] - coord_punto[1])
            pos_actual = coord_punto
        return 1.0 / (distancia_total + 1)  # +1 para evitar división por cero
    
    def crear_individuo():
        """Crear un orden aleatorio de puntos"""
        return random.sample(puntos_info, len(puntos_info))
    
    def cruzar(padre1, padre2):
        """Cruzamiento de orden (OX)"""
        tamano = len(padre1)
        inicio_idx = random.randint(0, tamano - 2)
        fin_idx = random.randint(inicio_idx + 1, tamano - 1)
        
        hijo = [None] * tamano
        hijo[inicio_idx:fin_idx + 1] = padre1[inicio_idx:fin_idx + 1]
        
        restantes = [item for item in padre2 if item not in hijo]
        idx_restante = 0
        for i in range(tamano):
            if hijo[i] is None:
                hijo[i] = restantes[idx_restante]
                idx_restante += 1
        
        return hijo
    
    def mutar(individuo):
        """Mutación por intercambio"""
        if random.random() < TASA_MUTACION:
            i, j = random.sample(range(len(individuo)), 2)
            individuo[i], individuo[j] = individuo[j], individuo[i]
        return individuo
    
    # Inicializar población
    poblacion = [crear_individuo() for _ in range(POBLACION_SIZE)]
    
    # Evolucionar
    for generacion in range(GENERACIONES):
        # Evaluar fitness
        fitness_scores = [(individuo, calcular_fitness(individuo)) for individuo in poblacion]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar los mejores (elitismo)
        nueva_poblacion = [individuo for individuo, _ in fitness_scores[:POBLACION_SIZE // 4]]
        
        # Generar nueva población
        while len(nueva_poblacion) < POBLACION_SIZE:
            padre1 = random.choices(fitness_scores[:POBLACION_SIZE // 2], weights=[f for _, f in fitness_scores[:POBLACION_SIZE // 2]])[0][0]
            padre2 = random.choices(fitness_scores[:POBLACION_SIZE // 2], weights=[f for _, f in fitness_scores[:POBLACION_SIZE // 2]])[0][0]
            hijo = cruzar(padre1, padre2)
            hijo = mutar(hijo)
            nueva_poblacion.append(hijo)
        
        poblacion = nueva_poblacion
    
    # Obtener el mejor resultado
    mejor_individuo = max(poblacion, key=calcular_fitness)
    
    # Construir resultado
    orden_visita_coords = [inicio]
    orden_visita_puntos = []
    for punto in mejor_individuo:
        orden_visita_coords.append(punto['coordenadas'])
        orden_visita_puntos.append(punto)
    
    return orden_visita_coords, orden_visita_puntos, "Algoritmo Genético + A*", f"Algoritmo genético con {GENERACIONES} generaciones y población de {POBLACION_SIZE} individuos para optimizar la ruta"

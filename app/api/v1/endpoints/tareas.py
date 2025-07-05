# Endpoint refactorizado para usar el servicio
from app.services.ruta_optimizada import obtener_ruta_optimizada

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
import traceback
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
    print(f"[DEBUG] [encontrar_punto_accesible] Coordenada mueble recibida: {coordenada_mueble}")
    # VERIFICACIÓN: Si el mueble mismo es caminable, NO usarlo (es un error)
    if coordenada_mueble in coordenadas_caminables:
        print(f"WARNING: Mueble en {coordenada_mueble} está marcado como caminable, esto es incorrecto")
    # Primero: buscar en las 8 casillas adyacentes directas (prioridad alta)
    direcciones_adyacentes = [
        (0, 1), (0, -1), (1, 0), (-1, 0),  # arriba, abajo, derecha, izquierda
        (1, 1), (1, -1), (-1, 1), (-1, -1)  # diagonales
    ]
    for dx, dy in direcciones_adyacentes:
        punto_candidato = (x + dx, y + dy)
        if punto_candidato in coordenadas_caminables and punto_candidato != coordenada_mueble:
            print(f"[DEBUG] [encontrar_punto_accesible] Punto accesible encontrado para mueble {coordenada_mueble}: {punto_candidato}")
            return punto_candidato
    # Segundo: si no hay casillas adyacentes caminables, buscar en círculos concéntricos
    for radio in range(2, 8):  # Buscar hasta 7 unidades de distancia
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                # Solo puntos en el borde del círculo actual
                if abs(dx) == radio or abs(dy) == radio:
                    punto_candidato = (x + dx, y + dy)
                    if punto_candidato in coordenadas_caminables and punto_candidato != coordenada_mueble:
                        print(f"[DEBUG] [encontrar_punto_accesible] Punto accesible encontrado (radio {radio}) para mueble {coordenada_mueble}: {punto_candidato}")
                        return punto_candidato
    # Si no se encontró ningún punto accesible, lanzar excepción clara
    error_msg = f"No hay ninguna casilla caminable adyacente al mueble en {coordenada_mueble}. Verifica el layout del mapa."
    print(f"[ERROR] [encontrar_punto_accesible] {error_msg}")
    raise ValueError(error_msg)

def encontrar_punto_accesible_cruz(coordenada_mueble: tuple, coordenadas_caminables: set) -> tuple:
    """
    Busca SOLO en cruz (arriba, abajo, izquierda, derecha) el punto caminable más cercano al mueble.
    """
    x, y = coordenada_mueble
    print(f"[DEBUG] [encontrar_punto_accesible_cruz] Coordenada mueble recibida: {coordenada_mueble}")
    print(f"[DEBUG] [encontrar_punto_accesible_cruz] Total coordenadas caminables: {len(coordenadas_caminables)}")
    
    direcciones_cruz = [
        (0, 1), (0, -1), (1, 0), (-1, 0)  # arriba, abajo, derecha, izquierda
    ]
    
    # Buscar en radio 1 primero
    for dx, dy in direcciones_cruz:
        punto_candidato = (x + dx, y + dy)
        print(f"[DEBUG] [encontrar_punto_accesible_cruz] Probando punto candidato: {punto_candidato}")
        if punto_candidato in coordenadas_caminables:
            print(f"[DEBUG] [encontrar_punto_accesible_cruz] ✓ Punto accesible encontrado para mueble {coordenada_mueble}: {punto_candidato}")
            return punto_candidato
    
    # Buscar en radios mayores
    for radio in range(2, 8):
        print(f"[DEBUG] [encontrar_punto_accesible_cruz] Buscando en radio {radio}")
        for dx, dy in direcciones_cruz:
            punto_candidato = (x + dx * radio, y + dy * radio)
            if punto_candidato in coordenadas_caminables:
                print(f"[DEBUG] [encontrar_punto_accesible_cruz] ✓ Punto accesible encontrado (radio {radio}) para mueble {coordenada_mueble}: {punto_candidato}")
                return punto_candidato
    
    # Si no encuentra nada, buscar cualquier punto caminable cercano
    print(f"[WARNING] [encontrar_punto_accesible_cruz] No se encontró punto en cruz, buscando cualquier punto cercano...")
    min_dist = float('inf')
    mejor_punto = None
    
    for coord_caminable in coordenadas_caminables:
        dist = abs(coord_caminable[0] - x) + abs(coord_caminable[1] - y)
        if dist < min_dist:
            min_dist = dist
            mejor_punto = coord_caminable
    
    if mejor_punto:
        print(f"[DEBUG] [encontrar_punto_accesible_cruz] ✓ Punto alternativo encontrado: {mejor_punto} (distancia: {min_dist})")
        return mejor_punto
    
    print(f"[ERROR] [encontrar_punto_accesible_cruz] No se encontró ningún punto accesible para mueble {coordenada_mueble}")
    raise ValueError(f"No hay puntos caminables accesibles para el mueble en {coordenada_mueble}")

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


# --- Modelo Pydantic para cambio de estado genérico ---
class CambioEstadoRequest(BaseModel):
    nuevo_estado: str

class AsignarReponedorRequest(BaseModel):
    id_reponedor: int
@router.put("/tareas/{id_tarea}/cambiar-estado", status_code=200)
def cambiar_estado_tarea(
    id_tarea: int = Path(..., description="ID de la tarea"),
    body: CambioEstadoRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    estado_actual = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    estado_nuevo = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == body.nuevo_estado).first()
    if not estado_nuevo:
        raise HTTPException(status_code=422, detail="El estado solicitado no existe.")

    # Validación de transición de estado (puedes ajustar según tu lógica de negocio)
    transiciones_validas = {
        "sin asignar": ["pendiente", "cancelada"],
        "pendiente": ["en progreso", "cancelada"],
        "en progreso": ["completada", "cancelada"],
        "completada": [],
        "cancelada": []
    }
    if estado_nuevo.nombre_estado not in transiciones_validas.get(estado_actual.nombre_estado, []):
        raise HTTPException(status_code=409, detail=f"No se puede cambiar de '{estado_actual.nombre_estado}' a '{estado_nuevo.nombre_estado}'.")

    tarea.estado_id = estado_nuevo.estado_id
    db.commit()
    db.refresh(tarea)
    return {
        "mensaje": f"Estado de la tarea cambiado a '{estado_nuevo.nombre_estado}'.",
        "id_tarea": tarea.id_tarea,
        "nuevo_estado": estado_nuevo.nombre_estado
    }


@router.put("/detalle-tarea/{id_detalle}/cambiar-estado", status_code=200)
def cambiar_estado_detalle_tarea(
    id_detalle: int = Path(..., description="ID del detalle de tarea"),
    body: CambioEstadoRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    detalle = db.query(DetalleTarea).filter(DetalleTarea.id_detalle == id_detalle).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle de tarea no encontrado.")

    estado_actual = db.query(EstadoTarea).filter(EstadoTarea.estado_id == detalle.estado_id).first()
    estado_nuevo = db.query(EstadoTarea).filter(EstadoTarea.nombre_estado == body.nuevo_estado).first()
    if not estado_nuevo:
        raise HTTPException(status_code=422, detail="El estado solicitado no existe.")

    # Validación de transición de estado (ajusta según tu lógica de negocio)
    transiciones_validas = {
        "pendiente": ["en progreso", "cancelada"],
        "en progreso": ["completada", "cancelada"],
        "completada": [],
        "cancelada": []
    }
    if estado_nuevo.nombre_estado not in transiciones_validas.get(estado_actual.nombre_estado, []):
        raise HTTPException(status_code=409, detail=f"No se puede cambiar de '{estado_actual.nombre_estado}' a '{estado_nuevo.nombre_estado}'.")

    detalle.estado_id = estado_nuevo.estado_id
    db.commit()
    db.refresh(detalle)
    return {
        "mensaje": f"Estado del detalle de tarea cambiado a '{estado_nuevo.nombre_estado}'.",
        "id_detalle": detalle.id_detalle,
        "nuevo_estado": estado_nuevo.nombre_estado
    }

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




@router.get("/tareas/{id_tarea}/ruta-optimizada", response_model=dict)
def optimizar_rutas_por_detalle_tarea(
    id_tarea: int,
    algoritmo: str = Query("A*", description="Algoritmo a utilizar: 'A*', 'vecino_mas_cercano', etc."),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera y almacena rutas optimizadas independientes para cada detalle_tarea de una tarea.
    Devuelve un JSON con todas las rutas optimizadas por producto.
    """
    # 1. Validar tarea y permisos
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    if current_user.rol.nombre_rol == RolEnum.REPONEDOR.value and int(tarea.id_reponedor) != int(current_user.id_usuario):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea.")

    # 2. Obtener detalles de tarea
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea).all()
    if not detalles:
        raise HTTPException(status_code=404, detail="No hay detalles de tarea para optimizar.")

    # 3. Obtener info de reponedor
    reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
    nombre_reponedor = reponedor.nombre if reponedor else None

    # 4. Preparar respuesta
    respuesta = {
        "id_tarea": tarea.id_tarea,
        "reponedor": nombre_reponedor,
        "detalle_tareas": []
    }

    # 5. Limpiar rutas previas (opcional, según política)
    from sqlalchemy import text
    ids_detalle = ','.join(str(d.id_detalle) for d in detalles)
    if ids_detalle:
        # El nombre correcto de la columna es id_detalle_tarea en detalle_ruta
        db.execute(text(f"DELETE FROM paso_ruta WHERE id_detalle_ruta IN (SELECT id_detalle_ruta FROM detalle_ruta WHERE id_detalle_tarea IN ({ids_detalle}))"))
        db.execute(text(f"DELETE FROM detalle_ruta WHERE id_detalle_tarea IN ({ids_detalle})"))
        db.commit()


    # 6. Procesar cada detalle_tarea usando el servicio real
    from app.services.ruta_optimizada import obtener_ruta_optimizada
    # Llamamos al servicio para obtener la ruta global optimizada (incluye todos los pasos)
    try:
        resultado = obtener_ruta_optimizada(
            id_tarea,
            algoritmo,
            db,
            current_user,
            Tarea,
            UsuarioModel,
            EstadoTarea,
            DetalleTarea,
            Mapa,
            UbicacionFisica,
            ObjetoMapa,
            ObjetoTipo,
            PuntoReposicion,
            MuebleReposicion,
            Producto,
            generar_grafo,
            encontrar_punto_accesible_cruz,
            encontrar_punto_accesible,
            calcular_ruta,
            CoordenadaResponse,
            MuebleRutaResponse,
            ProductoRutaResponse,
            PuntoRutaResponse,
            AlgoritmoResponse,
            RutaOptimizadaResponse,
            RolEnum
        )
    except ValueError as e:
        # Error de punto accesible: mostrar como warning global y continuar con respuesta vacía
        print(f"[ERROR] {str(e)}")
        return {
            "id_tarea": tarea.id_tarea,
            "reponedor": nombre_reponedor,
            "detalle_tareas": [],
            "warning": str(e)
        }
    except HTTPException as e:
        return {"error": e.detail}

    # ENFOQUE HÍBRIDO: Usar optimización global para el orden, rutas individuales para precisión
    from collections import defaultdict
    
    print(f"[DEBUG] ===== INICIO ENFOQUE HÍBRIDO =====")
    print(f"[DEBUG] Total detalle_tareas a procesar: {len(detalles)}")
    
    # Paso 1: Agrupar detalle_tareas por mueble_id
    muebles_grupos = defaultdict(list)
    
    for detalle in detalles:
        producto = db.query(Producto).filter(Producto.id_producto == detalle.id_producto).first()
        producto_nombre = producto.nombre if producto else "Producto desconocido"
        
        print(f"[DEBUG] Procesando detalle {detalle.id_detalle} - Producto: {producto_nombre} - Punto: {detalle.id_punto}")
        
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == detalle.id_punto).first()
        if punto and punto.id_mueble:
            muebles_grupos[punto.id_mueble].append({
                'detalle': detalle,
                'punto': punto
            })
            print(f"[DEBUG] ✓ Detalle {detalle.id_detalle} ({producto_nombre}) asignado a mueble {punto.id_mueble}")
        else:
            print(f"[WARNING] ✗ Punto {detalle.id_punto} no tiene mueble asignado o punto no encontrado")
    
    print(f"[DEBUG] Total muebles encontrados: {len(muebles_grupos)}")
    print(f"[DEBUG] Muebles IDs: {list(muebles_grupos.keys())}")
    
    # Paso 2: Extraer orden óptimo de muebles desde la ruta global
    pasos_globales = resultado.coordenadas_ruta
    
    def distancia_manhattan(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    # Mapear cada mueble a su posición en la ruta global
    muebles_orden = []
    
    for mueble_id, grupo in muebles_grupos.items():
        # Obtener información y coordenadas del mueble
        mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == mueble_id).first()
        objeto = None
        coordenadas_mueble = []
        
        if mueble:
            objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first()
            if objeto:
                ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).all()
                for ubic in ubicaciones:
                    coordenadas_mueble.append((ubic.x, ubic.y))
        
        # Encontrar el punto más cercano en la ruta global
        mejor_posicion = -1
        min_distancia = float('inf')
        
        if coordenadas_mueble:
            for coord_mueble in coordenadas_mueble:
                for idx, paso in enumerate(pasos_globales):
                    dist = distancia_manhattan((paso.x, paso.y), coord_mueble)
                    if dist < min_distancia:
                        min_distancia = dist
                        mejor_posicion = idx
                        if dist <= 1:  # Encontrado punto adyacente
                            break
        
        muebles_orden.append({
            'mueble_id': mueble_id,
            'grupo': grupo,
            'objeto': objeto,
            'coordenadas': coordenadas_mueble,
            'posicion_global': mejor_posicion,
            'distancia_min': min_distancia
        })
        
        print(f"[DEBUG] Mueble {mueble_id}: posición en ruta global = {mejor_posicion}, distancia = {min_distancia}")
    
    # Paso 3: Ordenar muebles según su aparición en la ruta global
    muebles_orden_sorted = sorted(muebles_orden, key=lambda x: x['posicion_global'] if x['posicion_global'] >= 0 else float('inf'))
    
    print(f"[DEBUG] Orden final de muebles:")
    for i, m in enumerate(muebles_orden_sorted):
        print(f"[DEBUG] {i+1}. Mueble {m['mueble_id']} (posición: {m['posicion_global']})")
    
    # Paso 4: Generar rutas individuales siguiendo el orden optimizado
    muebles_rutas = []
    posicion_actual = (0, 0)  # Punto de inicio
    ruta_global_completa = []
    
    for i, mueble_info in enumerate(muebles_orden_sorted):
        mueble_id = mueble_info['mueble_id']
        grupo = mueble_info['grupo']
        objeto = mueble_info['objeto']
        coordenadas_mueble = mueble_info['coordenadas']
        
        print(f"[DEBUG] ===== GENERANDO RUTA INDIVIDUAL PARA MUEBLE {mueble_id} =====")
        
        # Preparar lista de detalle_tareas para este mueble
        detalle_tareas_mueble = []
        for item in grupo:
            detalle = item['detalle']
            punto = item['punto']
            producto = db.query(Producto).filter(Producto.id_producto == detalle.id_producto).first()
            
            detalle_tareas_mueble.append({
                "id_detalle_tarea": detalle.id_detalle,
                "producto": producto.nombre if producto else None,
                "cantidad": detalle.cantidad,
                "id_punto_reposicion": punto.id_punto
            })
        
        # Generar ruta individual hacia este mueble
        ruta_mueble_individual = []
        distancia_total = 0
        
        print(f"[DEBUG] Mueble {mueble_id}: coordenadas_mueble = {coordenadas_mueble}")
        print(f"[DEBUG] Posición actual antes de calcular ruta: {posicion_actual}")
        
        if coordenadas_mueble:
            # Encontrar coordenada de acceso al mueble (punto caminable más cercano)
            try:
                # Obtener mapa activo
                print(f"[DEBUG] Obteniendo mapa activo para mueble {mueble_id}...")
                mapa_activo = db.query(Mapa).filter(Mapa.activo == True).first()
                if not mapa_activo:
                    print(f"[ERROR] No hay mapa activo en la base de datos")
                    ruta_mueble_individual = []
                    distancia_total = 0
                    continue
                
                # Obtener coordenadas caminables del grafo
                print(f"[DEBUG] Generando grafo para mueble {mueble_id} con mapa {mapa_activo.id_mapa}...")
                grafo = generar_grafo(db, mapa_activo.id_mapa)
                coordenadas_caminables = grafo  # grafo ya es un set o lista de coordenadas caminables
                print(f"[DEBUG] Total coordenadas caminables: {len(coordenadas_caminables)}")
                
                # Mostrar algunas coordenadas caminables para debug
                coordenadas_muestra = list(coordenadas_caminables)[:10]
                print(f"[DEBUG] Primeras 10 coordenadas caminables: {coordenadas_muestra}")
                
                # Encontrar mejor punto de acceso al mueble
                mejor_acceso = None
                min_dist_acceso = float('inf')
                
                print(f"[DEBUG] Buscando punto de acceso para {len(coordenadas_mueble)} coordenadas del mueble...")
                
                for coord_mueble in coordenadas_mueble:
                    print(f"[DEBUG] Buscando acceso para coordenada del mueble: {coord_mueble}")
                    try:
                        punto_acceso = encontrar_punto_accesible_cruz(coord_mueble, coordenadas_caminables)
                        print(f"[DEBUG] Punto de acceso encontrado: {punto_acceso}")
                        
                        dist_desde_actual = distancia_manhattan(posicion_actual, punto_acceso)
                        print(f"[DEBUG] Distancia desde posición actual {posicion_actual}: {dist_desde_actual}")
                        
                        if dist_desde_actual < min_dist_acceso:
                            min_dist_acceso = dist_desde_actual
                            mejor_acceso = punto_acceso
                            print(f"[DEBUG] Nuevo mejor acceso: {mejor_acceso} (distancia: {min_dist_acceso})")
                            
                    except ValueError as ve:
                        print(f"[ERROR] Error en encontrar_punto_accesible_cruz para {coord_mueble}: {str(ve)}")
                        continue
                    except Exception as e:
                        print(f"[ERROR] Error inesperado buscando acceso para {coord_mueble}: {str(e)}")
                        continue
                
                print(f"[DEBUG] Mejor acceso final para mueble {mueble_id}: {mejor_acceso}")
                
                if mejor_acceso:
                    # Calcular ruta desde posición actual hasta el mueble
                    try:
                        print(f"[DEBUG] [A* INPUT] inicio={posicion_actual}, meta={mejor_acceso}, ejemplo_walkable={list(coordenadas_caminables)[:5]}")
                        ruta_hacia_mueble = calcular_ruta(db, mapa_activo.id_mapa, posicion_actual, mejor_acceso)
                        print(f"[DEBUG] Ruta calculada: {len(ruta_hacia_mueble)} pasos")
                        print(f"[DEBUG] Ruta completa: {ruta_hacia_mueble}")
                        # Convertir a formato de respuesta
                        for j, (x, y) in enumerate(ruta_hacia_mueble):
                            ruta_mueble_individual.append({
                                "orden": j + 1,
                                "x": x,
                                "y": y
                            })
                        distancia_total = len(ruta_hacia_mueble) - 1 if len(ruta_hacia_mueble) > 1 else 0
                        print(f"[DEBUG] Distancia total calculada: {distancia_total}")
                        # Actualizar posición actual para el siguiente mueble
                        posicion_actual = mejor_acceso
                        print(f"[DEBUG] Posición actual actualizada a: {posicion_actual}")
                        # Agregar a ruta global completa
                        ruta_global_completa.extend(ruta_hacia_mueble)
                        print(f"[DEBUG] ✅ Ruta generada exitosamente para mueble {mueble_id}")
                        print(f"[DEBUG] - Pasos en ruta: {len(ruta_mueble_individual)}")
                        print(f"[DEBUG] - Distancia: {distancia_total}")
                    except Exception as e:
                        print(f"[ERROR] Error calculando ruta hacia mueble {mueble_id}: {str(e)}")
                        print(f"[ERROR] Tipo de error: {type(e)}")
                        import traceback
                        print(f"[ERROR] Traceback: {traceback.format_exc()}")
                        ruta_mueble_individual = []
                        distancia_total = 0
                else:
                    print(f"[ERROR] No se pudo encontrar punto de acceso para mueble {mueble_id}")
                    print(f"[DEBUG] Coordenadas del mueble: {coordenadas_mueble}")
                    print(f"[DEBUG] ¿Hay coordenadas caminables cerca?")
                    
                    # Mostrar coordenadas caminables cerca del mueble para debug
                    for coord_mueble in coordenadas_mueble:
                        x, y = coord_mueble
                        cercanas = []
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                test_coord = (x + dx, y + dy)
                                if test_coord in coordenadas_caminables:
                                    cercanas.append(test_coord)
                        print(f"[DEBUG] Coordenadas caminables cerca de {coord_mueble}: {cercanas}")
                    
                    ruta_mueble_individual = []
                    distancia_total = 0
                    
            except Exception as e:
                print(f"[ERROR] Error generando grafo o acceso para mueble {mueble_id}: {str(e)}")
                print(f"[ERROR] Tipo de error: {type(e)}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                ruta_mueble_individual = []
                distancia_total = 0
        else:
            print(f"[ERROR] Mueble {mueble_id} no tiene coordenadas definidas")
            print(f"[DEBUG] Objeto del mueble: {objeto}")
            if objeto:
                ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).all()
                print(f"[DEBUG] Ubicaciones encontradas: {[(u.x, u.y) for u in ubicaciones]}")
            ruta_mueble_individual = []
            distancia_total = 0
        
        # SIEMPRE agregar el mueble a la respuesta (incluso si la ruta falló)
        muebles_rutas.append({
            "id_mueble": mueble_id,
            "nombre_mueble": objeto.nombre if objeto else f"Mueble {mueble_id}",
            "detalle_tareas": detalle_tareas_mueble,
            "ruta_optimizada_mueble": ruta_mueble_individual,
            "distancia_total_mueble": float(distancia_total),
            "algoritmo_usado": getattr(resultado.algoritmo_utilizado, "nombre", None)
        })
        
        print(f"[DEBUG] ✓ Mueble {mueble_id} agregado con {len(detalle_tareas_mueble)} productos y ruta de {len(ruta_mueble_individual)} pasos")
    
    print(f"[DEBUG] ===== RESULTADO FINAL =====")
    print(f"[DEBUG] Total muebles en respuesta: {len(muebles_rutas)}")
    for i, mueble in enumerate(muebles_rutas):
        print(f"[DEBUG] Mueble {i+1}: ID={mueble['id_mueble']}, Productos={len(mueble['detalle_tareas'])}, Pasos={len(mueble['ruta_optimizada_mueble'])}")
    print(f"[DEBUG] ===============================")

    respuesta["muebles_rutas"] = muebles_rutas
    respuesta["tiempo_estimado_total"] = getattr(resultado, "tiempo_estimado_minutos", None)
    
    # Usar la ruta global completa generada por el enfoque híbrido si está disponible
    if ruta_global_completa:
        respuesta["coordenadas_ruta_global"] = [
            {"x": x, "y": y} for x, y in ruta_global_completa
        ]
        print(f"[DEBUG] Usando ruta global híbrida con {len(ruta_global_completa)} pasos")
    else:
        # Fallback a la ruta global original del servicio
        respuesta["coordenadas_ruta_global"] = [
            {"x": c.x, "y": c.y} for c in getattr(resultado, "coordenadas_ruta", [])
        ]
        print(f"[DEBUG] Usando ruta global original del servicio")
    
    return respuesta

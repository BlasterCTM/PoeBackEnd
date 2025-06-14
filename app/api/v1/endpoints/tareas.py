# Endpoints para detalle de tarea

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.repositories.detalle_tarea import agregar_producto_a_detalle, eliminar_producto_de_detalle, listar_detalle_tarea
from app.models.producto import Producto

router = APIRouter()

@router.post("/tareas/{id_tarea}/detalle")
def agregar_producto_detalle(
    id_tarea: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    id_producto = body.get("id_producto")
    cantidad = body.get("cantidad")
    if not id_producto or cantidad is None:
        raise HTTPException(status_code=422, detail="id_producto y cantidad son obligatorios.")
    try:
        detalle, producto = agregar_producto_a_detalle(db, id_tarea, id_producto, cantidad, current_user)
    except Exception as e:
        msg = str(e)
        if "ya está asignado" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return {
        "mensaje": "Producto agregado correctamente a la tarea.",
        "detalle_tarea": {
            "id_producto": detalle.id_producto,
            "nombre_producto": producto.nombre,
            "cantidad": detalle.cantidad
        }
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

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    db_producto = create_producto(db, producto, id_usuario=current_user.id_usuario, codigo_unico=codigo_unico)
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


@router.get("/productos/{id_producto}", response_model=ProductoOut)
def obtener_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    db_producto = get_producto_by_id(db, id_producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto


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
    # Solo se pueden editar nombre y categoria
    cambios = {}
    if producto_update.nombre is not None:
        cambios["nombre"] = producto_update.nombre
    if producto_update.categoria is not None:
        cambios["categoria"] = producto_update.categoria
    if not cambios:
        raise HTTPException(status_code=422, detail="No se proporcionaron campos válidos para actualizar")
    db_producto = update_producto(db, db_producto, **cambios)
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


from fastapi import Security
from fastapi.security import OAuth2PasswordBearer

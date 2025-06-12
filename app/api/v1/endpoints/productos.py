from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.producto import ProductoCreate, ProductoOut, ProductoUpdate
from app.repositories.producto import create_producto, get_productos, update_producto, get_producto_by_id
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
import uuid

router = APIRouter()

@router.post("/productos", response_model=ProductoOut, status_code=201)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear productos")
    # Generar código único si no se proporciona
    codigo_unico = producto.codigo_unico or str(uuid.uuid4())[:8].upper()
    db_producto = create_producto(db, producto, id_usuario=current_user.id_usuario, codigo_unico=codigo_unico)
    return db_producto

@router.get("/productos", response_model=list[ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    return get_productos(db)

@router.put("/productos/{id_producto}", response_model=ProductoOut)
def actualizar_producto(
    id_producto: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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

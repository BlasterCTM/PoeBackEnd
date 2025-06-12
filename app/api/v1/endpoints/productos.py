from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.producto import ProductoCreate, ProductoOut
from app.repositories.producto import create_producto, get_productos
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

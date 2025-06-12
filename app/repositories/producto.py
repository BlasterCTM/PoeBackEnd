from sqlalchemy.orm import Session
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate
from typing import List

def create_producto(db: Session, producto: ProductoCreate, id_usuario: int, codigo_unico: str = None):
    db_producto = Producto(
        nombre=producto.nombre,
        categoria=producto.categoria,
        unidad_tipo=producto.unidad_tipo,
        unidad_cantidad=producto.unidad_cantidad,
        codigo_unico=codigo_unico,
        id_usuario=id_usuario
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def get_productos(db: Session) -> List[Producto]:
    return db.query(Producto).all()

def get_producto_by_id(db: Session, id_producto: int) -> Producto:
    return db.query(Producto).filter(Producto.id_producto == id_producto).first()

def update_producto(db: Session, db_producto: Producto, **cambios) -> Producto:
    for campo, valor in cambios.items():
        setattr(db_producto, campo, valor)
    db.commit()
    db.refresh(db_producto)
    return db_producto

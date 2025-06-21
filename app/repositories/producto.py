from sqlalchemy.orm import Session
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate
from typing import List
from app.models.detalle_tarea import DetalleTarea
from app.models.tarea import Tarea
from sqlalchemy import or_, asc, desc, func

def existe_codigo_unico(db: Session, codigo_unico: str, exclude_id: int = None) -> bool:
    query = db.query(Producto).filter(func.lower(Producto.codigo_unico) == codigo_unico.lower())
    if exclude_id:
        query = query.filter(Producto.id_producto != exclude_id)
    return db.query(query.exists()).scalar()

def create_producto(db: Session, producto: ProductoCreate, id_usuario: int, codigo_unico: str = None):
    # Validar unicidad de codigo_unico
    codigo = codigo_unico or producto.codigo_unico
    if existe_codigo_unico(db, codigo):
        raise ValueError(f"Ya existe un producto con el código '{codigo}'.")
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

def get_productos(
    db: Session,
    page: int = 1,
    limit: int = 10,
    orden: str = "nombre",
    estado: str = None,
    id_usuario: int = None  # Nuevo parámetro opcional
):
    query = db.query(Producto)
    if estado:
        query = query.filter(Producto.estado == estado)
    if id_usuario is not None:
        query = query.filter(Producto.id_usuario == id_usuario)
    total = query.count()
    # Ordenamiento seguro
    if orden == "nombre":
        query = query.order_by(asc(Producto.nombre))
    elif orden == "fecha":
        if hasattr(Producto, "created_at"):
            query = query.order_by(desc(Producto.created_at))
        else:
            query = query.order_by(asc(Producto.nombre))
    # Paginación
    productos = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "productos": productos
    }

def get_producto_by_id(db: Session, id_producto: int) -> Producto:
    return db.query(Producto).filter(Producto.id_producto == id_producto).first()

def update_producto(db: Session, db_producto: Producto, **cambios) -> Producto:
    if "codigo_unico" in cambios and cambios["codigo_unico"]:
        nuevo_codigo = cambios["codigo_unico"]
        if nuevo_codigo.lower() != db_producto.codigo_unico.lower():
            if existe_codigo_unico(db, nuevo_codigo, exclude_id=db_producto.id_producto):
                raise ValueError(f"Ya existe un producto con el código '{nuevo_codigo}'.")
    for campo, valor in cambios.items():
        setattr(db_producto, campo, valor)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def producto_vinculado_a_tareas_activas(db: Session, id_producto: int, estados_activos: list) -> bool:
    query = (
        db.query(DetalleTarea)
        .join(Tarea, DetalleTarea.id_tarea == Tarea.id_tarea)
        .filter(
            DetalleTarea.id_producto == id_producto,
            Tarea.estado_id.in_(estados_activos)
        )
    )
    return db.query(query.exists()).scalar()

def buscar_productos(
    db: Session,
    nombre: str = None,
    categoria: str = None
):
    query = db.query(Producto).filter(Producto.estado == "activo")
    if nombre:
        query = query.filter(func.lower(Producto.nombre).ilike(f"%{nombre.lower()}%"))
    if categoria:
        query = query.filter(func.lower(Producto.categoria) == categoria.lower())
    resultados = query.order_by(asc(Producto.nombre)).all()
    return resultados

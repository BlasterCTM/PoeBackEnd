from sqlalchemy.orm import Session
from app.models.punto_reposicion import PuntoReposicion
from app.models.producto import Producto
from sqlalchemy.exc import NoResultFound

# Asociar o reasignar un producto a un punto de reposición
def asignar_producto_a_punto(db: Session, id_punto: int, id_producto: int):
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == id_punto).first()
    if not punto:
        raise NoResultFound("Punto de reposición no encontrado")
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise NoResultFound("Producto no encontrado")
    punto.id_producto = id_producto
    db.commit()
    db.refresh(punto)
    return punto

# Obtener el punto de reposición donde está asignado un producto
def obtener_punto_por_producto(db: Session, id_producto: int):
    return db.query(PuntoReposicion).filter(PuntoReposicion.id_producto == id_producto).first()

# Desasignar un producto de un punto de reposición
def desasignar_producto_de_punto(db: Session, id_punto: int):
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == id_punto).first()
    if not punto:
        raise NoResultFound("Punto de reposición no encontrado")
    punto.id_producto = None
    db.commit()
    db.refresh(punto)
    return punto

# Desasignar un producto de su punto usando id_producto
def desasignar_punto_por_producto(db: Session, id_producto: int):
    punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_producto == id_producto).first()
    if not punto:
        raise NoResultFound("No hay punto de reposición asignado a este producto")
    punto.id_producto = None
    db.commit()
    db.refresh(punto)
    return punto

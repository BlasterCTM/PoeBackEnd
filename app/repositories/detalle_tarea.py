# Repositorio para operaciones sobre detalle_tarea

from sqlalchemy.orm import Session
from app.models.detalle_tarea import DetalleTarea
from app.models.producto import Producto
from app.models.tarea import Tarea
from app.models.supervision import Supervision
from app.models.usuario import Usuario, RolEnum
from sqlalchemy.exc import NoResultFound

def agregar_producto_a_detalle(db: Session, id_tarea: int, id_producto: int, cantidad: int, current_user: Usuario):
    # Validar cantidad
    if cantidad <= 0:
        raise Exception("La cantidad debe ser mayor a cero.")
    # Validar existencia de tarea y producto
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise Exception("La tarea no existe.")
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise Exception("El producto no existe.")
    # Validar permisos
    if current_user.rol.nombre_rol.lower() == "supervisor":
        # Validar que la tarea fue creada por este supervisor
        if tarea.id_supervisor != current_user.id_usuario:
            raise Exception("No tienes permisos para modificar esta tarea (no eres el supervisor asignado).")
        # Si la tarea tiene reponedor asignado, validar supervisión
        if tarea.id_reponedor is not None:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == tarea.id_reponedor, 
                Supervision.supervisor_id == current_user.id_usuario
            ).first()
            if not supervision:
                raise Exception("No tienes permisos para modificar esta tarea (el reponedor no está bajo tu supervisión).")
    elif current_user.rol.nombre_rol.lower() != "administrador":
        raise Exception("No tienes permisos para modificar tareas.")
    # Validar duplicado
    existe = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_producto == id_producto).first()
    if existe:
        raise Exception("El producto ya está asignado a la tarea.")
    # Agregar
    detalle = DetalleTarea(id_tarea=id_tarea, id_producto=id_producto, cantidad=cantidad)
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return detalle, producto

def eliminar_producto_de_detalle(db: Session, id_tarea: int, id_producto: int, current_user: Usuario):
    detalle = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea, DetalleTarea.id_producto == id_producto).first()
    if not detalle:
        raise Exception("El producto no está en el detalle de la tarea.")
    # Validar permisos (igual que agregar)
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise Exception("La tarea no existe.")
    if current_user.rol.nombre_rol.lower() == "supervisor":
        # Validar que la tarea fue creada por este supervisor
        if tarea.id_supervisor != current_user.id_usuario:
            raise Exception("No tienes permisos para modificar esta tarea (no eres el supervisor asignado).")
        # Si la tarea tiene reponedor asignado, validar supervisión
        if tarea.id_reponedor is not None:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == tarea.id_reponedor, 
                Supervision.supervisor_id == current_user.id_usuario
            ).first()
            if not supervision:
                raise Exception("No tienes permisos para modificar esta tarea (el reponedor no está bajo tu supervisión).")
    elif current_user.rol.nombre_rol.lower() != "administrador":
        raise Exception("No tienes permisos para modificar tareas.")
    db.delete(detalle)
    db.commit()
    return True

def listar_detalle_tarea(db: Session, id_tarea: int, current_user: Usuario):
    # Validar permisos (igual que agregar)
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise Exception("La tarea no existe.")
    if current_user.rol.nombre_rol.lower() == "supervisor":
        # Validar que la tarea fue creada por este supervisor
        if tarea.id_supervisor != current_user.id_usuario:
            raise Exception("No tienes permisos para ver esta tarea (no eres el supervisor asignado).")
        # Si la tarea tiene reponedor asignado, validar supervisión
        if tarea.id_reponedor is not None:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == tarea.id_reponedor, 
                Supervision.supervisor_id == current_user.id_usuario
            ).first()
            if not supervision:
                raise Exception("No tienes permisos para ver esta tarea (el reponedor no está bajo tu supervisión).")
    elif current_user.rol.nombre_rol.lower() == "reponedor":
        if int(tarea.id_reponedor) != int(current_user.id_usuario):
            raise Exception("No tienes permisos para ver esta tarea.")
    elif current_user.rol.nombre_rol.lower() != "administrador":
        raise Exception("No tienes permisos para ver tareas.")
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea).all()
    return detalles

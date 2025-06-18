import pytest
from fastapi.testclient import TestClient
from app.main import app
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app.core.database.database import db
from app.models.usuario import Usuario, Rol
from app.models.producto import Producto
from app.models.punto_reposicion import PuntoReposicion

client = TestClient(app)

Session = sessionmaker(bind=db.engine)

def get_token_admin():
    # Login real para obtener token admin
    response = client.post("/usuarios/token", json={"correo": "admin@poe.com", "contraseña": "admin123"})
    assert response.status_code == 200, f"No se pudo obtener token admin: {response.text}"
    return response.json()["access_token"]

def get_token_supervisor():
    response = client.post("/usuarios/token", json={"correo": "supervisor@poe.com", "contraseña": "supervisor123"})
    assert response.status_code == 200, f"No se pudo obtener token supervisor: {response.text}"
    return response.json()["access_token"]

def poblar_datos_minimos():
    """Asegura que existan los usuarios, productos y punto requeridos para los tests."""
    session = Session()
    # Roles
    if not session.query(Rol).filter_by(id_rol=1).first():
        session.add(Rol(id_rol=1, nombre_rol="admin"))
    if not session.query(Rol).filter_by(id_rol=2).first():
        session.add(Rol(id_rol=2, nombre_rol="supervisor"))
    if not session.query(Rol).filter_by(id_rol=3).first():
        session.add(Rol(id_rol=3, nombre_rol="reponedor"))
    session.commit()
    # Usuarios
    if not session.query(Usuario).filter_by(id_usuario=1).first():
        session.add(Usuario(id_usuario=1, nombre="Admin", correo="admin@poe.com", contraseña="$2b$12$QWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTY", rol_id=1, estado="activo"))
    if not session.query(Usuario).filter_by(id_usuario=2).first():
        session.add(Usuario(id_usuario=2, nombre="Supervisor", correo="supervisor@poe.com", contraseña="$2b$12$QWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTY", rol_id=2, estado="activo"))
    if not session.query(Usuario).filter_by(id_usuario=3).first():
        session.add(Usuario(id_usuario=3, nombre="Reponedor", correo="reponedor@poe.com", contraseña="$2b$12$QWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTY", rol_id=3, estado="activo"))
    session.commit()
    # Productos (requiere unidad_cantidad, id_usuario, estado)
    if not session.query(Producto).filter_by(id_producto=1).first():
        session.add(Producto(id_producto=1, nombre="Producto 1", categoria="cat1", unidad_tipo="unidad", unidad_cantidad=1, codigo_unico="P1", id_usuario=1, estado="activo"))
    if not session.query(Producto).filter_by(id_producto=2).first():
        session.add(Producto(id_producto=2, nombre="Producto 2", categoria="cat2", unidad_tipo="unidad", unidad_cantidad=1, codigo_unico="P2", id_usuario=1, estado="activo"))
    session.commit()
    # Punto de reposición
    if not session.query(PuntoReposicion).filter_by(id_punto=1).first():
        session.add(PuntoReposicion(id_punto=1, id_mueble=1, nivel=1, estanteria=1, id_producto=1))
    session.commit()
    session.close()

def test_crear_tarea_exitosa():
    poblar_datos_minimos()
    token = get_token_admin()
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5},
            {"id_producto": 2, "cantidad": 3}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Error: {response.text}"
    assert response.json()["mensaje"] == "Tarea creada exitosamente"

def test_crear_tarea_sin_productos():
    poblar_datos_minimos()
    token = get_token_admin()
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": []
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

def test_crear_tarea_productos_duplicados():
    poblar_datos_minimos()
    token = get_token_admin()
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5},
            {"id_producto": 1, "cantidad": 3}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

def test_agregar_producto_detalle_exitoso():
    poblar_datos_minimos()
    token = get_token_admin()
    # Primero crea una tarea válida
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Error: {response.text}"
    id_tarea = response.json()["tarea"]["id_tarea"]
    # Agrega un producto nuevo al detalle
    detalle = {"id_producto": 2, "cantidad": 4}
    response = client.post(f"/tareas/{id_tarea}/detalle", json=detalle, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Producto agregado correctamente"

def test_agregar_producto_detalle_cantidad_negativa():
    poblar_datos_minimos()
    token = get_token_admin()
    # Primero crea una tarea válida
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Error: {response.text}"
    id_tarea = response.json()["tarea"]["id_tarea"]
    detalle = {"id_producto": 2, "cantidad": -1}
    response = client.post(f"/tareas/{id_tarea}/detalle", json=detalle, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert "mayor que 0" in response.text

def test_agregar_producto_detalle_duplicado():
    poblar_datos_minimos()
    token = get_token_admin()
    # Primero crea una tarea válida
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Error: {response.text}"
    id_tarea = response.json()["tarea"]["id_tarea"]
    detalle = {"id_producto": 1, "cantidad": 2}
    response = client.post(f"/tareas/{id_tarea}/detalle", json=detalle, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409
    assert "ya está asignado" in response.text

def test_eliminar_producto_detalle():
    poblar_datos_minimos()
    token = get_token_admin()
    # Primero crea una tarea válida
    data = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5},
            {"id_producto": 2, "cantidad": 3}
        ]
    }
    response = client.post("/tareas", json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Error: {response.text}"
    id_tarea = response.json()["tarea"]["id_tarea"]
    # Elimina un producto
    response = client.delete(f"/tareas/{id_tarea}/detalle/2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "eliminado" in response.text

def test_no_permite_tarea_en_punto_ocupado():
    poblar_datos_minimos()
    token = get_token_admin()
    # Limpiar tareas activas del punto antes de probar
    session = Session()
    from app.models.tarea import Tarea
    from app.models.estado_tarea import EstadoTarea
    tareas_activas = session.query(Tarea).join(EstadoTarea, Tarea.estado_id == EstadoTarea.estado_id).filter(
        Tarea.id_punto == 1,
        EstadoTarea.nombre_estado.in_(["pendiente", "en progreso"])
    ).all()
    for t in tareas_activas:
        # Cambiar estado a "completada" (debe existir ese estado en la tabla)
        estado_completada = session.query(EstadoTarea).filter(EstadoTarea.nombre_estado == "completada").first()
        if estado_completada:
            t.estado_id = estado_completada.estado_id
    session.commit()
    session.close()
    # Crear primera tarea (deja el punto en estado pendiente)
    data1 = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 1, "cantidad": 5}
        ]
    }
    response1 = client.post("/tareas", json=data1, headers={"Authorization": f"Bearer {token}"})
    assert response1.status_code == 201, f"Error inesperado: {response1.text}"
    # Intentar crear otra tarea en el mismo punto
    data2 = {
        "id_reponedor": 3,
        "id_punto": 1,
        "id_supervisor": 2,
        "productos": [
            {"id_producto": 2, "cantidad": 2}
        ]
    }
    response2 = client.post("/tareas", json=data2, headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 409, f"Debe rechazar por conflicto, obtuvo: {response2.status_code} - {response2.text}"
    detail = response2.json().get("detail")
    assert detail and "tarea_conflictiva" in detail, f"Respuesta inesperada: {response2.text}"
    assert detail["tarea_conflictiva"]["estado"] in ["pendiente", "en progreso"]

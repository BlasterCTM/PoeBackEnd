import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Utilidades para autenticación
ADMIN_LOGIN = {"correo": "admin@poe.com", "contraseña": "admin123"}
SUPERVISOR_LOGIN = {"correo": "supervisor.test@poe.com", "contraseña": "supervisor123"}
REPONEDOR_LOGIN = {"correo": "reponedor.test@poe.com", "contraseña": "reponedor123"}


def get_token(login_data):
    response = client.post("/usuarios/token", json=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_admin():
    token = get_token(ADMIN_LOGIN)
    assert token

def test_login_supervisor():
    token = get_token(SUPERVISOR_LOGIN)
    assert token

def test_login_reponedor():
    token = get_token(REPONEDOR_LOGIN)
    assert token


def test_crear_producto_admin():
    token = get_token(ADMIN_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "nombre": "Producto Test",
        "categoria": "TestCat",
        "unidad_tipo": "Caja",
        "unidad_cantidad": 10
    }
    response = client.post("/productos", json=data, headers=headers)
    assert response.status_code == 201
    assert response.json()["nombre"] == "Producto Test"


def test_crear_producto_no_admin():
    token = get_token(SUPERVISOR_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "nombre": "Producto Test2",
        "categoria": "TestCat",
        "unidad_tipo": "Caja",
        "unidad_cantidad": 10
    }
    response = client.post("/productos", json=data, headers=headers)
    assert response.status_code == 403


def test_listar_productos():
    response = client.get("/productos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_editar_producto_admin():
    token = get_token(ADMIN_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    # Crear producto primero
    data = {
        "nombre": "Producto Edit",
        "categoria": "CatEdit",
        "unidad_tipo": "Caja",
        "unidad_cantidad": 5
    }
    response = client.post("/productos", json=data, headers=headers)
    assert response.status_code == 201
    id_producto = response.json()["id_producto"]
    # Editar producto
    update = {"nombre": "Producto Editado", "categoria": "CatNueva"}
    response = client.put(f"/productos/{id_producto}", json=update, headers=headers)
    assert response.status_code == 200
    assert response.json()["nombre"] == "Producto Editado"
    assert response.json()["categoria"] == "CatNueva"


def test_editar_producto_no_admin():
    token = get_token(SUPERVISOR_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    # Crear producto como admin
    admin_token = get_token(ADMIN_LOGIN)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "nombre": "Producto NoAdmin",
        "categoria": "CatNoAdmin",
        "unidad_tipo": "Caja",
        "unidad_cantidad": 5
    }
    response = client.post("/productos", json=data, headers=admin_headers)
    id_producto = response.json()["id_producto"]
    # Intentar editar como supervisor
    update = {"nombre": "Intento NoAdmin"}
    response = client.put(f"/productos/{id_producto}", json=update, headers=headers)
    assert response.status_code == 403


def test_editar_producto_invalido():
    token = get_token(ADMIN_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    # Intentar editar producto inexistente
    response = client.put("/productos/99999", json={"nombre": "Nada"}, headers=headers)
    assert response.status_code == 404
    # Intentar editar sin campos válidos
    # Crear producto
    data = {
        "nombre": "Producto SinCambios",
        "categoria": "CatSinCambios",
        "unidad_tipo": "Caja",
        "unidad_cantidad": 5
    }
    response = client.post("/productos", json=data, headers=headers)
    id_producto = response.json()["id_producto"]
    response = client.put(f"/productos/{id_producto}", json={}, headers=headers)
    assert response.status_code == 422


def test_listar_usuarios_admin():
    token = get_token(ADMIN_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/usuarios", headers=headers)
    assert response.status_code == 200
    assert "usuarios" in response.json()


def test_listar_usuarios_no_admin():
    token = get_token(SUPERVISOR_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/usuarios", headers=headers)
    assert response.status_code == 403


def test_perfil_usuario():
    token = get_token(ADMIN_LOGIN)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/usuarios/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["correo"] == "admin@poe.com"

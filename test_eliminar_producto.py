import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ADMIN_CREDENTIALS = {"correo": "admin@poe.com", "contraseña": "admin123"}
USER_CREDENTIALS = {"correo": "usuario@poe.com", "contraseña": "TU_CONTRASEÑA_USER"}


def get_token(credentials):
    response = client.post("/usuarios/token", json=credentials)
    assert response.status_code == 200, f"No se pudo obtener token: {response.text}"
    return response.json()["access_token"]

def test_eliminar_producto_no_referenciado():
    token = get_token(ADMIN_CREDENTIALS)
    # Crear producto de prueba (debería hacerse vía endpoint o fixture)
    response = client.post(
        "/productos",
        json={"nombre": "TestProd", "categoria": "Test", "unidad_tipo": "u", "unidad_cantidad": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    prod_id = response.json()["id_producto"]

    # Eliminar producto
    response = client.delete(f"/productos/{prod_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    # Verificar que ya no existe
    response = client.get(f"/productos/{prod_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_eliminar_producto_con_tarea_activa():
    token = get_token(ADMIN_CREDENTIALS)
    # Suponiendo que existe un producto con id 999 vinculado a tarea activa
    prod_id = 999
    response = client.delete(f"/productos/{prod_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409
    assert "vinculado a tareas activas" in response.json()["detail"]

def test_eliminar_producto_sin_permiso():
    token = get_token(USER_CREDENTIALS)
    # Simula un token de usuario no admin
    prod_id = 1
    response = client.delete(f"/productos/{prod_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403 or response.status_code == 401

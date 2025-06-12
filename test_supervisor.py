import requests
import json
import pytest
from typing import Dict

@pytest.fixture(scope="module")
def context():
    """Fixture para compartir el contexto entre las pruebas"""
    return {
        "base_url": "http://localhost:8000",
        "admin_token": None,
        "supervisor_token": None,
        "reponedor_id": None
    }

def test_login_admin(context):
    """Test: Login como administrador"""
    login_data = {
        "correo": "admin@poe.com",
        "contraseña": "admin123"
    }
    
    response = requests.post(
        f"{context['base_url']}/usuarios/token",
        json=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    context["admin_token"] = data["access_token"]

def test_crear_supervisor(context):
    """Test: Crear un supervisor de prueba"""
    assert context["admin_token"] is not None        supervisor_data = {
            "nombre": "Supervisor Test",
            "correo": "supervisor.test@poe.com",
            "contraseña": "supervisor123",
            "rol": "Supervisor",
            "estado": "activo"
        }
    
    headers = {
        "Authorization": f"Bearer {context['admin_token']}"
    }
    
    response = requests.post(
        f"{context['base_url']}/usuarios/",
        json=supervisor_data,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["usuario"]["correo"] == "supervisor.test@poe.com"

def test_login_supervisor(context):
    """Test: Login como supervisor"""
    login_data = {
        "correo": "supervisor.test@poe.com",
        "contraseña": "supervisor123"
    }
    
    response = requests.post(
        f"{context['base_url']}/usuarios/token",
        json=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    context["supervisor_token"] = data["access_token"]

def test_crear_reponedor(context):
    """Test: Crear un nuevo reponedor"""
    assert context["supervisor_token"] is not None
    
    reponedor_data = {
        "nombre": "Reponedor Test",
        "correo": "reponedor.test@poe.com",
        "contraseña": "reponedor123",
        "estado": "activo"
    }
    
    headers = {
        "Authorization": f"Bearer {context['supervisor_token']}"
    }
    
    response = requests.post(
        f"{context['base_url']}/supervisor/reponedores",
        json=reponedor_data,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["mensaje"] == "Reponedor registrado exitosamente"
    assert data["usuario"]["correo"] == "reponedor.test@poe.com"
    context["reponedor_id"] = data["usuario"]["id_usuario"]

def test_listar_reponedores_disponibles(context):
    """Test: Listar reponedores disponibles"""
    assert context["supervisor_token"] is not None
    
    headers = {
        "Authorization": f"Bearer {context['supervisor_token']}"
    }
    
    response = requests.get(
        f"{context['base_url']}/supervisor/reponedores/disponibles",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reponedores" in data
    assert isinstance(data["reponedores"], list)

def test_asignar_reponedor(context):
    """Test: Asignar reponedor"""
    assert context["supervisor_token"] is not None
    assert context["reponedor_id"] is not None
    
    headers = {
        "Authorization": f"Bearer {context['supervisor_token']}"
    }
    
    response = requests.post(
        f"{context['base_url']}/supervisor/reponedores/{context['reponedor_id']}/asignar",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Reponedor asignado exitosamente"

def test_listar_reponedores_asignados(context):
    """Test: Listar reponedores asignados"""
    assert context["supervisor_token"] is not None
    
    headers = {
        "Authorization": f"Bearer {context['supervisor_token']}"
    }
    
    response = requests.get(
        f"{context['base_url']}/supervisor/reponedores",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reponedores" in data
    assert any(r["id"] == context["reponedor_id"] for r in data["reponedores"])

def test_desasignar_reponedor(context):
    """Test: Desasignar reponedor"""
    assert context["supervisor_token"] is not None
    assert context["reponedor_id"] is not None
    
    headers = {
        "Authorization": f"Bearer {context['supervisor_token']}"
    }
    
    response = requests.delete(
        f"{context['base_url']}/supervisor/reponedores/{context['reponedor_id']}/desasignar",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mensaje"] == "Reponedor desasignado exitosamente"
    
    # Verificar que ya no aparezca en la lista
    response = requests.get(
        f"{context['base_url']}/supervisor/reponedores",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert not any(r["id"] == context["reponedor_id"] for r in data["reponedores"])


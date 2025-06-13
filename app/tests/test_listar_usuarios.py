import requests
import json
from typing import Optional, Dict

def test_listar_usuarios():
    """Prueba el endpoint de listar usuarios con diferentes filtros"""
    base_url = "http://localhost:8000"
    
    # 1. Login como administrador
    login_data = {
        "correo": "admin@poe.com",
        "contraseña": "admin123"
    }
    
    response = requests.post(
        f"{base_url}/usuarios/token",
        json=login_data
    )
    
    if response.status_code != 200:
        print(f"❌ Error en login: {response.json()}")
        return
        
    admin_token = response.json()["access_token"]
    print("✅ Login administrador exitoso")
    
    # Headers para las peticiones
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    
    # 2. Listar todos los usuarios (sin filtro)
    print("\n=== Listando todos los usuarios ===")
    response = requests.get(
        f"{base_url}/usuarios?page=1&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total usuarios: {data['total']}")
        print("Usuarios encontrados:", json.dumps(data, indent=2))
        assert "total" in data
        assert "usuarios" in data
    else:
        print(f"❌ Error al listar usuarios: {response.json()}")
        return
        
    # 3. Listar usuarios filtrados por rol Supervisor
    print("\n=== Listando supervisores ===")
    response = requests.get(
        f"{base_url}/usuarios?rol=Supervisor&page=1&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total supervisores: {data['total']}")
        print("Supervisores encontrados:", json.dumps(data, indent=2))
        assert "total" in data
        assert "usuarios" in data
    else:
        print(f"❌ Error al listar supervisores: {response.json()}")
        return
        
    # 4. Listar usuarios filtrados por rol Reponedor
    print("\n=== Listando reponedores ===")
    response = requests.get(
        f"{base_url}/usuarios?rol=Reponedor&page=1&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total reponedores: {data['total']}")
        print("Reponedores encontrados:", json.dumps(data, indent=2))
        assert "total" in data
        assert "usuarios" in data
    else:
        print(f"❌ Error al listar reponedores: {response.json()}")
        return
        
    print("\n=== Pruebas completadas exitosamente ===")

if __name__ == "__main__":
    test_listar_usuarios()

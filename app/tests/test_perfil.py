import requests
import json

def test_perfil_usuario():
    """Prueba el endpoint de perfil de usuario con diferentes roles"""
    base_url = "http://localhost:8000"
    
    # Lista de usuarios de prueba con diferentes roles
    usuarios_prueba = [
        {
            "correo": "admin@poe.com",
            "contraseña": "admin123",
            "descripcion": "Administrador"
        },
        {
            "correo": "supervisor.test@poe.com",
            "contraseña": "supervisor123",
            "descripcion": "Supervisor"
        },
        {
            "correo": "reponedor.test@poe.com",
            "contraseña": "reponedor123",
            "descripcion": "Reponedor"
        }
    ]
    
    for usuario in usuarios_prueba:
        print(f"\n=== Probando perfil de {usuario['descripcion']} ===")
        
        # 1. Login
        response = requests.post(
            f"{base_url}/usuarios/token",
            json={
                "correo": usuario["correo"],
                "contraseña": usuario["contraseña"]
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Error en login: {response.json()}")
            continue
            
        token = response.json()["access_token"]
        print(f"✅ Login {usuario['descripcion']} exitoso")
        
        # 2. Obtener perfil
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"{base_url}/usuarios/me",
            headers=headers
        )
        
        if response.status_code == 200:
            perfil = response.json()
            print(f"✅ Perfil obtenido exitosamente:")
            print(json.dumps(perfil, indent=2))
            assert "correo" in perfil
            assert "rol" in perfil
        else:
            print(f"❌ Error al obtener perfil: {response.json()}")
    
    print("\n=== Pruebas completadas ===")

if __name__ == "__main__":
    test_perfil_usuario()

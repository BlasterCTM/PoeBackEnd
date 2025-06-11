import requests
import json

def test_auth():
    # URL base
    base_url = "http://localhost:8000"
    
    # 1. Login como administrador
    login_data = {
        "correo": "admin@poe.com",
        "contraseña": "admin123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/usuarios/token",
            json=login_data
        )
        print("\nRespuesta del login:")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Probar el endpoint con el token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Ejemplo: desactivar usuario 2
            estado_data = {
                "estado": "inactivo"
            }
            
            response = requests.patch(
                f"{base_url}/usuarios/2/estado",
                json=estado_data,
                headers=headers
            )
            
            print("\nRespuesta de actualización de estado:")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_auth()

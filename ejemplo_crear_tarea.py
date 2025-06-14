# Ejemplo de cómo crear una tarea y agregar productos a ella

import requests
import json

# URL base del backend
BASE_URL = "http://localhost:8000"

# Credenciales de supervisor (ajustar según tus datos)
SUPERVISOR_CREDENTIALS = {
    "correo": "supervisor.test@poe.com",
    "contraseña": "supervisor123"
}

# Credenciales de administrador (ajustar según tus datos)
ADMIN_CREDENTIALS = {
    "correo": "admin@poe.com",
    "contraseña": "admin123"
}

def get_token(credentials):
    """Obtiene un token de autenticación"""
    response = requests.post(f"{BASE_URL}/login", json=credentials)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error al obtener token: {response.text}")
        return None

def crear_tarea_como_supervisor(token, id_punto, id_reponedor=None):
    """Crea una tarea como supervisor"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "id_punto": id_punto,
        "id_reponedor": id_reponedor
    }
    response = requests.post(f"{BASE_URL}/tareas", json=data, headers=headers)
    print(f"Respuesta al crear tarea como supervisor: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json() if response.status_code == 201 else None

def crear_tarea_como_admin(token, id_supervisor, id_punto, id_reponedor=None):
    """Crea una tarea como administrador"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "id_supervisor": id_supervisor,
        "id_punto": id_punto,
        "id_reponedor": id_reponedor
    }
    response = requests.post(f"{BASE_URL}/tareas", json=data, headers=headers)
    print(f"Respuesta al crear tarea como administrador: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json() if response.status_code == 201 else None

def agregar_producto_a_tarea(token, id_tarea, id_producto, cantidad):
    """Agrega un producto a una tarea"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "id_producto": id_producto,
        "cantidad": cantidad
    }
    response = requests.post(f"{BASE_URL}/tareas/{id_tarea}/detalle", json=data, headers=headers)
    print(f"Respuesta al agregar producto: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json() if response.status_code == 200 else None

def obtener_detalle_tarea(token, id_tarea):
    """Obtiene el detalle de una tarea"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/tareas/{id_tarea}/detalle", headers=headers)
    print(f"Respuesta al obtener detalle: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json() if response.status_code == 200 else None

# Ejemplo de uso
def main():
    # Obtener token de supervisor
    supervisor_token = get_token(SUPERVISOR_CREDENTIALS)
    if not supervisor_token:
        return
    
    # Crear una tarea como supervisor
    # Debes reemplazar estos IDs con valores reales de tu base de datos
    id_punto = 1  # ID de un punto de reposición existente
    id_reponedor = 3  # ID de un reponedor existente (opcional)
    
    tarea = crear_tarea_como_supervisor(supervisor_token, id_punto, id_reponedor)
    if not tarea:
        return
    
    # Agregar productos a la tarea
    # Debes reemplazar estos IDs con valores reales de tu base de datos
    id_tarea = tarea["id_tarea"]
    id_producto1 = 1  # ID de un producto existente
    id_producto2 = 2  # ID de otro producto existente
    
    agregar_producto_a_tarea(supervisor_token, id_tarea, id_producto1, 5)
    agregar_producto_a_tarea(supervisor_token, id_tarea, id_producto2, 3)
    
    # Obtener detalle de la tarea
    obtener_detalle_tarea(supervisor_token, id_tarea)
    
    # También puedes probar crear una tarea como administrador
    admin_token = get_token(ADMIN_CREDENTIALS)
    if admin_token:
        id_supervisor = 2  # ID de un supervisor existente
        crear_tarea_como_admin(admin_token, id_supervisor, id_punto, id_reponedor)

if __name__ == "__main__":
    main()
"""
Script de prueba para el endpoint del dashboard
Prueba la funcionalidad del dashboard resumido para administradores
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
ADMIN_LOGIN = {
    "correo": "admin@poe.com",
    "contraseña": "admin123"
}

def obtener_token_admin():
    """Obtiene un token de autenticación para el administrador."""
    response = requests.post(
        f"{BASE_URL}/usuarios/token",
        json=ADMIN_LOGIN
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error al obtener token: {response.status_code}")
        print(response.text)
        return None

def test_dashboard_resumen(token):
    """Prueba el endpoint del dashboard resumido."""
    print("\n=== PRUEBA: Dashboard Resumen ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/dashboard/resumen", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        
        # Mostrar tareas
        print("\n📊 TAREAS DEL DÍA:")
        tareas = data.get("tareas", {})
        print(f"  Total de tareas hoy: {tareas.get('total_hoy', 0)}")
        print(f"  Pendientes: {tareas.get('pendientes', 0)}")
        print(f"  En progreso: {tareas.get('en_progreso', 0)}")
        print(f"  Completadas: {tareas.get('completadas', 0)}")
        
        # Mostrar top productos
        print("\n📦 TOP PRODUCTOS MÁS REPUESTOS:")
        top_productos = data.get("top_productos", [])
        if top_productos:
            for i, producto in enumerate(top_productos, 1):
                print(f"  {i}. {producto['nombre']}: {producto['cantidad_repuesta']} unidades")
        else:
            print("  No hay productos repuestos hoy")
        
        # Mostrar actividad de usuarios
        print("\n👥 ACTIVIDAD DE REPONEDORES:")
        actividad = data.get("actividad_usuarios", [])
        if actividad:
            for usuario in actividad:
                print(f"  - {usuario['nombre']}: {usuario['tareas_completadas']} tareas ({usuario['tiempo_total_minutos']} min)")
        else:
            print("  No hay actividad de reponedores hoy")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_acceso_no_autorizado():
    """Prueba que el endpoint requiere autenticación de administrador."""
    print("\n=== PRUEBA: Acceso No Autorizado ===")
    
    # Sin token
    response = requests.get(f"{BASE_URL}/dashboard/resumen")
    print(f"Sin token - Status Code: {response.status_code} (esperado: 401)")
    
    # Con token incorrecto
    headers = {"Authorization": "Bearer token_incorrecto"}
    response = requests.get(f"{BASE_URL}/dashboard/resumen", headers=headers)
    print(f"Token incorrecto - Status Code: {response.status_code} (esperado: 401)")

def main():
    """Ejecuta todas las pruebas del dashboard."""
    print("==========================================")
    print("INICIO DE PRUEBAS - Dashboard POE")
    print("==========================================")
    
    # Obtener token de administrador
    print("\n1. Obteniendo token de administrador...")
    token = obtener_token_admin()
    if not token:
        print("❌ No se pudo obtener el token. Verifica las credenciales.")
        return
    
    print("✅ Token obtenido exitosamente")
    
    # Prueba de acceso no autorizado
    test_acceso_no_autorizado()
    
    # Prueba del dashboard
    if test_dashboard_resumen(token):
        print("\n✅ Dashboard funcionando correctamente")
    else:
        print("\n❌ Error en el dashboard")
    
    print("\n==========================================")
    print("PRUEBAS COMPLETADAS")
    print("==========================================")

if __name__ == "__main__":
    main()

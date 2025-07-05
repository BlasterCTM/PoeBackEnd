#!/usr/bin/env python3

import requests
import json
import sys

# Configuración
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Obtener token de autenticación"""
    login_url = f"{BASE_URL}/usuarios/token"
    
    # Usar form data en lugar de JSON
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(login_url, data=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            print("❌ Error: No se obtuvo token de acceso")
            return None
            
        print(f"✅ Login exitoso - Token obtenido")
        return token
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en login: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"📄 Respuesta de error: {e.response.text}")
        return None

def test_ruta_optimizada_debug(id_tarea=1):
    """Probar el endpoint de debug sin autenticación"""
    
    # Endpoint de debug
    url = f"{BASE_URL}/tareas/{id_tarea}/ruta-optimizada-debug"
    
    try:
        print(f"🔄 Probando endpoint DEBUG: {url}")
        response = requests.get(url)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa")
            print(f"📝 Estructura de respuesta:")
            print(f"   - ID Tarea: {data.get('id_tarea')}")
            print(f"   - Reponedor: {data.get('reponedor')}")
            print(f"   - Muebles: {len(data.get('muebles_rutas', []))}")
            
            # Analizar cada mueble
            for i, mueble in enumerate(data.get('muebles_rutas', [])):
                print(f"   - Mueble {i+1}: ID={mueble.get('id_mueble')}, Productos={len(mueble.get('detalle_tareas', []))}, Pasos en ruta={len(mueble.get('ruta_optimizada_mueble', []))}")
                
                # Mostrar si hay rutas vacías
                if len(mueble.get('ruta_optimizada_mueble', [])) == 0:
                    print(f"   ⚠️  RUTA VACÍA para mueble {mueble.get('id_mueble')}")
                else:
                    print(f"   ✅ Ruta generada para mueble {mueble.get('id_mueble')}")
            
            # Mostrar respuesta completa para debugging
            print("\n📋 Respuesta completa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición: {e}")

def main():
    print("🚀 Iniciando prueba de ruta optimizada DEBUG...")
    
    # Obtener ID de tarea desde argumentos o usar default
    id_tarea = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"🎯 Probando con tarea ID: {id_tarea}")
    
    # Probar endpoint de debug
    test_ruta_optimizada_debug(id_tarea)
    
    print("✅ Prueba completada")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para probar la conexión a PostgreSQL Azure
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("🔍 Probando conexión a PostgreSQL Azure...\n")

# Obtener credenciales
host = os.getenv("AZURE_POSTGRES_HOST")
port = os.getenv("AZURE_POSTGRES_PORT", "5432")
user = os.getenv("AZURE_POSTGRES_USER")
password = os.getenv("AZURE_POSTGRES_PASSWORD")
database = os.getenv("AZURE_POSTGRES_DB")

print(f"📍 Host: {host}")
print(f"📍 Port: {port}")
print(f"📍 User: {user}")
print(f"📍 Database: {database}")
print(f"📍 Password: {'*' * len(password) if password else 'NO CONFIGURADO'}\n")

# Intentar conexión
try:
    import psycopg2
    
    print("⏳ Intentando conectar...")
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        sslmode='require',
        connect_timeout=10
    )
    
    print("✅ CONEXIÓN EXITOSA!\n")
    
    # Probar query simple
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"📊 PostgreSQL version: {version[0]}\n")
    
    cursor.execute("SELECT current_database();")
    db = cursor.fetchone()
    print(f"📊 Database actual: {db[0]}\n")
    
    cursor.close()
    conn.close()
    
    print("✅ Todo funciona correctamente!")
    print("🐳 El problema está en la red de Docker, no en las credenciales.\n")
    
    sys.exit(0)
    
except ImportError:
    print("❌ Error: psycopg2 no está instalado")
    print("Instalar con: pip install psycopg2-binary\n")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}\n")
    
    error_str = str(e).lower()
    
    if "timeout" in error_str or "timed out" in error_str:
        print("💡 PROBLEMA: Timeout de conexión")
        print("   - Tu IP no está permitida en el firewall de Azure")
        print("   - Ve a Azure Portal → PostgreSQL → Networking → Agregar tu IP")
        
    elif "password authentication failed" in error_str:
        print("💡 PROBLEMA: Contraseña incorrecta")
        print("   - Verifica AZURE_POSTGRES_PASSWORD en .env")
        
    elif "database" in error_str and "does not exist" in error_str:
        print("💡 PROBLEMA: Base de datos no existe")
        print(f"   - Verifica que la DB '{database}' existe en Azure")
        
    elif "role" in error_str or "user" in error_str:
        print("💡 PROBLEMA: Usuario incorrecto")
        print("   - Verifica AZURE_POSTGRES_USER en .env")
        
    else:
        print("💡 PROBLEMA: Error desconocido")
        print("   - Verifica todas las credenciales en .env")
    
    print()
    sys.exit(1)

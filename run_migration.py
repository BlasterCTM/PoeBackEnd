"""
Script para ejecutar migración SQL directamente desde Python
Útil cuando psql no está en el PATH
"""

import psycopg2
from psycopg2 import sql
import os
from pathlib import Path

# Configuración de conexión (ajustar según tu configuración)
DB_CONFIG = {
    'dbname': 'poe_db',
    'user': 'postgres',
    'password': 'tu_password_aqui',  # CAMBIAR ESTO
    'host': 'localhost',
    'port': 5432
}

def run_migration(migration_file: str):
    """Ejecuta un archivo SQL de migración"""
    
    # Leer archivo SQL
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"❌ Error: Archivo no encontrado: {migration_file}")
        return False
    
    print(f"📄 Leyendo migración: {migration_path.name}")
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Conectar a la base de datos
    try:
        print(f"🔌 Conectando a PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Usaremos transacciones manuales
        cursor = conn.cursor()
        
        print(f"⚙️  Ejecutando migración...")
        
        # Ejecutar el SQL completo
        cursor.execute(migration_sql)
        
        # Commit de la transacción
        conn.commit()
        
        print("✅ Migración ejecutada exitosamente!")
        print("\nResultados:")
        print("  ✓ Tabla log_auditoria creada")
        print("  ✓ 8 índices creados en log_auditoria")
        print("  ✓ Campo modulos_habilitados agregado a plan_empresa")
        print("  ✓ Permisos configurados")
        print("  ✓ Log inicial insertado")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error al ejecutar migración:")
        print(f"   {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    # Ruta al archivo de migración
    migration_file = os.path.join(
        os.path.dirname(__file__),
        'migrations',
        '002_backoffice_y_auditoria.sql'
    )
    
    print("=" * 60)
    print("🚀 EJECUTAR MIGRACIÓN 002: BACKOFFICE Y AUDITORÍA")
    print("=" * 60)
    print()
    
    # Verificar configuración
    print("⚠️  IMPORTANTE: Verifica la configuración de DB_CONFIG en este script")
    print(f"   Database: {DB_CONFIG['dbname']}")
    print(f"   User: {DB_CONFIG['user']}")
    print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    continuar = input("¿Continuar con la migración? (s/n): ")
    if continuar.lower() == 's':
        success = run_migration(migration_file)
        if success:
            print("\n✅ Migración completada. El módulo Backoffice está listo para usar.")
        else:
            print("\n❌ La migración falló. Revisa los errores anteriores.")
    else:
        print("❌ Migración cancelada.")

"""
Script para corregir la restricción CHECK de la tabla empresa
Agrega el valor 'suspendido' a los estados permitidos
"""
from sqlalchemy import create_engine, text
import os

# Obtener la URL de la base de datos desde variables de entorno o usar valores por defecto
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poe_db")

try:
    # Crear engine de SQLAlchemy
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Eliminar restricción antigua
        print("Eliminando restricción CHECK antigua...")
        conn.execute(text("ALTER TABLE empresa DROP CONSTRAINT IF EXISTS empresa_estado_check;"))
        
        # Agregar nueva restricción con 'suspendido'
        print("Agregando nueva restricción CHECK...")
        conn.execute(text("""
            ALTER TABLE empresa 
            ADD CONSTRAINT empresa_estado_check 
            CHECK (estado IN ('activo', 'inactivo', 'suspendido', 'prueba'));
        """))
        
        # Confirmar cambios
        conn.commit()
        print("✓ Restricción CHECK actualizada exitosamente")
        print("✓ Estados permitidos: activo, inactivo, suspendido, prueba")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nIntenta ejecutar directamente en PostgreSQL:")
    print("ALTER TABLE empresa DROP CONSTRAINT IF EXISTS empresa_estado_check;")
    print("ALTER TABLE empresa ADD CONSTRAINT empresa_estado_check CHECK (estado IN ('activo', 'inactivo', 'suspendido', 'prueba'));")

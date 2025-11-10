"""
Script para insertar usuarios de prueba para testing
Ejecutar: python seed_usuarios_test.py
"""
from app.core.database.database import Database
from app.models.usuario import Usuario
from app.core.security.password import get_password_hash

def seed_usuarios():
    db_instance = Database()
    db = db_instance.SessionLocal()
    
    try:
        # Verificar si ya existen
        existing = db.query(Usuario).filter(Usuario.correo.in_([
            'admin@poe.com',
            'admin.empresa1@test.com',
            'supervisor.empresa1@test.com',
            'reponedor.empresa1@test.com'
        ])).all()
        
        if existing:
            print(f"⚠️  Eliminando {len(existing)} usuarios existentes...")
            for user in existing:
                db.delete(user)
            db.commit()
        
        # Contraseña de prueba: Admin123!@
        password_hash = get_password_hash("Admin123!@")
        
        usuarios_test = [
            # SuperAdmin (acceso global)
            Usuario(
                nombre="Super Admin POE",
                correo="admin@poe.com",
                contraseña=password_hash,
                rol_id=4,  # SuperAdmin
                estado="activo",
                id_empresa=1  # Asignado a empresa 1 pero tiene acceso global por rol
            ),
            
            # Administrador Empresa 1
            Usuario(
                nombre="Admin Empresa 1",
                correo="admin.empresa1@test.com",
                contraseña=password_hash,
                rol_id=1,  # Administrador
                estado="activo",
                id_empresa=1
            ),
            
            # Supervisor Empresa 1
            Usuario(
                nombre="Supervisor Test",
                correo="supervisor.empresa1@test.com",
                contraseña=password_hash,
                rol_id=2,  # Supervisor
                estado="activo",
                id_empresa=1
            ),
            
            # Reponedor Empresa 1
            Usuario(
                nombre="Reponedor Test",
                correo="reponedor.empresa1@test.com",
                contraseña=password_hash,
                rol_id=3,  # Reponedor
                estado="activo",
                id_empresa=1
            ),
        ]
        
        print("\n📝 Insertando usuarios de prueba...")
        for usuario in usuarios_test:
            db.add(usuario)
        
        db.commit()
        
        print("\n✅ Usuarios de prueba creados exitosamente!")
        print("\n=== USUARIOS CREADOS ===")
        print("SuperAdmin:")
        print("  - Email: admin@poe.com")
        print("  - Password: Admin123!@")
        print("  - Rol: SuperAdmin (acceso global)")
        print("\nAdministrador:")
        print("  - admin.empresa1@test.com (Empresa 1)")
        print("  - Password: Admin123!@")
        print("\nSupervisor:")
        print("  - supervisor.empresa1@test.com (Empresa 1)")
        print("  - Password: Admin123!@")
        print("\nReponedor:")
        print("  - reponedor.empresa1@test.com (Empresa 1)")
        print("  - Password: Admin123!@")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_usuarios()
